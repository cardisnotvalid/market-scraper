import time
import aiohttp
import asyncio
from typing import List, Dict, Any

from market_scraper.logger import logger
from market_scraper.utils import load_config, save_json
from market_scraper.paths import ANIBIS_DIR


class Anibis:
    base_url = "https://api.anibis.ch/v4/fr"
    
    def __init__(self, max_concurrent_tasks: int = 10) -> None:
        self.save_ads = load_config()["save_ads"]
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def get_categories(self, id: int = 1) -> dict:
        url = f"{self.base_url}/search/categories?cid={id}"
        try:
            async with self.session.get(url) as response:
                return await response.json()
        except Exception as ex:
            logger.error(f"Ошибка при получении категорий: {str(ex)}")
            return

    async def get_sub_categories(self, categories: List[Dict[str, Any]]) -> List[int]:
        tasks = [self.get_categories(category["id"]) for category in categories if category.get("id")]
        return await asyncio.gather(*tasks)

    async def collect_all_categories(self) -> List[Dict[str, Any]]:
        logger.info("[Anibis] Процесс получение всех категорий")
        
        main_categories = await self.get_categories()
        main_sub_categories = main_categories.get("categoryPath").get("children", [])
        main_sub_sub_categories = await self.get_sub_categories(main_sub_categories)
        
        all_categories = []
        for category in main_sub_sub_categories:
            for sub_category in category.get("categoryPath").get("children"):
                if  isinstance(sub_category, str) or not sub_category.get("children"):
                    continue
                for sub_sub_category in sub_category.get("children"):
                    all_categories.append(sub_sub_category)
        
        logger.info(f"[Anibis] Количество категорий: {len(all_categories)}")
        
        return all_categories
    
    async def fetch_ads(self, url: str, params: dict):
        try:
            async with self.session.get(url, params=params) as response:
                return ((await response.json()).get("listings", []))
        except:
            return []
    
    async def collect_ads(self, cun: str, name: str = None):
        logger.debug(f"[Anibis] Получение объявлений из {name}")
        
        last_page = await self.get_last_page(cun)

        tasks = []
        for page in range(1, last_page + 1):
            url = f"{self.base_url}/search/listings"
            params = {"cun": cun, "fcun": cun, "pi": page, "pr": 1}
            tasks.append(self.fetch_ads(url, params))
        
        start = time.monotonic()
        ads = [item for sublist in await asyncio.gather(*tasks) for item in sublist if item]
        delta = round(time.monotonic() - start, 3)
        
        logger.debug(f"[Anibis] Количетсво объявлений на {name}: {len(ads)} ({delta} сек)")
        
        return ads
    
    async def get_last_page(self, cun: str) -> int:
        page = 1
        while True:
            url = f"{self.base_url}/search/listings"
            params = {"cun": cun, "fcun": cun, "pi": page, "pr": 1}
            async with self.session.get(url, params=params) as response:
                if (await response.json()).get("status") == 404:
                    return page - 1
            page += 1
    
    async def collect_all_ads(self):
        categories = await self.collect_all_categories()
        
        logger.info("[Anibis] Процесс получение всех объявлений")
        
        async def collect_and_save_ads(category):
            name = category.get("name")
            cun = category.get("languageUrls").get("fr").rsplit("/")[-1]
            
            async with self.semaphore:
                ads_data = await self.collect_ads(cun, name)
                if self.save_ads:
                    save_json(ads_data, ANIBIS_DIR, name)
                return ads_data
        
        tasks = [collect_and_save_ads(category) for category in categories]
        
        start = time.monotonic()
        all_ads = await asyncio.gather(*tasks)
        delta = round(time.monotonic() - start, 3)
        
        logger.info(f"[Anibis] Время выполнения: {delta} сек")
        
        return all_ads

            