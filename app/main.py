#!/usr/bin/env python3
"""spacedesk for Linux: espelhamento local do desktop Linux para o navegador de um tablet."""
import argparse
import io
import re
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = ImageGrab = None

PORT = 18900
FPS_DELAY = 0.05
JPEG_QUALITY = 65
MAX_WIDTH = 1920
BG = "#0a0d17"
CARD = "#121724"
BORDER = "#242d3e"
WHITE = "#f4f7fb"
MUTED = "#9ba9bf"
MINT = "#6fe7ce"
PURPLE = "#bca8ff"


class StreamState:
    def __init__(self):
        self.lock = threading.Lock()
        self.latest = b""
        self.sequence = 0
        self.error = ""
        self.original_fb = None
        self.capture_bbox = None
        self.active = threading.Event()
        self.server = None
        self.url = ""


STATE = StreamState()


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def capture_loop():
    while STATE.active.is_set():
        try:
            if ImageGrab is None:
                raise RuntimeError("Não foi possível capturar a tela. Confira a sessão gráfica e a instalação do Pillow.")
            with STATE.lock:
                bbox = STATE.capture_bbox
            try:
                frame = ImageGrab.grab(bbox=bbox, all_screens=True)
            except TypeError:
                frame = ImageGrab.grab(bbox=bbox)
            if frame.width > MAX_WIDTH:
                height = max(1, int(frame.height * MAX_WIDTH / frame.width))
                frame = frame.resize((MAX_WIDTH, height), Image.Resampling.BILINEAR)
            frame = frame.convert("RGB")
            buffer = io.BytesIO()
            frame.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            with STATE.lock:
                STATE.latest = buffer.getvalue()
                STATE.sequence += 1
                STATE.error = ""
        except Exception:
            # O estado de conexÃ£o segue visÃ­vel no painel; a captura tenta novamente.
            pass
        time.sleep(FPS_DELAY)


