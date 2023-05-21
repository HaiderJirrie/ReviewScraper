from abc import ABC, abstractmethod
import time
from bs4 import BeautifulSoup
import aiohttp
import csv

class Scraper(ABC):
    def __init__(self, name, prefix, query, pageNumbervar):
        self.name = name
        self.hrefPrefix = prefix
        self.starterQuery = query
        self.pageNumberVar = pageNumbervar
        self.reviews = []

    @abstractmethod
    async def scrape(self):
        pass

    # Haalt de HTML van de website op
    @staticmethod
    async def getSoup(url):
        website = url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        async with aiohttp.ClientSession() as session:
            async with session.get(website, headers=headers) as response:
                content = await response.content.read()
                return BeautifulSoup(content, "html.parser")
            
    def getNextPageQuery(self, pageNumber):
        querySplit = self.starterQuery.split(self.pageNumberVar)
        nextPageQuery = querySplit[0] + self.pageNumberVar + str(pageNumber)
        querySecondHalf = querySplit[1]
        nextPageQuery = nextPageQuery + querySecondHalf[1:]

        return nextPageQuery

    async def run(self):
        startTime = time.time()
        
        with open('data/' + self.name + '_reviews.csv', 'w', newline='', encoding='utf-8') as File:
            reviewFieldnames = ['product_id', 'review_text']
            reviewWriter = csv.DictWriter(File, fieldnames=reviewFieldnames)
   
            print('\nReviews scrapen van ' + self.hrefPrefix + self.starterQuery + '...\n')
            await self.scrape()

            print('Reviews opslaan in csv...\n')
            reviewWriter.writeheader()
            for review in self.reviews:
                product_id, review_text = review 
                reviewWriter.writerow({'product_id': product_id, 'review_text': review_text})

            elapsedTime = round((time.time() - startTime), 1)
            print('Klaar in ' + str(elapsedTime) + ' seconden! Data ligt in ./data/' + self.name + '_reviews.csv\n')
