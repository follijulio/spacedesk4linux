# What we found in C:\Program Files\datronicsoft\spacedesk\spacedeskService.exe

spacedeskService.exe is a program for Windows, built for x86_64 (64-bit). Its internal names were removed (stripped), so most functions will have generated names.

Evidence ev_fcbcdb44d8e60dbc78f8c5502a68e580769b61705c82fab3c18347b6ef3c39bf.

```json
{
  "architecture": "x86_64",
  "bits": 64,
  "dotnet_arch": null,
  "entry_point": "0x1402b91a0",
  "format": "pe",
  "format_name": "PE (Windows)",
  "kind": "executable",
  "libraries": [
    "ADVAPI32.dll",
    "AVRT.dll",
    "CRYPT32.dll",
    "GDI32.dll",
    "IPHLPAPI.DLL",
    "KERNEL32.dll",
    "POWRPROF.dll",
    "SETUPAPI.dll",
    "SHELL32.dll",
    "SHLWAPI.dll",
    "USER32.dll",
    "WINMM.dll",
    "WTSAPI32.dll",
    "XmlLite.dll",
    "bcrypt.dll",
    "d3d11.dll",
    "dxgi.dll",
    "ole32.dll",
    "qwave.dll",
    "CFGMGR32.dll",
    "MFPlat.DLL",
    "WS2_32.dll"
  ],
  "next_steps": [
    {
      "tool": "core_overview_show",
      "why": "a one-page summary: sections, imports, counts"
    },
    {
      "tool": "native_functions_list",
      "why": "every function we found"
    },
    {
      "tool": "native_strings_find",
      "why": "find text the program shows or uses"
    },
    {
      "tool": "native_function_study",
      "why": "a full dossier on one function (start with main or the entry point)"
    },
    {
      "tool": "core_feature_find",
      "why": "follow a word you see in the app to the code behind it"
    },
    {
      "tool": "native_pe_resources_list",
      "why": "icons, version information and the manifest"
    }
  ],
  "operating_system": "Windows",
  "plain_english": "spacedeskService.exe is a program for Windows, built for x86_64 (64-bit). Its internal names were removed (stripped), so most functions will have generated names.",
  "recommended_toolsets": [
    "core",
    "native",
    "formats"
  ],
  "stripped": true,
  "symbol_table_stripped": true,
  "toolchain_hints": [
    {
      "category": "compiler",
      "evidence": "Rich header",
      "id": "msvc",
      "label": "Microsoft Visual C++ toolchain",
      "strength": "strong"
    }
  ]
}
```

## Ghidra

Deep mode: Ghidra has analysed C:\Program Files\datronicsoft\spacedesk\spacedeskService.exe (2 min), so decompiling it is quick.
