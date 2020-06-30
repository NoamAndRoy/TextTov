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


#	The '".\urls-results\2019-BBC-visitedUrls.txt"' file was not generated 
#	using this spider but by filtring the results from the BBC spider for 
#	the jargon project.


class WebSite(scrapy.Item):
	url = scrapy.Field()
	year = scrapy.Field()

class BBCUrlsSpider(CrawlSpider):
	name = "BBCUrlsSpider"
	allowed_domains = ["bbc.com"]

	YEAR = '2019'
	LIMIT_URLS_COUNT = 1000
	MATCH = r'.*\bwww\.bbc\.com\/news\/science-environment-.*$'

	visitedUrls = []
	start_urls  = ['https://www.bbc.com/news/science_and_environment']
	
	def __init__(self, *args, **kwargs):
		super(BBCUrlsSpider, self).__init__(*args, **kwargs)
		SignalManager(dispatcher.Any).connect(self.spiderClosed, signals.spider_closed)

	rules = (	
		Rule(LinkExtractor(
			allow=(MATCH),
			deny=(r'.*(m\.|\.test\.|\.stage\.|%|comments|\/live\/|\/athlete\/|\/weather\/).*'),
			restrict_xpaths="//body"),
			callback='parseArticle',
			follow=True),
		Rule(LinkExtractor(
			allow=(r'(\bnews\b)\D+(-\d+)$'), 
			deny=(r'.*(m\.|\.test\.|\.stage\.|%|comments|\/live\/|\/athlete\/|\/weather\/).*'), 
			restrict_xpaths="//body"), 
			follow=True),
    )

	def parseArticle(self, response):
		item = WebSite()
		item['url'] = self.cleanUrl(response.url)		
		item['year'] = str(self.getYearFromArray(response.xpath("//@data-seconds")))

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
			return datetime.datetime.fromtimestamp(int(array[0].extract())).year
		
		return None
	
	def spiderClosed(self, spider):
		if not os.path.exists("urls-results"):
			os.makedirs("urls-results")

		self.printUrlsToFiles("BBC-visitedUrls2.txt", "urls-results")

	def printUrlsToFiles(self, filename, folder = ""):
		folderPath = folder + "/" if folder else ""

		with open(folderPath + self.YEAR + "-" + filename, 'a') as f:
			for url in self.visitedUrls:
				f.write(url+"\n")
			f.close()
