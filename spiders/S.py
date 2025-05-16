import csv
import os
import time
from random import random
from typing import Iterable
import random
import requests
import scrapy
from scrapy import Request
from datetime import datetime

from scrapy.utils import spider

class SSpider(scrapy.Spider):
    name = "S"

    start_urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
                'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
                  'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
                'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
                'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
                'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
                'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
                'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17']

    custom_settings = {
        # 'DOWNLOAD_DELAY': 6,
        'COOKIES_ENABLED': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 3,
        "REDIRECT_ENABLED": True,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DOWNLOAD_TIMEOUT": 180,
        "HTTPERROR_ALLOWED_CODES": [502, 401],
        "RETRY_TIMES": 2,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls_queue = list(self.start_urls)
        self.active_requests = 0
        self.current_url_index = 0
        self.sheriff_file = 'sheriff_nums.txt'
        if not os.path.exists(self.sheriff_file):
            open(self.sheriff_file, 'w').close()
        with open(self.sheriff_file, 'r', encoding='utf-8') as f:
            self.saved_nums = set(line.strip() for line in f if line.strip())
        self.redirect_302_count = 0  # счётчик 302 редиректов
    #
    def start_requests(self):
        if self.start_urls:
            yield scrapy.Request(
                url=self.start_urls[0],
                callback=self.parse,
                meta={'url_index': 0}
            )

    def is_new_sheriff_num(self, sheriff_num):
        return sheriff_num not in self.saved_nums

    def schedule_next_url(self, current_index):
        next_index = current_index + 1
        if next_index < len(self.start_urls):
            next_url = self.start_urls[next_index]
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={'url_index': next_index}
            )
    def parse(self, response):
        self.active_requests = 0  # Сброс на начало новой страницы
        part_url_lst = response.xpath('//table[@class="table table-striped "]/tr')#('//table[@class="table table-striped "]/tr') '//table[@class="table table-striped "]/tbody/tr' or
        print(len(part_url_lst))
        county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
        for part_url in part_url_lst:
            url = response.urljoin(part_url.xpath(".//a/@href").get())
            sheriff_num = part_url.xpath('./td[2]/text()').get().strip()
            if sheriff_num and self.is_new_sheriff_num(sheriff_num):
                self.active_requests += 1
                yield scrapy.Request(
                    url,
                    callback=self.parse_article_enc,
                    meta={
                        'County': county,
                        'SheriffNum': sheriff_num,
                        'url_index': response.meta['url_index']
                    }
                )
        if self.active_requests == 0:
            yield from self.schedule_next_url(response.meta['url_index'])


    def extract_with_xpath(self, response, *xpaths):
        for xpath in xpaths:
            data = response.xpath(f'normalize-space({xpath})').get()
            if data:
                return data.strip()
        return None

    def clean_text(self, text):
        if text:
            return text.replace('ET AL.', '').replace('ET. ALS.', '').replace('ET ALS.', '').strip()
        return text

    def parse_article_enc(self, response):
        try:
            sales_date = self.extract_with_xpath(response,'//div[contains(text(), "Sales Date")]/following-sibling::div',
                                    '//div[contains(text(), "Sale Date")]/following-sibling::div') or None
        except:
            sales_date = ''

        if sales_date:
            data= {
                    'Country': response.meta['County'],
                    'Sheriff #': response.meta['SheriffNum'],
                    'Sales Date': sales_date,
                    'Defendant': self.clean_text(self.extract_with_xpath(response,
                                                         '//div[contains(text(), "Defendant")]/following-sibling::div')) or None,

                    'Address': self.extract_with_xpath(response,
                                                       '//div[contains(text(), "Address")]/following-sibling::div') or None,
                    'Description': self.extract_with_xpath(response,
                                                           '//div[contains(text(), "Description")]/following-sibling::div//text()') or None,
                    'Approx. Upset*': self.extract_with_xpath(response,
                                                              '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()') or None,
                    'Approx. Judgment*': self.extract_with_xpath(response, '//div[contains(text(), "Judgment")]/following-sibling::div//text()') or None,
                    'Good Faith Upset': self.extract_with_xpath(response,'//div[contains(text(), "Good Faith Upset*")]/following-sibling::div//text()') or None,
                    'URL': response.url
                }
            with open ('05_05_25.csv', 'a', newline='', encoding='UTF-8') as f:
                w = csv.DictWriter(f, data.keys())
                if f.tell() == 0:
                    w.writeheader()
                w.writerow(data)
            important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
            if all(data[k] for k in important_keys):
                sheriff_num = data['Sheriff #']
                with open(self.sheriff_file, 'a', encoding='utf-8') as f:
                    f.write(sheriff_num + '\n')
                    self.saved_nums.add(sheriff_num)
                    yield data
        self.active_requests -= 1
        if self.active_requests == 0:
            yield from self.schedule_next_url(response.meta['url_index'])



