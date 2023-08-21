import json
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from aiohttp import ClientSession, TCPConnector

from typing import List, Dict, Tuple, Any
from market_scraper.logger import logger
from market_scraper.utils import save_ads


class Anibis:
    base_api_url = "https://api.anibis.ch/v4/fr"
    base_url = "https://www.anibis.ch"
    
    def __init__(
        self,
        max_concurrent_tasks: int, 
        seller_date: List[str] = ("20.05.2013", "13.08.2023"),
        ads_date: List[str] = ("20.05.2013", "13.08.2023"),
        ads_count: int = 1, 
        price: List[float] = (0.0, 1000000.0),
        chf_currency: float = 100.0
    ) -> None:
        self.seller_date = self.convert_to_strptime(seller_date)
        self.ads_date = self.convert_to_strptime(ads_date)
        self.ads_count = ads_count
        self.price = price
        self.chf_currency = chf_currency
        
        self.connector = TCPConnector(verify_ssl=False)
        self.session = ClientSession(connector=self.connector)
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args, **kwargs):
        await self.session.close()
    
    async def get_categories(self, id: int = 1) -> Dict[str, Any]:
        url = f"{self.base_api_url}/search/categories?cid={id}"
        try:
            async with self.session.get(url) as response:
                return await response.json()
        except Exception as ex:
            logger.error(f"Ошибка при получении категорий: {str(ex)}")
            return

    async def get_sub_categories(self, categories: List[Dict[str, Any]]) -> List[int]:
        async def process_sub_categories(id):
            async with self.semaphore:
                return await self.get_categories(id)
        
        tasks = [
            asyncio.create_task(process_sub_categories(category["id"]))
            for category in categories if category.get("id")
        ]
        
        return await asyncio.gather(*tasks)

    async def get_all_categories(self) -> List[Dict[str, Any]]:
        logger.info("[Anibis] Процесс получение всех категорий")
        
        await asyncio.sleep(2.5)
        
        main_categories = await self.get_categories()
        main_sub_categories = main_categories.get("categoryPath", {}).get("children", [])
        main_sub_sub_categories = await self.get_sub_categories(main_sub_categories)
        
        all_categories = []
        for category in main_sub_sub_categories:
            for sub_category in category.get("categoryPath", {}).get("children", []):
                if isinstance(sub_category, dict) and sub_category.get("children"):
                    all_categories.extend(sub_category["children"])
        
        logger.info(f"[Anibis] Кол-во категорий: {len(all_categories)}")
        
        return all_categories
    
    async def fetch_ads_data(self, cun: str, name: str) -> List[Dict[str, str]]:
        # async def process_fetch_ads_listings(cun, page):
        #     async with self.semaphore:
        #         return await self.fetch_ads_listings(cun, page)
                
        last_page = await self.get_last_page(cun)
        ads_listings_tasks = [
            asyncio.create_task(self.fetch_ads_listings(cun, page)) 
            for page in range(1, last_page + 1)
        ]
        ads_listings_list = await asyncio.gather(*ads_listings_tasks)
        ads_listings_result = [item for sublist in ads_listings_list for item in sublist if item]
    
        logger.debug(f"[Anibis] Кол-во объявлений {name}: {sum(len(item) for item in ads_listings_result)}")
        
        # async def process_fetch_ads_page_data(url):
        #     async with asyncio.Semaphore(5):
        #         return await self.fetch_ads_page_data(url)
        
        ads_data_tasks = [
            asyncio.create_task(self.fetch_ads_page_data(ads["url"], ads["category"]["name"]))
            for ads in ads_listings_result
        ]
        ads_data_list = await asyncio.gather(*ads_data_tasks)

        logger.debug(f"[Anibis] Проверено {name}: {sum(len(item) for item in ads_data_list if item)}")
    
    async def collect_all_ads(self, all_categories: List[str]):
        logger.info("[Anibis] Процесс получение всех объявлений")
        
        async def task_collect_ads(name, url):
            async with self.semaphore:
                logger.debug(f"[Anibis] Категория: {name}")
                return await self.fetch_ads_data(name, url)
        
        collecting_tasks = [
            asyncio.create_task(
                task_collect_ads(
                    category["name"], 
                    category["languageUrls"]["fr"].split("/")[-1]
                )
            )
            for category in all_categories
        ]
        all_ads_data = await asyncio.gather(*collecting_tasks)
        
        logger.info(f"[Anibis] Количество проверенных объявлений {len(all_ads_data)}")
        
        return all_ads_data
    
    async def get_last_page(self, cun: str) -> int:
        async with self.session.get(
            url=f"{self.base_api_url}/search/listings", 
            params={"cun": cun, "fcun": cun, "pi": 1, "pr": 1}
        ) as response:
            return (await response.json())["pagingInfo"]["totalItems"] // 20 + 1
    
    async def fetch_ads_listings(self, cun: str, page: int) -> List[Dict[str, Any]]:
        async with self.session.get(
            url=f"{self.base_api_url}/search/listings", 
            params={"cun": cun, "fcun": cun, "pi": page, "pr": 1}
        ) as response:
            return ((await response.json()).get("listings", []))
    
    async def fetch_ads_page_data(self, url: str, name: str) -> Dict[str, str] | None:
        response = await self.session.get(self.base_url + url)
        page_content = await response.text()
        
        soup = BeautifulSoup(page_content, "lxml")
        
        if soup.select_one("div.gGjkaC") is None or soup.select_one("script#state") is None:
            return None
        
        script = soup.select_one("script#state").string
        ads_data = script.split('"detail":', 1)[-1]
        ads_data = json.loads(ads_data.rsplit(',"error":')[0])
        ads_data = self.formatting_ads_data(ads_data)
        
        if self.is_data_valid(ads_data):
            valid_url = self.base_url + ads_data.get("languageUrls", {}).get("fr", "")
            await save_ads(valid_url, name)
        else:
            return None
                    
    def is_data_valid(self, ads_data: Dict[str, Any]) -> bool:
        seller = ads_data.get("seller", {})
        
        seller_date = seller.get("registrationDate")
        if seller_date is None:
            return
        
        ads_count = seller.get("amountOfActiveListings")
        if ads_count is None:
            return
        
        ads_date = ads_data.get("formattedModified")
        if ads_date is None:
            return
        
        price = ads_data.get("price")
        if price is None:
            return
        
        ads_date = datetime.strptime(ads_date, "%d.%m.%Y")
        seller_date = datetime.strptime(seller_date, "%d.%m.%Y")
        
        return all([
            self.seller_date[0] <= seller_date <= self.seller_date[1],
            self.ads_date[0] <= ads_date <= self.ads_date[1],
            self.ads_count <= ads_count,
            self.price[0] <= price * self.chf_currency <= self.price[1]
        ])

    
    def convert_to_strptime(self, date: Tuple[str, str]) -> Tuple[datetime, datetime]:
        start_range = datetime.strptime(date[0], "%d.%m.%Y")
        end_range = datetime.strptime(date[1], "%d.%m.%Y")
        return start_range, end_range
    
    def formatting_ads_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        formatted_data = data
        if not data.get("seller", {}).get("registrationDate"):
            formatted_data.setdefault("seller", {}).setdefault("registrationDate", "00.00.0000")
        else:
            formatted_data["seller"]["registrationDate"] = data["seller"]["registrationDate"].rsplit(" ")[-1]
        return formatted_data
