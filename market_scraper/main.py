from market_scraper.logger import logger
from market_scraper.scrapers.anibis import Anibis
from market_scraper.utils import load_config, clear_files, collect_files_to_one


config = load_config()


async def main():
    max_concurrent_tasks = config["max_concurrent_tasks"]
    
    seller_date = config["seller_date"]
    ads_date = config["ads_date"]
    ads_count = config["ads_count"]
    price = config["price"]
    chf_currency = config["CHF"]
    
    logger.info(f"Регистрация продавца: {seller_date[0]} - {seller_date[1]}")
    logger.info(f"{'Дата объявления:':<21} {ads_date[0]} - {ads_date[1]}")
    logger.info(f"{'Кол-во объявлений:':<21} {ads_count}")
    logger.info(f"{'Диапазон цен:':<21} {price[0]} - {price[1]}₽")
    logger.info(f"{'Курс валюты CHF:':<21} {chf_currency}₽\n")
    
    try:
        async with Anibis(
            max_concurrent_tasks=max_concurrent_tasks,
            seller_date=seller_date,
            ads_date=ads_date,
            ads_count=ads_count,
            price=price,
            chf_currency=chf_currency
        ) as anibis:
            all_categories = await anibis.get_all_categories()
            await anibis.collect_all_ads(all_categories)
    finally:
        await clear_files()
        collect_files_to_one()