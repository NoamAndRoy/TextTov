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
	year = scrapy.Field()

class PubmedNcbiUrlsSpider (CrawlSpider):
	name = "PubmedNcbiUrlsSpider "
	allowed_domains = ["pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov/pubmed"]

	YEAR = '2019'
	LIMIT_URLS_COUNT = 1000
	MATCH = r'.*\bpubmed.ncbi.nlm.nih.gov\/\d+\/?.*$'

	visitedUrls = []
	start_urls  = ['https://pubmed.ncbi.nlm.nih.gov/']

	def __init__(self, *args, **kwargs):
		super(PubmedNcbiUrlsSpider , self).__init__(*args, **kwargs)
		SignalManager(dispatcher.Any).connect(self.spiderClosed, signals.spider_closed)

	rules = (	
		Rule(LinkExtractor(allow=(MATCH), deny=(), restrict_xpaths="//body"), callback='parseArticle', follow=True),
		Rule(LinkExtractor(allow=(), deny=(), restrict_xpaths="//body"), follow=True),
	)

	def parseArticle(self, response):
		item = WebSite()
		item['url'] = self.cleanUrl(response.url)		
		item['year'] = str(self.getYearFromArray(response.css("span.cit::text")))

		if item['year'] == self.YEAR and item['url'] not in self.visitedUrls:
			self.visitedUrls.append(response.url)

			print("Found", len(self.visitedUrls), "urls")

			if len(self.visitedUrls) == self.LIMIT_URLS_COUNT:
				raise CloseSpider('LIMIT_URLS_COUNT')

			return item

	def cleanUrl(self, url):
		if(url.startswith('https')):
			url = url.replace('https', 'http')

		return url

	def getYearFromArray(self, array):
		if len(array) >= 1:
			return array[0].extract().split(" ")[0]
		
		return None
	
	def spiderClosed(self, spider):
		if not os.path.exists("urls-results"):
			os.makedirs("urls-results")

		self.printUrlsToFiles("PubmedNcbi-visitedUrls.txt", "urls-results")

	def printUrlsToFiles(self, filename, folder = ""):
		folderPath = folder + "/" if folder else ""

		with open(folderPath + self.YEAR + "-" + filename, 'a') as f:
			for url in self.visitedUrls:
				f.write(url+"\n")
			f.close()
