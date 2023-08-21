import os
import yaml
import string
import asyncio
import aiofiles

from market_scraper.paths import CONFIG_PATH, ANIBIS_DIR, OUT_DIR


def load_config() -> dict:
    with open(CONFIG_PATH) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def collect_files_to_one() -> None:
    files = os.listdir(ANIBIS_DIR)
    datas = []
    for file in files:
        filepath = ANIBIS_DIR / file
        with open(filepath, encoding="utf-8") as file:
            datas += file.read().split()
    
    datas = [data for data in datas if data.startswith("https")]

    out_filename = "anibis.txt"
    out_filepath = OUT_DIR / out_filename
    with open(out_filepath, "a", encoding="utf-8") as file:
        for data in datas:
            file.write(data + "\n")



def sanitize_filename(filename: str) -> str:
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    sanitized_filename = ''.join(c for c in filename if c in valid_chars)
    return sanitized_filename


async def clear_files() -> None:
    files = os.listdir(ANIBIS_DIR)
    
    async def process_task(filepath):
        async with aiofiles.open(filepath, "r", encoding="utf-8") as file:
            text = list(set((await file.read()).split()))
            
        async with aiofiles.open(filepath, "w", encoding="utf-8") as file:
            for line in text:
                await file.write(line + "\n")
    
    tasks = [process_task(ANIBIS_DIR / file) for file in files]
    await asyncio.gather(*tasks)
    

async def save_ads(data: str, filename: str) -> None:
    filename = sanitize_filename(f"{filename.strip()}.txt")
    filepath = ANIBIS_DIR / filename
    
    async with aiofiles.open(filepath, mode="a") as file:
        await file.write(data + "\n")
        

async def valid_response(response) -> bool:
    if response.status in [200, 201, 204]:
        return True
    else:
        return False