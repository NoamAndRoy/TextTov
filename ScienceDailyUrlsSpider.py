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

class ScienceDailyUrlsSpider(CrawlSpider):
	name = "ScienceDailyUrlsSpider"
	allowed_domains = ["sciencedaily.com"]

	YEAR = '2019'
	LIMIT_URLS_COUNT = 1000
	MATCH = r'.*\bwww.sciencedaily.com/releases/%s.*$' % YEAR

	visitedUrls = []
	start_urls  = ['https://www.sciencedaily.com']
	
	def __init__(self, *args, **kwargs):
		super(ScienceDailyUrlsSpider, self).__init__(*args, **kwargs)
		SignalManager(dispatcher.Any).connect(self.spiderClosed, signals.spider_closed)

	rules = (	
		Rule(LinkExtractor(allow=(MATCH), deny=(), restrict_xpaths="//body"), callback='parseArticle', follow=True),
		Rule(LinkExtractor(allow=(), deny=(), restrict_xpaths="//body"), follow=True),
	)

				
	def parseArticle(self, response):
		item = WebSite()
		item['url'] = self.cleanUrl(response.url)	

		if item['url'] not in self.visitedUrls:
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

		self.printUrlsToFiles("ScienceDaily-visitedUrls-gggg.txt", "urls-results")

	def printUrlsToFiles(self, filename, folder = ""):
		folderPath = folder + "/" if folder else ""

		with open(folderPath + self.YEAR + "-" + filename, 'a') as f:
			for url in self.visitedUrls:
				f.write(url+"\n")
			f.close()