class Receiver(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Connection", "close")
            self.end_headers()
            last_sequence = -1
            while STATE.active.is_set():
                with STATE.lock:
                    frame = STATE.latest
                    sequence = STATE.sequence
                if frame and sequence != last_sequence:
                    try:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " +
                                         str(len(frame)).encode() + b"\r\n\r\n" + frame + b"\r\n")
                        self.wfile.flush()
                        last_sequence = sequence
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        break
                time.sleep(0.01)
            return

        page = """<!doctype html><html lang="pt-br"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><meta name="theme-color" content="#080b13">
<title>spacedesk for Linux</title><style>*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#080b13;color:#edf3fb;font:16px system-ui}body{min-height:100vh;display:grid;place-items:center}.wrap{width:100%;max-width:1100px;padding:18px}header{display:flex;justify-content:space-between;gap:10px;align-items:center;margin:4px 0 14px;color:#6fe7ce;font-weight:700;letter-spacing:.08em}button{border:0;border-radius:9px;padding:10px 14px;background:#6fe7ce;color:#081819;font:600 14px system-ui}main{background:#111725;border:1px solid #273146;border-radius:14px;padding:10px}img{width:100%;height:auto;display:block;border-radius:8px}small{display:block;color:#a7b4ca;margin:12px 3px}.fullscreen{position:fixed;inset:0;width:100vw;height:100dvh;background:#080b13;display:flex;align-items:center;justify-content:center}.fullscreen .wrap{max-width:none;width:100%;height:100%;padding:0;display:flex;flex-direction:column}.fullscreen header{padding:8px 12px;margin:0;flex:none}.fullscreen main{flex:1;min-height:0;border:0;border-radius:0;padding:0;display:flex;align-items:center;justify-content:center}.fullscreen img{width:100%;height:100%;object-fit:contain;border-radius:0}.fullscreen small{display:none}@media(orientation:landscape){.fullscreen header{position:absolute;top:0;right:0;z-index:2;opacity:.25}.fullscreen header:hover{opacity:1}}</style><div class="wrap"><header><span>◉ &nbsp; SPACEDESK FOR LINUX</span><button id="full" type="button">Tela cheia</button></header><main><img src="/stream.mjpg" alt="Tela compartilhada"></main><small>Transmissão local · Para encerrar, pare pelo computador.</small></div><script>const btn=document.getElementById('full');function sync(){document.body.classList.toggle('fullscreen',!!document.fullscreenElement);btn.textContent=document.fullscreenElement?'Sair da tela cheia':'Tela cheia'}btn.addEventListener('click',async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}catch(e){document.body.classList.toggle('fullscreen');btn.textContent=document.body.classList.contains('fullscreen')?'Sair da tela cheia':'Tela cheia'}});document.addEventListener('fullscreenchange',sync);</script></html>"""
        body = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def create_extended_display():
    if __import__("sys").platform != "linux":
        raise RuntimeError("A tela estendida automática está disponível no Linux com X11.")
    try:
        info = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Não encontrei o xrandr/X11. No Wayland, crie a tela virtual nas configurações do sistema.") from exc
    match = re.search(r"current (\d+) x (\d+)", info)
    if not match:
        raise RuntimeError("Não consegui ler o tamanho da área de trabalho X11.")
    base_w, base_h = map(int, match.groups())
    width, height = 1280, 800
    subprocess.run(["xrandr", "--fb", f"{base_w + width}x{max(base_h, height)}"], check=True, capture_output=True, text=True)
    try:
        subprocess.run(["xrandr", "--setmonitor", "TelaLivre", f"{width}/300x{height}/190+{base_w}+0", "none"], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        subprocess.run(["xrandr", "--fb", f"{base_w}x{base_h}"], capture_output=True, text=True)
        detail = getattr(exc, "stderr", "") or str(exc)
        raise RuntimeError(f"O X11 não aceitou a tela virtual: {detail}") from exc
    STATE.original_fb = (base_w, base_h)
    STATE.capture_bbox = (base_w, 0, base_w + width, height)


def remove_extended_display():
    if STATE.original_fb is None:
        return
    subprocess.run(["xrandr", "--delmonitor", "TelaLivre"], capture_output=True, text=True)
    width, height = STATE.original_fb
    subprocess.run(["xrandr", "--fb", f"{width}x{height}"], check=True, capture_output=True, text=True)
    STATE.original_fb = None
    STATE.capture_bbox = None


def start_stream():
    if ImageGrab is None:
        raise RuntimeError("Falta Pillow. Instale com: python3 -m pip install Pillow")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Receiver)
    server.daemon_threads = True
    STATE.server = server
    STATE.active.set()
    STATE.url = f"http://{local_ip()}:{PORT}"
    threading.Thread(target=capture_loop, daemon=True).start()
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.25}, daemon=True).start()


def stop_stream():
    STATE.active.clear()
    server, STATE.server = STATE.server, None
    if server:
        server.shutdown()
        server.server_close()


