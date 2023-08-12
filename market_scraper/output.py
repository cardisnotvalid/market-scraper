import json
from market_scraper.paths import OUT_DIR

def write_txt(mail: str, password: str, filename: str = "accounts"):
    filename = filename + ".txt"
    filepath = OUT_DIR / filename
    with filepath.open("a", encoding="utf-8") as file:
        file.write(f"{mail}:{password}\n")

def write_json(accounts: list, filename: str = "accounts"):
    filename = filename + ".json"
    filepath = OUT_DIR / filename

    data = [{username: password} for username, password in accounts]

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
