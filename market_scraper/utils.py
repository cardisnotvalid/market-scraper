import json
import yaml
from pathlib import Path
from typing import List, Dict, Any

from market_scraper.logger import logger
from market_scraper.paths import CONFIG_PATH, JSON_DIR


def load_config() -> dict:
    with open(CONFIG_PATH) as file:
        return yaml.load(file, Loader=yaml.FullLoader)
    

def save_json(data: List[Dict[str, Any]], site: Path, filename: str) -> None:
    formatted_filename = filename.lower().replace(' ', '_').replace("/", "_").replace(",", "").replace(":", "")
    filename = f"{formatted_filename}.json"
    filepath = JSON_DIR / site / filename
    
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        
    logger.debug(f"Данные сохранены в файле {filename}")