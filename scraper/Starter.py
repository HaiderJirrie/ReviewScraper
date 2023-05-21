import asyncio
from BeverScraper import BeverScraper

async def start():
    Bever = BeverScraper('c/heren/schoenen/wandelschoenen.html')

    tasks = [Bever.run()]
    await asyncio.gather(*tasks)

asyncio.run(start())