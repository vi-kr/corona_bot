#!/usr/bin/python3
import os
import csv
import scrapy
import pathlib
from datetime import datetime
from scrapy.crawler import CrawlerProcess

class FallzahlenSpider(scrapy.Spider):
    name = 'fallzahlen'
    allowed_domains = ['rki.de']
    start_urls = ['https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Fallzahlen.html/']

    def parse(self, response):
        felder = []
        i = 0
        for row in response.xpath('//tbody//tr'):
            felder.append( {
                'Land' : row.xpath('td[1]//text()').extract_first(),
                'Anzahl' : row.xpath('td[2]//text()').extract_first(),
                'Dif­fe­renz' : row.xpath('td[3]//text()').extract_first(),
                'Fälle' : row.xpath('td[4]//text()').extract_first(),
                'Inzidenz' : row.xpath('td[5]//text()').extract_first(),
                'Tode' : row.xpath('td[6]//text()').extract_first(),
                } )
            i = i + 1
        filename = (str(pathlib.Path(__file__).resolve().parents[2])
                   + os.path.sep + "data"
                   + os.path.sep + datetime.now().strftime("%Y%m%d") + ".csv")
        with open(filename, 'w', encoding='utf8', newline='') as output_file:
            fc = csv.DictWriter(output_file, 
                                fieldnames=felder[0].keys())
            fc.writeheader()
            fc.writerows(felder)
            
            
c = CrawlerProcess()
c.crawl(FallzahlenSpider)
c.start()
