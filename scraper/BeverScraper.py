import asyncio
import sys
import aiohttp
import math

from Scraper import Scraper

class BeverScraper(Scraper):
    def __init__(self, query):
        super().__init__("Bever", "https://www.bever.nl/", query, "page=")

    async def scrape(self):
        # Er wordt een query toegevoegd dat er voor zorgt dat er geen producten zonder reviews worden opgehaald.
        self.starterQuery = self.starterQuery + "?size=48&page=0&filter=%2526filter%253Daverage_rating%253A10%253Caverage_rating%253C50"
        # De eerste pagina met producten worden opgehaald.
        try:
            response = await self.getSoup(self.hrefPrefix + self.starterQuery)
            productPages = self.getNumberOfProductPages(response)
        except:
            print("scrapen heeft gefaald, controleer de URL\n")
            sys.exit()
        
        tasks = []
        for i in range(productPages):
            # Per pagina worden alle producten opgehaald
            productsOnPage = await self.getProductsOnPage(i)

            for product in productsOnPage:
                # Per product worden alle reviews opgehaald
                productId = self.getProductId(product)
                tasks.append(self.fetchReviews(productId))

        await asyncio.gather(*tasks)

    def getNumberOfProductPages(self, pagina):
        productCountSpanTag = pagina.find('span', {'data-qa': 'search_result_product-count'}).text.strip()
        productCount = int(productCountSpanTag.split(' producten')[0])
        # Bij Bever kan een pagina maximaal 48 producten bevatten
        return math.ceil(productCount / 48)

    async def getProductsOnPage(self, page):
        response = await self.getSoup(self.hrefPrefix + self.getNextPageQuery(page))
        return response.find_all('a', {'class': 'as-a-link as-a-link--container as-m-product-tile__link'})
    
    def getProductId(self, productATag):
        # In de URL van een product kan de 10 karakter lange productId eruit worden gesplit.
        # voorbeeld van zo'n URL: /p/meindl-bernina-2-comfort-fit-bergschoenen-HBBAC32002.html?colour=3623
        productLink = productATag.get('href')
        linkSplit = productLink.split('.html?')
        return linkSplit[0][-10:]

    async def fetchReviews(self, productId):
        response = await self.fetchReviewData(productId, 1) # haalt JSON met review informatie op
        numberOfPages = self.getNumberOfReviewPages(response)

        tasks = []
        for i in range(numberOfPages):
            tasks.append(self.fetchReviewData(productId, i + 1))

        # Bevat alle JSON review responses van het product
        fetchedDataList = await asyncio.gather(*tasks)

        for fetchedData in fetchedDataList:
            if fetchedData is not None and 'body' in fetchedData and 'reviews' in fetchedData['body']:
                for review in fetchedData['body']['reviews']:
                    if review.get('text'):
                        # Reviews van Bever bestaan uit "good_points" en "bad_points",
                        # die worden hier samegevoegd tot 1 string
                        goodPoints = review["text"].get("good_points", "")
                        badPoints = review["text"].get("bad_points", "")
                        reviewText = ' '.join(filter(None, [str(goodPoints), str(badPoints)]))
                        reviewText = ' '.join(reviewText.split())
                        self.reviews.append((productId, reviewText))

    async def fetchReviewData(self, productId, page):
        reviewUrl = 'https://widgets.reevoo.com/api/product_reviews?per_page=10&trkref=BEV&sku=' + productId + '&locale=nl-NL&display_mode=embedded&page=' + str(page)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(reviewUrl) as response:
                contentType = response.headers.get('Content-Type', '').lower()
                
                #Het kan voorkomen dat de response geen JSON content type is
                if 'application/json' in contentType:
                    return await response.json()
                else:
                    return None

    def getNumberOfReviewPages(self, response):
        # In de review JSON bestaat een variabel met het totaal aantal reviews.
        numberOfReviews = response['header']['num_of_reviews']
        numberOfReviewTrimmed = ''.join(filter(str.isdigit, numberOfReviews))
        # ieder response bevat maximaal 10 reviews
        return math.ceil(int(numberOfReviewTrimmed) / 10)