class TelaLivre:
    def __init__(self, root, screenshot=None):
        self.root = root
        self.screenshot = screenshot
        self.frames = 0
        self.screenshot_done = False
        self.started = time.monotonic()
        root.title("spacedesk for Linux")
        root.geometry("920x720")
        root.minsize(780, 680)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._fonts()
        self._layout()
        if screenshot:
            self.root.after_idle(self._prepare_capture_window)
        self._tick()

    def _prepare_capture_window(self):
        if __import__("sys").platform != "win32":
            return
        import ctypes
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
        user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0043)  # HWND_BOTTOM; no move, size or activation; show

    def _fonts(self):
        self.f_small = ("Segoe UI", 10)
        self.f_label = ("Segoe UI", 10, "bold")
        self.f_body = ("Segoe UI", 11)
        self.f_heading = ("Segoe UI", 27, "bold")
        self.f_title = ("Segoe UI", 14, "bold")

    def label(self, parent, text, color=WHITE, font=None, **kw):
        bg = kw.pop("bg", parent.cget("bg"))
        return tk.Label(parent, text=text, bg=bg, fg=color, font=font or self.f_body, **kw)

    def _card(self, parent, **pack):
        box = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1, bd=0)
        box.pack(**pack)
        return box

    def _layout(self):
        root = self.root
        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=32, pady=(22, 0))
        self.label(top, "◉", MINT, ("Segoe UI Symbol", 24, "bold")).pack(side="left")
        self.label(top, "SPACEDESK FOR LINUX", WHITE, self.f_title).pack(side="left", padx=(7, 13))
        self.label(top, "TRANSMISSÃO LOCAL", MINT, ("Segoe UI", 8, "bold"),
                   bg="#162b30", padx=10, pady=5).pack(side="left")
        self.label(top, "LINUX  ·  WI-FI", "#8492a8", ("Segoe UI", 9, "bold")).pack(side="right")

        title = tk.Frame(root, bg=BG)
        title.pack(fill="x", padx=32, pady=(21, 0))
        self.label(title, "Sua tela,", WHITE, self.f_heading).pack(anchor="w")
        self.label(title, "em outra tela.", MINT, self.f_heading).pack(anchor="w")
        self.label(root, "Conecte o tablet e envie a tela estendida pela rede local.",
                   MUTED, ("Segoe UI", 11)).pack(anchor="w", padx=32, pady=(6, 18))

        row = tk.Frame(root, bg=BG)
        row.pack(fill="x", padx=32)
        left = self._card(row, side="left", fill="both", expand=True, padx=(0, 9))
        right = self._card(row, side="left", fill="both", expand=True, padx=(9, 0))
        for box in (left, right):
            box.configure(padx=16, pady=14)
        self.label(left, "01    CONECTE SEU TABLET", MINT, self.f_label).pack(anchor="w")
        self.address = self.label(left, f"http://{local_ip()}:{PORT}", WHITE, ("Segoe UI", 16, "bold"))
        self.address.pack(anchor="w", pady=(14, 3))
        self.label(left, "Abra este endereço no navegador do tablet.", MUTED, self.f_small).pack(anchor="w")
        self.button = tk.Button(left, text="▶   Iniciar transmissão", command=self.toggle,
                                bg=MINT, fg="#081819", activebackground="#8af1dc", activeforeground="#081819",
                                relief="flat", bd=0, font=("Segoe UI", 11, "bold"), cursor="hand2",
                                pady=13, highlightthickness=0)
        self.button.pack(fill="x", pady=(17, 12))
        self.status = self.label(left, "●  Desligado · sua tela ainda é privada", "#b7c2d3", self.f_small)
        self.status.pack(anchor="w")
        self.error = self.label(left, "", "#ff898f", self.f_small, wraplength=360, justify="left")
        self.error.pack(anchor="w", pady=(6, 0))
        self.extend_button = tk.Button(left, text="Criar tela estendida para o tablet", command=self.toggle_extended,
                                       bg="#202a3a", fg=WHITE, activebackground="#2d3a4f", activeforeground=WHITE,
                                       relief="flat", bd=0, font=("Segoe UI", 10, "bold"), cursor="hand2",
                                       pady=9, highlightthickness=0)
        self.extend_button.pack(fill="x", pady=(10, 0))

        self.label(right, "02    PRÉVIA DA TELA", PURPLE, self.f_label).pack(anchor="w")
        preview = tk.Frame(right, bg="#111725", highlightbackground="#273146", highlightthickness=1, height=154)
        preview.pack(fill="x", pady=(13, 11))
        preview.pack_propagate(False)
        self.label(preview, "⊕", "#53677a", ("Segoe UI Symbol", 31)).pack(pady=(23, 0))
        self.label(preview, "A captura aparece quando iniciar", "#8593a9", ("Segoe UI", 9)).pack()
        metrics = tk.Frame(right, bg=CARD)
        metrics.pack(anchor="w")
        self.label(metrics, "QUALIDADE\nAdaptÃ¡vel", "#d7e0ed", self.f_small, justify="left").pack(side="left")
        self.label(metrics, "ACESSO\nRede local", "#d7e0ed", self.f_small, justify="left").pack(side="left", padx=(28, 0))

        guide = self._card(root, fill="x", padx=32, pady=(14, 0))
        guide.configure(padx=16, pady=12)
        self.label(guide, "COMO CONECTAR                                      MESMA REDE WI-FI",
                   "#b3bdce", self.f_label).pack(anchor="w")
        self.label(guide, "1. Inicie a transmissão   2. Abra o endereço no tablet   3. Use a mesma rede",
                   "#bdc8db", self.f_small).pack(anchor="w", pady=(9, 0))
        folder = tk.Frame(root, bg=BG)
        folder.pack(fill="x", padx=32, pady=(12, 0))
        self.label(folder, "PASTA DA APLICAÇÃO", MINT, ("Segoe UI", 8, "bold")).pack(anchor="w")
        self.label(folder, str(Path(__file__).resolve().parent), "#bdc8db", ("Segoe UI", 9),
                   anchor="w").pack(anchor="w", pady=(3, 0))
        footer = tk.Frame(root, bg=BG)
        footer.pack(fill="x", padx=32, pady=(9, 0))
        self.label(footer, "Acesso restrito à rede local. Pare a transmissão ao terminar.",
                   "#748197", ("Segoe UI", 9)).pack(side="left")
        self.label(footer, "SPACEDESK FOR LINUX", "#48566b", ("Segoe UI", 8, "bold")).pack(side="right")

    def toggle_extended(self):
        try:
            if STATE.original_fb is None:
                create_extended_display()
                self.extend_button.configure(text="Remover tela estendida")
            else:
                remove_extended_display()
                self.extend_button.configure(text="Criar tela estendida para o tablet")
            self.error.configure(text="Conecte-se ao tablet e arraste uma janela para a área à direita da tela.")
        except Exception as exc:
            self.error.configure(text=str(exc))

    def toggle(self):
        if STATE.active.is_set():
            stop_stream()
            self.button.configure(text="▶   Iniciar transmissão", bg=MINT)
            self.status.configure(text="●  Desligado · sua tela ainda é privada", fg="#b7c2d3")
            self.error.configure(text="")
            return
        try:
            start_stream()
            self.address.configure(text=STATE.url)
            self.button.configure(text="■  Parar transmissão", bg="#af4652", fg=WHITE)
            self.status.configure(text="●  Transmitindo · tablet pronto para conectar", fg=MINT)
            self.error.configure(text="")
        except Exception as exc:
            self.error.configure(text=str(exc))

    def _tick(self):
        self.frames += 1
        if STATE.error and not self.error.cget("text"):
            self.error.configure(text=STATE.error)
        if self.screenshot and not self.screenshot_done and self.frames >= 120:
            self.screenshot_done = True
            self.root.after(80, self._save_screenshot)
        self.root.after(16, self._tick)

    def _save_screenshot(self):
        try:
            self.root.update_idletasks()
            if ImageGrab is None:
                raise RuntimeError("Pillow é necessário para salvar capturas PNG.")
            if __import__("sys").platform == "win32":
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                ctypes.windll.user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
                ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0013)  # bottom; no activate; retain size
                image = ImageGrab.grab(window=hwnd)
            else:
                image = ImageGrab.grab()
            output = Path(self.screenshot)
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, format="PNG")
            print(f"Captura salva: {output}")
        except Exception as exc:
            print(f"Falha ao salvar a captura: {exc}", file=__import__("sys").stderr)
        finally:
            self.root.after(120, self.close)

    def close(self):
        stop_stream()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Transmita a tela para o navegador do tablet na mesma rede.")
    parser.add_argument("--screenshot", metavar="ARQUIVO.png", help="abra a janela, salve sua imagem e encerre")
    args = parser.parse_args()
    root = tk.Tk()
    TelaLivre(root, args.screenshot)
    root.mainloop()


if __name__ == "__main__":
    main()
