import scrapy
import os
import re
import csv
import datetime
import operator
from string import printable
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.signalmanager import SignalManager
from scrapy.exceptions import CloseSpider
from scrapy import signals
from pydispatch import dispatcher

class WebSite(scrapy.Item):
    url = scrapy.Field()
    date = scrapy.Field()

class PopsciUrlsSpider(CrawlSpider):
	name = "PopsciUrlsSpider"
	allowed_domains = ["popsci.com"]

	YEAR = '2019'
	LIMIT_URLS_COUNT = 1000
	MATCH = r'.*\b.popsci.com/.*'

	visitedUrls = []
	start_urls  = ['https://www.popsci.com/','https://www.popsci.com/coronavirus/','https://www.popsci.com/science/','https://www.popsci.com/technology/','https://www.popsci.com/diy/','https://www.popsci.com/health/','https://www.popsci.com/goods/','https://www.popsci.com/all-articles/','https://www.popsci.com/tags/archives/']
	
	def __init__(self, *args, **kwargs):
		super(PopsciUrlsSpider, self).__init__(*args, **kwargs)
		SignalManager(dispatcher.Any).connect(self.spiderClosed, signals.spider_closed)

	rules = (	
		Rule(LinkExtractor(allow=(MATCH), deny=(), restrict_xpaths="//body"), callback='parseArticle', follow=True),
		Rule(LinkExtractor(allow=(), deny=(), restrict_xpaths="//body"), follow=True),
	)

				
	def parseArticle(self, response):
		if len(response.xpath("//span[contains(@class,'article_byline')]/span")) == 0:
			return

		item = WebSite()
		item['url'] = self.cleanUrl(response.url)
		item['date'] = response.xpath("//span[contains(@class,'article_byline')]/span")[0].extract()	

		if self.YEAR in item['date'] and item['url'] not in self.visitedUrls:
			self.visitedUrls.append(item['url'] )

			print("Found", len(self.visitedUrls), "urls")

			if len(self.visitedUrls) == self.LIMIT_URLS_COUNT:
				raise CloseSpider('LIMIT_URLS_COUNT')

			return item

	def cleanUrl(self, url):
		if(url.startswith('https')):
			url = url.replace('https', 'http')

		return url
	
	def spiderClosed(self, spider):
		if not os.path.exists("urls-results"):
			os.makedirs("urls-results")

		self.printUrlsToFiles("Popsci-visitedUrls.txt", "urls-results")

	def printUrlsToFiles(self, filename, folder = ""):
		folderPath = folder + "/" if folder else ""

		with open(folderPath + self.YEAR + "-" + filename, 'a') as f:
			for url in self.visitedUrls:
				f.write(url+"\n")
			f.close()
