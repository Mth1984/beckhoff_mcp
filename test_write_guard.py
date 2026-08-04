"""Guard-Test fuer den Schreibschutz. Laeuft ohne SPS-Verbindung.

Prueft die drei Schutzschichten isoliert:
  1. Default = alles gesperrt
  2. Whitelist noetig, auch wenn Schalter an
  3. Blacklist schlaegt die Whitelist IMMER
"""

import importlib
import os
import sys

FAILS = []


def load(allow=None, whitelist=None):
    """Modul mit gesetzter Env frisch laden (Konstanten werden beim Import gelesen)."""
    os.environ.pop("BECKHOFF_MCP_ALLOW_WRITE", None)
    os.environ.pop("BECKHOFF_MCP_WRITE_WHITELIST", None)
    if allow is not None:
        os.environ["BECKHOFF_MCP_ALLOW_WRITE"] = allow
    if whitelist is not None:
        os.environ["BECKHOFF_MCP_WRITE_WHITELIST"] = whitelist
    for m in [m for m in sys.modules if m.startswith("beckhoff_mcp")]:
        del sys.modules[m]
    return importlib.import_module("beckhoff_mcp.server")


def check(label, got_denial, want_denied):
    denied = got_denial is not None
    ok = denied == want_denied
    print(f"  {'OK  ' if ok else 'FAIL'} {label:<58} "
          f"{'gesperrt' if denied else 'erlaubt'}")
    if not ok:
        FAILS.append(label)


print("\n=== Schicht 1: Default (nichts gesetzt) ===")
s = load()
check("write ohne Env -> muss gesperrt sein", s.check_write_allowed("GVL_Anim.fX"), True)

print("\n=== Schicht 2: Schalter an, aber keine Whitelist ===")
s = load(allow="1")
check("ALLOW_WRITE=1 ohne Whitelist -> gesperrt", s.check_write_allowed("GVL_Anim.fX"), True)

print("\n=== Schicht 2b: Schalter an + passende Whitelist ===")
s = load(allow="1", whitelist="GVL_Anim.*,MAIN.stHmi.*")
check("GVL_Anim.fAxisX -> erlaubt", s.check_write_allowed("GVL_Anim.fAxisX"), False)
check("MAIN.stHmi.fPos -> erlaubt", s.check_write_allowed("MAIN.stHmi.fPos"), False)
check("MAIN.irgendwas -> nicht auf Whitelist", s.check_write_allowed("MAIN.irgendwas"), True)

print("\n=== Schicht 3: Blacklist schlaegt Whitelist (Whitelist = ALLES) ===")
s = load(allow="1", whitelist="*")
gefaehrlich = [
    "MAIN.mMachine.m5H1SignalampelGruen.oQ",
    "MAIN.mMachine.mM1_Zufuehrung.m1Y1Vereinzelung1.mValvePos.oQ",
    "MAIN.mMachine.m1S3Bedienpanel1NH.iIn",
    "MAIN.mMachine.mM100_Rundtakttisch.m100M1ServoRtt.mSafetyAck.iIn",
    "MAIN.mMachine.mM100_Rundtakttisch.m100M1ServoRtt.AxRef.PlcToNc",
    "MAIN.mMachine.m1F3TemperaturSchaltschrank.iValue",
    "MAIN.mMachine.m1F2Sicherung230V.iIn",
]
for sym in gefaehrlich:
    check(sym[:56], s.check_write_allowed(sym), True)

print("\n=== Gegenprobe: harmlos, bei Whitelist=* erlaubt ===")
check("GVL_Anim.fAxisX -> erlaubt", s.check_write_allowed("GVL_Anim.fAxisX"), False)
check("MAIN.stHmi.nState -> erlaubt", s.check_write_allowed("MAIN.stHmi.nState"), False)

print("\n" + "=" * 66)
if FAILS:
    print(f"FEHLGESCHLAGEN: {len(FAILS)}")
    for f in FAILS:
        print(f"  - {f}")
    sys.exit(1)
print("ALLE GUARD-TESTS BESTANDEN")
