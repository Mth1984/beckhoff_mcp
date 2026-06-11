# beckhoff_mcp — Speedup-Vendored-Clone

**Was das ist:** Lokaler Clone von `malcolm-mill/beckhoff_mcp` (MIT) — ADS-MCP-Server (Python/pyads), liest Live-Symbole/State gegen eine laufende TwinCAT-SPS. Teil des Speedup-DIY-CoAgent-Backbones (Slice 1).

**Vault-Single-Source:** `04 Ressourcen/Beckhoff TwinCAT/TwinCAT DIY-CoAgent (MCP-Toolchain).md` — dort liegen Install-Log, Lessons und das Connect-Pattern. Diese Datei hier nur das Repo-lokale Manifest.

## ⚠️ Vendored — nicht blind pullen/pushen

- `origin` zeigt auf das **Upstream-Repo** (`malcolm-mill/beckhoff_mcp`). **Niemals dorthin pushen.**
- Wir tragen einen **lokalen Patch** (siehe unten). Ein blindes `git pull`/Re-Clone überschreibt ihn → vor jedem Upstream-Sync den Patch prüfen/neu anwenden.

## Lokaler Patch (2026-06-11)

**`src/beckhoff_mcp/server.py` → `beckhoff_discover_and_connect`** hat einen zusätzlichen optionalen Parameter `ams_net_id: str | None = None`.

- **Warum:** Im SpeedOS-Netz ist **UDP-Discovery (Port 48899) geblockt** → der Original-Pfad (`adsGetNetIdForPLC` per UDP) scheitert mit Timeout, obwohl ADS/TCP läuft und eine ADS-Route existiert.
- **Wirkung:** Wird `ams_net_id` übergeben, wird die UDP-Discovery übersprungen und die bekannte NetId direkt für `pyads.Connection(...)` genutzt. Rückwärtskompatibel (ohne Param = altes UDP-Verhalten).

## Registrierung (user-scope MCP)

```
claude mcp add beckhoff-ads -s user -- D:\VS_Repos\beckhoff_mcp\.venv\Scripts\python.exe -m beckhoff_mcp.server
```

venv via `uv venv` + `uv pip install -e .` (pyads 3.5.2, mcp 1.27.2, pydantic 2.13.4).

## Connect-Pattern SpeedOS-PLC

```
beckhoff_discover_and_connect(ip_address="192.168.12.1", ams_net_id="192.168.12.2.1.1")
  → beckhoff_list_symbols(filter="GVL_*") / beckhoff_read_variable("MAIN.bStart")
```

- NetId/Route **live** aus `Get-AdsRoute` holen, nie aus IP konstruieren — die Route kann driften.
- ⚠️ **Mid-Session-MCP-Quirk:** Mid-Session registrierte/gepatchte MCP-Server surfacen ihre Tools erst in der **nächsten** Claudian-Session. Direkt-Smoke über pyads umgeht das.
