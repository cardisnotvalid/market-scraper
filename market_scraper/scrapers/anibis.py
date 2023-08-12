import aiohttp
import asyncio
from typing import List, Dict, Any

from market_scraper.logger import logger


class Anibis:
    base_url = "https://api.anibis.ch/v4/fr"
    
    def __init__(self) -> None:
        pass
    
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
        
        logger.debug(f"[Anibis] Количество категорий: {len(all_categories)}")
        
        return all_categories