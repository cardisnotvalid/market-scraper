from pathlib import Path
from os import makedirs

ROOT        = Path(__file__).resolve().parent
LOG_DIR     = ROOT / "logs"
JSON_DIR    = ROOT / "json"
OUT_DIR     = ROOT.parent / "output"

ANIBIS_DIR  = JSON_DIR / "anibis"

CONFIG_PATH = ROOT.parent / "config.yaml"

makedirs(LOG_DIR,    exist_ok=True)
makedirs(OUT_DIR,    exist_ok=True)

makedirs(JSON_DIR,   exist_ok=True)
makedirs(ANIBIS_DIR, exist_ok=True)