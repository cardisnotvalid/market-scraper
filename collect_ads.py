import asyncio
from market_scraper.utils import clear_files, collect_files_to_one


async def main():
    await clear_files()
    collect_files_to_one()
    

if __name__ == "__main__":
    asyncio.run(main())