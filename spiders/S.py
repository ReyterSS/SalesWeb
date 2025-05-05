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


# class SSpider(scrapy.Spider):
#     name = "S"
#
#     start_urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
#                   'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17']
#
#     custom_settings = {
#         'DOWNLOAD_DELAY': 6,
#         'COOKIES_ENABLED': True,
#         'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
#         'CONCURRENT_REQUESTS_PER_IP': 1,
#         'AUTOTHROTTLE_ENABLED': True,
#         'AUTOTHROTTLE_START_DELAY': 1,
#         'AUTOTHROTTLE_MAX_DELAY': 3,
#         "REDIRECT_ENABLED": True,
#         "RANDOMIZE_DOWNLOAD_DELAY": True,
#         "DOWNLOAD_TIMEOUT": 240,
#         "HTTPERROR_ALLOWED_CODES": [502, 401],
#         "RETRY_TIMES": 2,
#     }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.start_urls_queue = list(self.start_urls)
#         self.active_requests = 0
#         self.current_url_index = 0
#         self.sheriff_file = 'sheriff_nums.txt'
#         if not os.path.exists(self.sheriff_file):
#             open(self.sheriff_file, 'w').close()
#         with open(self.sheriff_file, 'r', encoding='utf-8') as f:
#             self.saved_nums = set(line.strip() for line in f if line.strip())
#         self.redirect_302_count = 0  # счётчик 302 редиректов
#     #
#     def start_requests(self):
#         if self.start_urls:
#             yield scrapy.Request(
#                 url=self.start_urls[0],
#                 callback=self.parse,
#                 meta={'url_index': 0}
#             )
#
#     def is_new_sheriff_num(self, sheriff_num):
#         return sheriff_num not in self.saved_nums
#
#     def schedule_next_url(self, current_index):
#         next_index = current_index + 1
#         if next_index < len(self.start_urls):
#             next_url = self.start_urls[next_index]
#             yield scrapy.Request(
#                 url=next_url,
#                 callback=self.parse,
#                 meta={'url_index': next_index}
#             )
#     def parse(self, response):
#         self.active_requests = 0  # Сброс на начало новой страницы
#         part_url_lst = response.xpath('//table[@class="table table-striped "]/tr')
#         county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
#         for part_url in part_url_lst:
#             url = response.urljoin(part_url.xpath(".//a/@href").get())
#             sheriff_num = part_url.xpath('./td[2]/text()').get().strip()
#             if sheriff_num and self.is_new_sheriff_num(sheriff_num):
#                 self.active_requests += 1
#                 yield scrapy.Request(
#                     url,
#                     callback=self.parse_article_enc,
#                     meta={
#                         'County': county,
#                         'SheriffNum': sheriff_num,
#                         'url_index': response.meta['url_index']
#                     }
#                 )
#         if self.active_requests == 0:
#             yield from self.schedule_next_url(response.meta['url_index'])
#
#
#     def extract_with_xpath(self, response, *xpaths):
#         for xpath in xpaths:
#             data = response.xpath(f'normalize-space({xpath})').get()
#             if data:
#                 return data.strip()
#         return None
#
#     def clean_text(self, text):
#         if text:
#             return text.replace('ET AL.', '').replace('ET. ALS.', '').replace('ET ALS.', '').strip()
#         return text
#
#     def parse_article_enc(self, response):
#         try:
#             sales_date = self.extract_with_xpath(response,'//div[contains(text(), "Sales Date")]/following-sibling::div',
#                                     '//div[contains(text(), "Sale Date")]/following-sibling::div') or None
#         except:
#             sales_date = ''
#
#         if sales_date:
#             data= {
#                     'Country': response.meta['County'],
#                     'Sheriff #': response.meta['SheriffNum'],
#                     'Sales Date': sales_date,
#                     'Defendant': self.clean_text(self.extract_with_xpath(response,
#                                                          '//div[contains(text(), "Defendant")]/following-sibling::div')) or None,
#
#                     'Address': self.extract_with_xpath(response,
#                                                        '//div[contains(text(), "Address")]/following-sibling::div') or None,
#                     'Description': self.extract_with_xpath(response,
#                                                            '//div[contains(text(), "Description")]/following-sibling::div//text()') or None,
#                     'Approx. Upset*': self.extract_with_xpath(response,
#                                                               '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()') or None,
#                     'Approx. Judgment*': self.extract_with_xpath(response, '//div[contains(text(), "Judgment")]/following-sibling::div//text()') or None,
#                     'Good Faith Upset': self.extract_with_xpath(response,'//div[contains(text(), "Good Faith Upset*")]/following-sibling::div//text()') or None,
#                     'URL': response.url
#                 }
#             with open ('04_05_25.csv', 'a', newline='', encoding='UTF-8') as f:
#                 w = csv.DictWriter(f, data.keys())
#                 if f.tell() == 0:
#                     w.writeheader()
#                 w.writerow(data)
#             important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
#             if all(data[k] for k in important_keys):
#                 sheriff_num = data['Sheriff #']
#                 with open(self.sheriff_file, 'a', encoding='utf-8') as f:
#                     f.write(sheriff_num + '\n')
#                     self.saved_nums.add(sheriff_num)
#                     yield data
#         self.active_requests -= 1
#         if self.active_requests == 0:
#             yield from self.schedule_next_url(response.meta['url_index'])




# class SSpider(scrapy.Spider):
#     name = "S"
#
#     # start_urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2"]
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=10']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=7']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=15']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=73']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=8']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=9']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=17']
#     start_urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
#                   'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17']
#
#
#     custom_settings = {
#         'DOWNLOAD_DELAY': 6,
#         'COOKIES_ENABLED': True,
#         'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
#         'CONCURRENT_REQUESTS_PER_IP': 1,
#         'AUTOTHROTTLE_ENABLED': True,
#         'AUTOTHROTTLE_START_DELAY': 1,
#         'AUTOTHROTTLE_MAX_DELAY': 3,
#         "REDIRECT_ENABLED": True,
#         "RANDOMIZE_DOWNLOAD_DELAY": True,
#         "DOWNLOAD_TIMEOUT": 240,
#         "HTTPERROR_ALLOWED_CODES": [502, 401],
#         "RETRY_TIMES": 2,
#     }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.start_urls_queue = list(self.start_urls)
#         self.active_requests = 0
#         self.current_url_index = 0
#
#         self.sheriff_file = 'sheriff_nums.txt'
#         if not os.path.exists(self.sheriff_file):
#             open(self.sheriff_file, 'w').close()
#         with open(self.sheriff_file, 'r', encoding='utf-8') as f:
#             self.saved_nums = set(line.strip() for line in f if line.strip())
#         self.redirect_302_count = 0  # счётчик 302 редиректов
#     #
#     def start_requests(self):
#         if self.start_urls:
#             yield scrapy.Request(
#                 url=self.start_urls[0],
#                 callback=self.parse,
#                 meta={'url_index': 0}
#             )
#
#     # def parse_with_queue(self, response):
#         # здесь вся логика разбора страницы и вложенных запросов
#         # yield внутренние реквесты, как обычно
#         # ...
#
#         # когда всё закончено (если нужно вручную управлять — дождитесь последнего yield)
#         # запускаем следующий URL из списка
#         # index = response.meta['url_index']
#         # if index + 1 < len(self.start_urls):
#         #     next_url = self.start_urls[index + 1]
#         #     yield scrapy.Request(
#         #         url=next_url,
#         #         callback=self.parse_with_queue,
#         #         meta={'url_index': index + 1}
#         #     )
#     def is_new_sheriff_num(self, sheriff_num):
#         return sheriff_num not in self.saved_nums
#
#     def schedule_next_url(self, current_index):
#         next_index = current_index + 1
#         if next_index < len(self.start_urls):
#             next_url = self.start_urls[next_index]
#             yield scrapy.Request(
#                 url=next_url,
#                 callback=self.parse,
#                 meta={'url_index': next_index}
#             )
#     def parse(self, response):
#         # cookie_header = ''
#         # if b'Set-Cookie' in response.headers:
#         #     cookies = response.headers.getlist(b'Set-Cookie')
#         #     cookie_parts = [c.decode().split(';')[0] for c in cookies]
#         #     cookie_header = '; '.join(cookie_parts)
#         # AWSALB = cookie_header.split('AWSALB=')[1].split('; ')[0]
#         # ASP = cookie_header.split('ASP.NET_SessionId=')[1].split('; ')[0]
#         # AWSALBCORS = cookie_header.split('AWSALBCORS=')[1].split('; ')[0]
#         #     # print(AWSALB, ASP, AWSALBCORS)
#         headers = {
#                 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#                 'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
#                 'cache-control': 'no-cache',
#                 'pragma': 'no-cache',
#                 'priority': 'u=0, i',
#                 # 'referer': 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
#                 'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
#                 'sec-ch-ua-mobile': '?0',
#                 'sec-ch-ua-platform': '"Windows"',
#                 'sec-fetch-dest': 'document',
#                 'sec-fetch-mode': 'navigate',
#                 'sec-fetch-site': 'same-origin',
#                 'sec-fetch-user': '?1',
#                 'upgrade-insecure-requests': '1',
#                 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
#                 # 'Cookie': f'cookie_header'
#                 # 'Cookie': 'ASP.NET_SessionId=3exjiebvaqegxndh0zlegkfm; AWSALBCORS=wUygVR/ACf82cfkUECLXzJtWLKKFVRfAFf5koMUcMmnIlOsSXsTzqIhw5lpf6nFu2+EMHMJnWNYkvlQKI3MU7pOu5e+/jM2TpaHozq/wkNJ93gG1l+9yr52Na/SI; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=0yHZTu0Mrk5xi9zArrwX0ebb5NL043DhWWBgL9DA2GyYFxHBqF7OU5nYbfP9/Y44tCiEkcRqF20CmdOygxbtfEFhr3KTq2YTRxb1g3SCr9erdu4UzU9PJeHjxZ3w; AWSALBCORS=0yHZTu0Mrk5xi9zArrwX0ebb5NL043DhWWBgL9DA2GyYFxHBqF7OU5nYbfP9/Y44tCiEkcRqF20CmdOygxbtfEFhr3KTq2YTRxb1g3SCr9erdu4UzU9PJeHjxZ3w'
#                 # 'Cookie': 'ASP.NET_SessionId=dq0ggiqk1ik4cyuiiyf0n5do; AWSALB=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; AWSALBCORS=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; AWSALBCORS=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y',
#                 # 'Cookie': f'ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}; ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}'
#                 # 'Cookie': f'AWSALB={AWSALB}; AWSALBCORS={}; ASP.NET_SessionId=3juy4hmu5bptnm3xfhkzthh0'
#             }
#
#         # def parse(self, response):
#         self.active_requests = 0  # Сброс на начало новой страницы
#         part_url_lst = response.xpath('//table[@class="table table-striped "]/tr')
#         county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
#
#         for part_url in part_url_lst:
#             url = response.urljoin(part_url.xpath(".//a/@href").get())
#             sheriff_num = part_url.xpath('./td[2]/text()').get().strip()
#             if sheriff_num and self.is_new_sheriff_num(sheriff_num):
#                 self.active_requests += 1
#                 yield scrapy.Request(
#                     url,
#                     callback=self.parse_article_enc,
#                     meta={
#                         'County': county,
#                         'SheriffNum': sheriff_num,
#                         'url_index': response.meta['url_index']
#                     }
#                 )
#
#             # Если не было ни одного подзапроса — переход сразу к следующему
#         if self.active_requests == 0:
#             yield from self.schedule_next_url(response.meta['url_index'])
#
#
#
#
#         # part_url_lst = response.xpath('//table[@class="table table-striped "]/tr')
#         # county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
#         # for part_url in part_url_lst:
#         #     url = response.urljoin(part_url.xpath(".//a/@href").get())
#         #     sheriff_num = part_url.xpath('./td[2]/text()').get().strip()
#         #     if sheriff_num and self.is_new_sheriff_num(sheriff_num):
#         #     # self.logger.info(f"New: {sheriff_num} — {each_url}")
#         #         r = scrapy.Request(
#         #             url,
#         #             headers=headers,
#         #             callback=self.parse_article_enc,
#         #             meta={
#         #                     'County': county,
#         #                     'SheriffNum': sheriff_num
#         #             }
#         #         )
#         #         yield r
#
#         # if self.start_urls_queue:
#         #     next_url = self.start_urls_queue.pop(0)
#         #     yield scrapy.Request(next_url, callback=self.parse)
#
#         # index = response.meta['url_index']
#         # if index + 1 < len(self.start_urls):
#         #     next_url = self.start_urls[index + 1]
#         #     yield scrapy.Request(
#         #         url=next_url,
#         #         callback=self.parse_with_queue,
#         #         meta={'url_index': index + 1}
#         #     )
#
#     def extract_with_xpath(self, response, *xpaths):
#         for xpath in xpaths:
#             data = response.xpath(f'normalize-space({xpath})').get()
#             if data:
#                 return data.strip()
#         return None
#
#     def clean_text(self, text):
#         if text:
#             return text.replace('ET AL.', '').replace('ET. ALS.', '').replace('ET ALS.', '').strip()
#         return text
#
#     def parse_article_enc(self, response):
#         # if response.status == 302 or "SalesDetails" in response.url:
#         #     self.redirect_302_count += 1
#         #     self.logger.warning(f"302 redirect detected ({self.redirect_302_count}/3): {response.url}")
#         #
#         #     if self.redirect_302_count >= 3:
#         #         self.logger.warning("Got 3 consecutive 302s, sleeping for 240s and refreshing cookies...")
#         #         time.sleep(240)
#         #         self.redirect_302_count = 0
#         #         # Возврат к главной для получения свежих cookies
#         #         yield scrapy.Request(
#         #             url="https://salesweb.civilview.com/",
#         #             callback=self.parse,
#         #             dont_filter=True
#         #         )
#         #
#         #     # просто пропустить текущий 302
#         #     return
#         #
#         # self.redirect_302_count = 0  # сброс, если всё ок
#
#         # if response.status == 302:
#         #     index_page = response.meta['url_index']
#         #     url = self.start_urls[index_page]
#         #     yield Request(
#         #         url=url,
#         #         callback=self.parse,
#         #         dont_filter=True
#         #     )
#         try:
#             sales_date = self.extract_with_xpath(response,'//div[contains(text(), "Sales Date")]/following-sibling::div',
#                                     '//div[contains(text(), "Sale Date")]/following-sibling::div') or None
#         except:
#             sales_date = ''
#         if sales_date:
#             data= {
#                     'Country': response.meta['County'],
#                     'Sheriff #': response.meta['SheriffNum'],
#                     'Sales Date': sales_date,
#                     'Defendant': self.clean_text(self.extract_with_xpath(response,
#                                                          '//div[contains(text(), "Defendant")]/following-sibling::div')) or None,
#
#                     'Address': self.extract_with_xpath(response,
#                                                        '//div[contains(text(), "Address")]/following-sibling::div') or None,
#                     'Description': self.extract_with_xpath(response,
#                                                            '//div[contains(text(), "Description")]/following-sibling::div//text()') or None,
#                     'Approx. Upset*': self.extract_with_xpath(response,
#                                                               '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()') or None,
#                     'Approx. Judgment*': self.extract_with_xpath(response, '//div[contains(text(), "Judgment")]/following-sibling::div//text()') or None,
#                     'Good Faith Upset': self.extract_with_xpath(response,'//div[contains(text(), "Good Faith Upset*")]/following-sibling::div//text()') or None,
#                     'URL': response.url
#                 }
#             with open ('04_05_25.csv', 'a', newline='', encoding='UTF-8') as f:
#                 w = csv.DictWriter(f, data.keys())
#                 if f.tell() == 0:
#                     w.writeheader()
#                 w.writerow(data)
#             important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
#             if all(data[k] for k in important_keys):
#                 sheriff_num = data['Sheriff #']
#                 with open(self.sheriff_file, 'a', encoding='utf-8') as f:
#                     f.write(sheriff_num + '\n')
#                     self.saved_nums.add(sheriff_num)
#                     yield data
#
#         self.active_requests -= 1
#         if self.active_requests == 0:
#             yield from self.schedule_next_url(response.meta['url_index'])


# class SSpider(scrapy.Spider):
    # name = "S"
#     # start_urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2"]
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=10']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=7']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=15']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=73']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=8']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=9']
#     # start_urls = ['https://salesweb.civilview.com/Sales/SalesSearch?countyId=17']
#     start_urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
#                   'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
#                 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17']
#
#
#     custom_settings = {
#         'DOWNLOAD_DELAY': 6,
#         'COOKIES_ENABLED': True,
#         'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
#         'CONCURRENT_REQUESTS_PER_IP': 1,
#         'AUTOTHROTTLE_ENABLED': True,
#         'AUTOTHROTTLE_START_DELAY': 1,
#         'AUTOTHROTTLE_MAX_DELAY': 3,
#         "REDIRECT_ENABLED": True,
#         "RANDOMIZE_DOWNLOAD_DELAY": True,
#         "DOWNLOAD_TIMEOUT": 240,
#         "HTTPERROR_ALLOWED_CODES": [502, 401],
#         # "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
#         "RETRY_TIMES": 2,
#         # "AUTOTHROTTLE_ENABLED": True,
#         # "AUTOTHROTTLE_START_DELAY": 2,
#         # "AUTOTHROTTLE_MAX_DELAY": 5,
#         # "AUTOTHROTTLE_TARGET_CONCURRENCY": 1
#     }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         self.start_urls_queue = list(self.start_urls)
#
#         self.sheriff_file = 'sheriff_nums.txt'
#         if not os.path.exists(self.sheriff_file):
#             open(self.sheriff_file, 'w').close()
#         with open(self.sheriff_file, 'r', encoding='utf-8') as f:
#             self.saved_nums = set(line.strip() for line in f if line.strip())
#
#         self.redirect_302_count = 0  # счётчик 302 редиректов
#     #
#     def start_requests(self):
#         if self.start_urls:
#             # for num, i in enumerate(self.start_urls):
#             yield scrapy.Request(
#                 url=self.start_urls[0],
#                 callback=self.parse,
#                 meta={'url_index': 0}  # храним индекс текущего URL
#             )
#
#     # def parse_with_queue(self, response):
#         # здесь вся логика разбора страницы и вложенных запросов
#         # yield внутренние реквесты, как обычно
#         # ...
#
#         # когда всё закончено (если нужно вручную управлять — дождитесь последнего yield)
#         # запускаем следующий URL из списка
#         # index = response.meta['url_index']
#         # if index + 1 < len(self.start_urls):
#         #     next_url = self.start_urls[index + 1]
#         #     yield scrapy.Request(
#         #         url=next_url,
#         #         callback=self.parse_with_queue,
#         #         meta={'url_index': index + 1}
#         #     )
#     def is_new_sheriff_num(self, sheriff_num):
#         return sheriff_num not in self.saved_nums
#
#     # def parse_with_queue(self, response):
#     def parse(self, response):
#         # cookie_header = ''
#         # if b'Set-Cookie' in response.headers:
#         #     cookies = response.headers.getlist(b'Set-Cookie')
#         #     cookie_parts = [c.decode().split(';')[0] for c in cookies]
#         #     cookie_header = '; '.join(cookie_parts)
#         # AWSALB = cookie_header.split('AWSALB=')[1].split('; ')[0]
#         # ASP = cookie_header.split('ASP.NET_SessionId=')[1].split('; ')[0]
#         # AWSALBCORS = cookie_header.split('AWSALBCORS=')[1].split('; ')[0]
#         #     # print(AWSALB, ASP, AWSALBCORS)
#         headers = {
#                 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#                 'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
#                 'cache-control': 'no-cache',
#                 'pragma': 'no-cache',
#                 'priority': 'u=0, i',
#                 # 'referer': 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
#                 'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
#                 'sec-ch-ua-mobile': '?0',
#                 'sec-ch-ua-platform': '"Windows"',
#                 'sec-fetch-dest': 'document',
#                 'sec-fetch-mode': 'navigate',
#                 'sec-fetch-site': 'same-origin',
#                 'sec-fetch-user': '?1',
#                 'upgrade-insecure-requests': '1',
#                 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
#                 # 'Cookie': f'cookie_header'
#                 # 'Cookie': 'ASP.NET_SessionId=3exjiebvaqegxndh0zlegkfm; AWSALBCORS=wUygVR/ACf82cfkUECLXzJtWLKKFVRfAFf5koMUcMmnIlOsSXsTzqIhw5lpf6nFu2+EMHMJnWNYkvlQKI3MU7pOu5e+/jM2TpaHozq/wkNJ93gG1l+9yr52Na/SI; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=0yHZTu0Mrk5xi9zArrwX0ebb5NL043DhWWBgL9DA2GyYFxHBqF7OU5nYbfP9/Y44tCiEkcRqF20CmdOygxbtfEFhr3KTq2YTRxb1g3SCr9erdu4UzU9PJeHjxZ3w; AWSALBCORS=0yHZTu0Mrk5xi9zArrwX0ebb5NL043DhWWBgL9DA2GyYFxHBqF7OU5nYbfP9/Y44tCiEkcRqF20CmdOygxbtfEFhr3KTq2YTRxb1g3SCr9erdu4UzU9PJeHjxZ3w'
#                 # 'Cookie': 'ASP.NET_SessionId=dq0ggiqk1ik4cyuiiyf0n5do; AWSALB=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; AWSALBCORS=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; AWSALBCORS=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y',
#                 # 'Cookie': f'ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}; ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}'
#                 # 'Cookie': f'AWSALB={AWSALB}; AWSALBCORS={}; ASP.NET_SessionId=3juy4hmu5bptnm3xfhkzthh0'
#             }
#         part_url_lst = response.xpath('//table[@class="table table-striped "]/tr')
#         county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
#         for part_url in part_url_lst:
#             url = response.urljoin(part_url.xpath(".//a/@href").get())
#             sheriff_num = part_url.xpath('./td[2]/text()').get().strip()
#             if sheriff_num and self.is_new_sheriff_num(sheriff_num):
#             # self.logger.info(f"New: {sheriff_num} — {each_url}")
#                 r = scrapy.Request(
#                     url,
#                     headers=headers,
#                     callback=self.parse_article_enc,
#                     meta={
#                             'County': county,
#                             'SheriffNum': sheriff_num
#                     }
#                 )
#                 yield r
#
#         # if self.start_urls_queue:
#         #     next_url = self.start_urls_queue.pop(0)
#         #     yield scrapy.Request(next_url, callback=self.parse)
#
#         # index = response.meta['url_index']
#         # if index + 1 < len(self.start_urls):
#         #     next_url = self.start_urls[index + 1]
#         #     yield scrapy.Request(
#         #         url=next_url,
#         #         callback=self.parse_with_queue,
#         #         meta={'url_index': index + 1}
#         #     )
#
#     def extract_with_xpath(self, response, *xpaths):
#         for xpath in xpaths:
#             data = response.xpath(f'normalize-space({xpath})').get()
#             if data:
#                 return data.strip()
#         return None
#
#     def clean_text(self, text):
#         if text:
#             return text.replace('ET AL.', '').replace('ET. ALS.', '').replace('ET ALS.', '').strip()
#         return text
#
#     def parse_article_enc(self, response):
#         # if response.status == 302 or "SalesDetails" in response.url:
#         #     self.redirect_302_count += 1
#         #     self.logger.warning(f"302 redirect detected ({self.redirect_302_count}/3): {response.url}")
#         #
#         #     if self.redirect_302_count >= 3:
#         #         self.logger.warning("Got 3 consecutive 302s, sleeping for 240s and refreshing cookies...")
#         #         time.sleep(240)
#         #         self.redirect_302_count = 0
#         #         # Возврат к главной для получения свежих cookies
#         #         yield scrapy.Request(
#         #             url="https://salesweb.civilview.com/",
#         #             callback=self.parse,
#         #             dont_filter=True
#         #         )
#         #
#         #     # просто пропустить текущий 302
#         #     return
#         #
#         self.redirect_302_count = 0  # сброс, если всё ок
#
#         if response.status == 302:
#             index_page = response.meta['url_index']
#             url = self.start_urls[index_page]
#             yield Request(
#                 url=url,
#                 callback=self.parse,
#                 dont_filter=True
#             )
#         try:
#             sales_date = self.extract_with_xpath(response,'//div[contains(text(), "Sales Date")]/following-sibling::div',
#                                     '//div[contains(text(), "Sale Date")]/following-sibling::div') or None
#         except:
#             sales_date = ''
#         if sales_date:
#             data= {
#                     'Country': response.meta['County'],
#                     'Sheriff #': response.meta['SheriffNum'],
#                     'Sales Date': sales_date,
#                     'Defendant': self.clean_text(self.extract_with_xpath(response,
#                                                          '//div[contains(text(), "Defendant")]/following-sibling::div')) or None,
#
#                     'Address': self.extract_with_xpath(response,
#                                                        '//div[contains(text(), "Address")]/following-sibling::div') or None,
#                     'Description': self.extract_with_xpath(response,
#                                                            '//div[contains(text(), "Description")]/following-sibling::div//text()') or None,
#                     'Approx. Upset*': self.extract_with_xpath(response,
#                                                               '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()') or None,
#                     'Approx. Judgment*': self.extract_with_xpath(response, '//div[contains(text(), "Judgment")]/following-sibling::div//text()') or None,
#                     'Good Faith Upset': self.extract_with_xpath(response,'//div[contains(text(), "Good Faith Upset*")]/following-sibling::div//text()') or None,
#                     'URL': response.url
#                 }
#             with open ('04_05_25.csv', 'a', newline='', encoding='UTF-8') as f:
#                 w = csv.DictWriter(f, data.keys())
#                 if f.tell() == 0:
#                     w.writeheader()
#                 w.writerow(data)
#             important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
#             if all(data[k] for k in important_keys):
#                 sheriff_num = data['Sheriff #']
#                 with open(self.sheriff_file, 'a', encoding='utf-8') as f:
#                     f.write(sheriff_num + '\n')
#                     self.saved_nums.add(sheriff_num)
#                     yield data







    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.sheriff_file = 'sheriff_nums.txt'
    #     if not os.path.exists(self.sheriff_file):
    #         open(self.sheriff_file, 'w').close()
    #     with open(self.sheriff_file, 'r', encoding='utf-8') as f:
    #         self.saved_nums = set(line.strip() for line in f if line.strip())
    # def is_new_sheriff_num(self, sheriff_num):
    #     return sheriff_num not in self.saved_nums
    #
    # # def parse(self, response):
    #     cookie_header = ''
    #     # if b'Set-Cookie' in response.headers:
    #     #     cookies = response.headers.getlist(b'Set-Cookie')
    #     #     cookie_parts = [c.decode().split(';')[0] for c in cookies]
    #     #     cookie_header = '; '.join(cookie_parts)
    # # def start_requests(self) -> Iterable[Request]:
    # #     headers = {
    # #         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    # #         'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    # #         'cache-control': 'no-cache',
    # #         'pragma': 'no-cache',
    # #         'priority': 'u=0, i',
    # #        # 'referer': 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
    # #         'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    # #         'sec-ch-ua-mobile': '?0',
    # #         'sec-ch-ua-platform': '"Windows"',
    # #         'sec-fetch-dest': 'document',
    # #         'sec-fetch-mode': 'navigate',
    # #         'sec-fetch-site': 'none',
    # #         'sec-fetch-user': '?1',
    # #         'upgrade-insecure-requests': '1',
    # #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    # #         # 'Cookie': cookie_header#'ASP.NET_SessionId=3exjiebvaqegxndh0zlegkfm; AWSALB=bBPhI+f8hDMMtUiQPumPURk6FS8lrZroZz9juv19qLxq5OU5Il0IoNIMCZF/bVq0qZVqQU14tmg4QRTab7NOjEZ4FjxzVdagfY1Yddm01EZlYDIhhFVjX14mKmcy; AWSALBCORS=bBPhI+f8hDMMtUiQPumPURk6FS8lrZroZz9juv19qLxq5OU5Il0IoNIMCZF/bVq0qZVqQU14tmg4QRTab7NOjEZ4FjxzVdagfY1Yddm01EZlYDIhhFVjX14mKmcy; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=WtCIY1/yPV82AEJ2lBwck1MQaxZdSvDBogxJbIQNHosZuBxwNBkv+WZmkeBNeagb0aUhbx+p0L+a6QSdCYhpZgD/U1AE7jW+Toll/eBXrSPq2nnrTEyMJpA6QV5j; AWSALBCORS=WtCIY1/yPV82AEJ2lBwck1MQaxZdSvDBogxJbIQNHosZuBxwNBkv+WZmkeBNeagb0aUhbx+p0L+a6QSdCYhpZgD/U1AE7jW+Toll/eBXrSPq2nnrTEyMJpA6QV5j'
    # #     }
    #     # url = "https://salesweb.civilview.com/Sales/SalesSearch?countyId=73" #73
    #     # urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',#,
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
    #     #         'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17'
    #     #     ]
    #     # for url in urls:
    #         # time.sl   eep(random.randrange(12))
    #     # yield scrapy.Request(
    #     # url=url,
    #     # callback=self.parse1,
    #     # # headers=headers,
    #     # # dont_filter=True,
    #     # meta={'handle_redirects': False}
    #     # )
    #     # r = requests.get(url=url, headers=headers)
    #     # from scrapy.selector import Selector
    #     # body = r.text
    #     # response = Selector(text=body)
    #
    # def parse(self, response):
    #     # cookie_header = ''
    #     # if b'Set-Cookie' in response.headers:
    #     #     cookies = response.headers.getlist(b'Set-Cookie')
    #     #     cookie_parts = [c.decode().split(';')[0] for c in cookies]
    #     #     cookie_header = '; '.join(cookie_parts)
    #     # AWSALB = cookie_header.split('AWSALB=')[1].split('; ')[0]
    #     # ASP = cookie_header.split('ASP.NET_SessionId=')[1].split('; ')[0]
    #     # AWSALBCORS = cookie_header.split('AWSALBCORS=')[1].split('; ')[0]
    #     # print(AWSALB, ASP, AWSALBCORS)
    #     headers = {
    #         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #         'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    #         'cache-control': 'no-cache',
    #         'pragma': 'no-cache',
    #         'priority': 'u=0, i',
    #         'referer': 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
    #         'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    #         'sec-ch-ua-mobile': '?0',
    #         'sec-ch-ua-platform': '"Windows"',
    #         'sec-fetch-dest': 'document',
    #         'sec-fetch-mode': 'navigate',
    #         'sec-fetch-site': 'same-origin',
    #         'sec-fetch-user': '?1',
    #         'upgrade-insecure-requests': '1',
    #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    #         # 'Cookie': f'cookie_header'
    #         # ''Cookie': 'ASP.NET_SessionId=3exjiebvaqegxndh0zlegkfm; AWSALBCORS=wUygVR/ACf82cfkUECLXzJtWLKKFVRfAFf5koMUcMmnIlOsSXsTzqIhw5lpf6nFu2+EMHMJnWNYkvlQKI3MU7pOu5e+/jM2TpaHozq/wkNJ93gG1l+9yr52Na/SI; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=0yHZTu0Mrk5xi9zArrwX0ebb5NL043DhWWBgL9DA2GyYFxHBqF7OU5nYbfP9/Y44tCiEkcRqF20CmdOygxbtfEFhr3KTq2YTRxb1g3SCr9erdu4UzU9PJeHjxZ3w; AWSALBCORS=0yHZTu0Mrk5xi9zArrwX0ebb5NL043DhWWBgL9DA2GyYFxHBqF7OU5nYbfP9/Y44tCiEkcRqF20CmdOygxbtfEFhr3KTq2YTRxb1g3SCr9erdu4UzU9PJeHjxZ3w'
    #         'Cookie': 'ASP.NET_SessionId=dq0ggiqk1ik4cyuiiyf0n5do; AWSALB=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; AWSALBCORS=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y; AWSALBCORS=qqVK7Rx/3fncBtZ3jMATelK9zwiPsep5hG7RLLz7bk/ILLRSZAmA7rulJtv5wzxdn0OdgX/UZlIaI+NyHPpDeg027K3nVmRpeo6iKpA6DIu/1FFR/DzmftsgRN+Y',
    #         # 'Cookie': f'ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS};'# ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}'
    #         # 'Cookie': f'AWSALB={AWSALB}; AWSALBCORS={}; ASP.NET_SessionId=3juy4hmu5bptnm3xfhkzthh0'
    #     }
    #     # one = "'Cookie': f'ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}; ASP.NET_SessionId={ASP}; AWSALB={AWSALB}; AWSALBCORS={AWSALBCORS}'"
    #     # print(one)
    #     # print(headers)
    #     all_urls = response.xpath('//table[@class="table table-striped "]/tr')
    #     county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
    #     for i in all_urls:
    #         each_url = 'https://salesweb.civilview.com'+ i.xpath(".//a/@href").get() #'https://salesweb.civilview.com' + i.xpath(".//a/@href").get()
    #
    #     # each_url = 'https://salesweb.civilview.com/Sales/SaleDetails?PropertyId=1565662845'
    #         sheriff_num = i.xpath('./td[2]/text()').get().strip()
    #         if sheriff_num and self.is_new_sheriff_num(sheriff_num):
    #             self.logger.info(f"New: {sheriff_num} — {each_url}")
    #             # time.sleep(random.randrange(13))
    #             # print(response.headers)
    #             yield scrapy.Request(#response.follow(
    #                 url=each_url,
    #                 # headers=headers,
    #                 meta={
    #                     'County': county,
    #                     'SheriffNum': sheriff_num,
    #                     # 'handle_redirects': False,
    #                     # 'handle_httpstatus_list': [302]
    #                 },
    #                 callback=self.parse_items
    #             )
    #         else:
    #             self.logger.info(f"Skipped (exists): {sheriff_num}")
    #
    # def extract_with_xpath(self, response, *xpaths):
    #     for xpath in xpaths:
    #         data = response.xpath(f'normalize-space({xpath})').get()
    #         if data:
    #             return data.strip()
    #     return None
    #
    # def parse_items(self, response):
    #     # def parse_items(self, response):
    #     # if response.status == 302:
    #     #     location = response.headers.get('Location', b'').decode()
    #     #     self.logger.warning(f"Redirected to: {location}")
    #     #     return
    #     # time.sleep(random.randrange(13))
    #     sheriff_num = response.meta['SheriffNum']
    #     data = {
    #         'Country': response.meta['County'],
    #         'Sheriff #': sheriff_num,
    #         'Sales Date': self.extract_with_xpath(response,
    #                                               '//div[contains(text(), "Sales Date")]/following-sibling::div'),
    #         'Defendant': self.extract_with_xpath(response,
    #                                              '//div[contains(text(), "Defendant")]/following-sibling::div'),
    #         'Address': self.extract_with_xpath(response,
    #                                            '//div[contains(text(), "Address")]/following-sibling::div'),
    #         'Description': self.extract_with_xpath(response,
    #                                                '//div[contains(text(), "Description")]/following-sibling::div//text()'),
    #         'Approx. Upset*': self.extract_with_xpath(response,
    #                                                   '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()'),
    #         'URL': response.url
    #     }
    #
    #     important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
    #     if all(data[k] for k in important_keys):
    #         sheriff_num = data['Sheriff #']
    #         with open(self.sheriff_file, 'a', encoding='utf-8') as f:
    #             f.write(sheriff_num + '\n')
    #             self.saved_nums.add(sheriff_num)
    #             yield data
    #     # else:
    #     #     retry_count = response.meta.get('retry_count', 0)
    #     #     if retry_count < 5:
    #     #         time.sleep(2)
    #     #         self.logger.warning(f"Retrying ({retry_count + 1}) for {response.url}")
    #     #         yield response.follow(
    #     #             response.url,
    #     #             callback=self.parse_items,
    #     #             meta={
    #     #                 'County': response.meta['County'],
    #     #                 'SheriffNum': sheriff_num,
    #     #                 'handle_redirects': False,
    #     #                 'handle_httpstatus_list': [302],
    #     #                 'retry_count': retry_count + 1
    #     #             },
    #     #             dont_filter=True
    #     #         )
    #     #     else:
    #     #         self.logger.error(f"Failed to extract full data for: {sheriff_num}")
    #

















        # if response.status == 302:
        #     location = response.headers.get('Location', b'').decode()
        #     self.logger.warning(f"Redirected to: {location}")
        #     return
        # time.sleep(random.randrange(13))
        # sheriff_num = response.meta['SheriffNum']
        # data = {
        #     'Country': response.meta['County'],
        #     'Sheriff #': sheriff_num,
        #     'Sales Date': self.extract_with_xpath(response,
        #                                           '//div[contains(text(), "Sales Date")]/following-sibling::div'),
        #     'Defendant': self.extract_with_xpath(response,
        #                                          '//div[contains(text(), "Defendant")]/following-sibling::div'),
        #     'Address': self.extract_with_xpath(response, '//div[contains(text(), "Address")]/following-sibling::div'),
        #     'Description': self.extract_with_xpath(response,
        #                                            '//div[contains(text(), "Description")]/following-sibling::div//text()'),
        #     'Approx. Upset*': self.extract_with_xpath(response,
        #                                               '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()'),
        #     'URL': response.url
        # }
        #
        # important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
        # if all(data[k] for k in important_keys):
        #     sheriff_num = data['Sheriff #']
        #     with open(self.sheriff_file, 'a', encoding='utf-8') as f:
        #         f.write(sheriff_num + '\n')
        #         self.saved_nums.add(sheriff_num)
        #         yield data
        # else:
        #     retry_count = response.meta.get('retry_count', 0)
        #     if retry_count < 3:
        #         self.logger.info("Refreshing cookies due to 302...")
        #         yield scrapy.Request(
        #             url=self.start_urls[0],
        #             # callback=self.retry_after_refresh,
        #             meta={
        #                 'original_url': response.url,
        #                 'County': response.meta['County'],
        #                 'SheriffNum': response.meta['SheriffNum'],
        #                 'retry_count': retry_count + 1,
        #             },
        #             dont_filter=True,
        #             # handle_httpstatus_list=[200]
        #         )


            # if retry_count < 5:
            #     time.sleep(2)
            #     self.logger.warning(f"Retrying ({retry_count + 1}) for {response.url}")
            #     yield response.follow(
            #         response.url,
            #         callback=self.parse_items,
            #         meta={
            #             'County': response.meta['County'],
            #             'SheriffNum': sheriff_num,
            #             'handle_redirects': False,
            #             'handle_httpstatus_list': [302],
            #             'retry_count': retry_count + 1
            #         },
            #         dont_filter=True
            #     )
            # else:
            #     self.logger.error(f"Failed to extract full data for: {sheriff_num}")


        # def parse_items(self, response):
        # if response.status == 302:
        #     location = response.headers.get('Location', b'').decode()
        #     self.logger.warning(f"Redirected (302) to: {location}")
        #     retry_count = response.meta.get('retry_count', 0)
        #     if retry_count < 3:
        #         self.logger.info("Refreshing cookies due to 302...")
        #         yield scrapy.Request(
        #             url=self.start_urls[0],
        #             callback=self.retry_after_refresh,
        #             meta={
        #                 'original_url': response.url,
        #                 'County': response.meta['County'],
        #                 'SheriffNum': response.meta['SheriffNum'],
        #                 'retry_count': retry_count + 1,
        #             },
        #             dont_filter=True,
        #             handle_httpstatus_list=[200]
        #         )
        #     else:
        #         self.logger.error(f"Too many redirects for: {response.meta['SheriffNum']}")
        #     return
        #
        # sheriff_num = response.meta['SheriffNum']
        # data = {
        #     'Country': response.meta['County'],
        #     'Sheriff #': sheriff_num,
        #     'Sales Date': self.extract_with_xpath(response,
        #                                           '//div[contains(text(), "Sales Date")]/following-sibling::div'),
        #     'Defendant': self.extract_with_xpath(response,
        #                                          '//div[contains(text(), "Defendant")]/following-sibling::div'),
        #     'Address': self.extract_with_xpath(response,
        #                                        '//div[contains(text(), "Address")]/following-sibling::div'),
        #     'Description': self.extract_with_xpath(response,
        #                                            '//div[contains(text(), "Description")]/following-sibling::div//text()'),
        #     'Approx. Upset*': self.extract_with_xpath(response,
        #                                               '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()'),
        #     'URL': response.url
        # }
        #
        # important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
        # if all(data[k] for k in important_keys):
        #     sheriff_num = data['Sheriff #']
        #     with open(self.sheriff_file, 'a', encoding='utf-8') as f:
        #         f.write(sheriff_num + '\n')
        #         self.saved_nums.add(sheriff_num)
        #     yield data
        # else:
        #     retry_count = response.meta.get('retry_count', 0)
        #     if retry_count < 5:
        #         time.sleep(2)
        #         self.logger.warning(f"Retrying ({retry_count + 1}) for {response.url}")
        #         yield response.follow(
        #             response.url,
        #             callback=self.parse_items,
        #             meta={
        #                 'County': response.meta['County'],
        #                 'SheriffNum': sheriff_num,
        #                 'handle_redirects': False,
        #                 'handle_httpstatus_list': [302],
        #                 'retry_count': retry_count + 1
        #             },
        #             dont_filter=True
        #         )
        #     else:
        #         self.logger.error(f"Failed to extract full data for: {sheriff_num}")

        # if response.status == 302:
        #     location = response.headers.get('Location', b'').decode()
        #     self.logger.warning(f"Redirected to: {location}")
        #     return
        # time.sleep(random.randrange(13))
        # sheriff_num = response.meta['SheriffNum']
        # data = {
        #     'Country': response.meta['County'],
        #     'Sheriff #': sheriff_num,
        #     'Sales Date': self.extract_with_xpath(response,
        #                                           '//div[contains(text(), "Sales Date")]/following-sibling::div'),
        #     'Defendant': self.extract_with_xpath(response,
        #                                          '//div[contains(text(), "Defendant")]/following-sibling::div'),
        #     'Address': self.extract_with_xpath(response, '//div[contains(text(), "Address")]/following-sibling::div'),
        #     'Description': self.extract_with_xpath(response,
        #                                            '//div[contains(text(), "Description")]/following-sibling::div//text()'),
        #     'Approx. Upset*': self.extract_with_xpath(response,
        #                                               '//div[contains(text(), "Approx. Upset*")]/following-sibling::div//text()'),
        #     'URL': response.url
        # }
        #
        # important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address']
        # if all(data[k] for k in important_keys):
        #     sheriff_num = data['Sheriff #']
        #     with open(self.sheriff_file, 'a', encoding='utf-8') as f:
        #         f.write(sheriff_num + '\n')
        #         self.saved_nums.add(sheriff_num)
        #         yield data
        # else:
        #     retry_count = response.meta.get('retry_count', 0)
        #     if retry_count < 3:
        #         self.logger.info("Refreshing cookies due to 302...")
        #         yield scrapy.Request(
        #             url=self.start_urls[0],
        #             callback=self.retry_after_refresh,
        #             meta={
        #                 'original_url': response.url,
        #                 'County': response.meta['County'],
        #                 'SheriffNum': response.meta['SheriffNum'],
        #                 'retry_count': retry_count + 1,
        #             },
        #             dont_filter=True,
        #             handle_httpstatus_list=[200]
        #         )
        #     # if retry_count < 5:
        #     #     time.sleep(2)
        #     #     self.logger.warning(f"Retrying ({retry_count + 1}) for {response.url}")
        #     #     yield response.follow(
        #     #         response.url,
        #     #         callback=self.parse_items,
        #     #         meta={
        #     #             'County': response.meta['County'],
        #     #             'SheriffNum': sheriff_num,
        #     #             'handle_redirects': False,
        #     #             'handle_httpstatus_list': [302],
        #     #             'retry_count': retry_count + 1
        #     #         },
        #     #         dont_filter=True
        #     #     )
        #     else:
        #         self.logger.error(f"Failed to extract full data for: {sheriff_num}")






    # # allowed_domains = ["dgh.com"]
    #
    # custom_settings = {
    #     'DOWNLOADER_MIDDLEWARES': {
    #         'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None
    #     }
    # }
    #
    # def start_requests(self) -> Iterable[Request]:
    #     url = "https://salesweb.civilview.com/Sales/SalesSearch?countyId=2"
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
    #         # 'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17',
    #     # ]
    #     #https://salesweb.civilview.com/Sales/SaleDetails?PropertyId=1565463655
    #     # for url in urls:
    #         # time.sleep(20)
    #     yield scrapy.Request(
    #         url=url,
    #         callback=self.parse,
    #         dont_filter=True,
    #         # 'handle_httpstatus_list': [302]
    #         meta={'handle_redirects': False}  # отключение обработки 302
    #     )
    #
    # def check_and_save_sheriff_num(self, sheriff_num):
    #     filename = 'sheriff_nums.txt'
    #     if not os.path.exists(filename):
    #         open(filename, 'w').close()
    #
    #     with open(filename, 'r', encoding='utf-8') as f:
    #         saved_nums = set(line.strip() for line in f)
    #
    #     if sheriff_num not in saved_nums:
    #         # with open(filename, 'a', encoding='utf-8') as f:
    #     #         f.write(sheriff_num + '\n')
    #         return True
    #     else:
    #         return False
    #
    # def parse(self, response):
    #
    #     cookie_header = ''
    #     if b'Set-Cookie' in response.headers:
    #         cookies = response.headers.getlist(b'Set-Cookie')
    #         cookie_parts = []
    #         for c in cookies:
    #             # Разделяем по ';' и берём первую часть (cookie-пара)
    #             cookie_str = c.decode().split(';')[0]
    #             cookie_parts.append(cookie_str)
    #         cookie_header = '; '.join(cookie_parts)
    #     # print(cookie_header)
    #     headers = {
    #         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #         'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    #         'cache-control': 'no-cache',
    #         'pragma': 'no-cache',
    #         'priority': 'u=0, i',
    #         'referer': 'https://salesweb.civilview.com/Home/Index?aspxerrorpath=/Sales/SaleDetails',
    #         'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    #         'sec-ch-ua-mobile': '?0',
    #         'sec-ch-ua-platform': '"Windows"',
    #         'sec-fetch-dest': 'document',
    #         'sec-fetch-mode': 'navigate',
    #         'sec-fetch-site': 'same-origin',
    #         'sec-fetch-user': '?1',
    #         'upgrade-insecure-requests': '1',
    #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    #         'Cookie': cookie_header
    #         # 'Cookie': 'ASP.NET_SessionId=3exjiebvaqegxndh0zlegkfm; AWSALB=vrjdihJupgBGiIl8J62q9nCMAgXNVMvo5H30AEdr5r9tPIrKhRx3BCQdLe4aOLja679KsC+L5wxNNc8cWfbDC6O1xjJmPZq/kwgYQ9CjpA8DPZjR+ICTeJ2hHjJY; AWSALBCORS=vrjdihJupgBGiIl8J62q9nCMAgXNVMvo5H30AEdr5r9tPIrKhRx3BCQdLe4aOLja679KsC+L5wxNNc8cWfbDC6O1xjJmPZq/kwgYQ9CjpA8DPZjR+ICTeJ2hHjJY; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=KnsQHB5rn99zBsJqY0QQNaDC56yRWisfPVw+EbJBrqJzeBtUP80CebkzYXRm2vgoeQFeUvO/xW4b7YZsAHJiRQXDR5ZQcqZ1KIrBnplQkdGRoVVOsjW1AKN3C46W; AWSALBCORS=KnsQHB5rn99zBsJqY0QQNaDC56yRWisfPVw+EbJBrqJzeBtUP80CebkzYXRm2vgoeQFeUvO/xW4b7YZsAHJiRQXDR5ZQcqZ1KIrBnplQkdGRoVVOsjW1AKN3C46W'
    #     }
    #     all_urls = response.xpath('//table[@class="table table-striped "]/tr')
    #     county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0]
    #     for i in all_urls:
    #         each_url = response.urljoin(i.xpath(".//a/@href").get())
    #         sheriff_num = i.xpath('./td[2]/text()').get().strip()
    #         if sheriff_num:
    #             if self.check_and_save_sheriff_num(sheriff_num):
    #                 print(f"New: {sheriff_num} — {each_url}")
    #                 yield response.follow(
    #                     each_url,
    #                     headers=headers,
    #                     meta={
    #                         'County': county,
    #                         'handle_redirects': False,
    #                         'handle_httpstatus_list': [302] # отключаем редиректы и здесь
    #                     },
    #                     callback=self.parse_items
    #                 )
    #             else:
    #                 print(f"Passed (already exists): {sheriff_num}")
    #
    # def extract_with_xpath(self, response, *xpaths):
    #     for xpath in xpaths:
    #         data = response.xpath(f'normalize-space({xpath})').get()
    #         if data:
    #             return data.strip()
    #     return None
    #
    # def parse_items(self, response):
    #     if response.status == 302:
    #         location = response.headers.get('Location', b'').decode()
    #         self.logger.warning(f"Redirected to: {location}")
    #         return
    #     data = {
    #         'Country': response.meta['County'],
    #         'Sheriff #': self.extract_with_xpath(response,
    #                                              '//div[@class="sale-details-list"]/div/div[contains(text(), "Sheriff #")]/following-sibling::div[@class="sale-detail-value"]'),
    #         'Sales Date': self.extract_with_xpath(response,
    #                                               '//div[@class="sale-details-list"]/div/div[contains(text(), "Sales Date")]/following-sibling::div[@class="sale-detail-value"]'),
    #         'Defendant': self.extract_with_xpath(response,
    #                                              '//div[@class="sale-details-list"]/div/div[contains(text(), "Defendant")]/following-sibling::div[@class="sale-detail-value"]/text()'),
    #         'Address': self.extract_with_xpath(response,
    #                                            '//div[@class="sale-details-list"]/div/div[contains(text(), "Address")]/following-sibling::div[@class="sale-detail-value"]'),
    #         'Description': self.extract_with_xpath(response,
    #                                                '//div[@class="sale-details-list"]/div/div[contains(text(), "Description")]/following-sibling::div[@class="sale-detail-value"]//text()'),
    #         'Approx. Upset*': self.extract_with_xpath(response,
    #                                                   '//div[@class="sale-details-list"]/div/div[contains(text(), "Approx. Upset*")]/following-sibling::div[@class="sale-detail-value"]//text()'),
    #         'URL': response.url
    #     }
    #
    #     # Проверка на наличие всех ключевых полей
    #     important_keys = ['Sheriff #', 'Sales Date', 'Defendant', 'Address'] #, 'Description', 'Approx. Upset*
    #     if all(data[key] is not None for key in important_keys):
    #         # Запись в TXT
    #         with open('sheriff_nums.txt', 'a', encoding='utf-8') as f:
    #             line =  '\t'.join([f"{k}: {v}" for k, v in data.items()])
    #             f.write(line + '\n')
    #         yield data
    #     else:
    #         # Повторный запрос при неполных данных
    #         retry_count = response.meta.get('retry_count', 0)
    #         if retry_count < 5:
    #             self.logger.warning(f"Partial/empty data, retrying ({retry_count + 1}) for {response.url}")
    #             yield response.follow(
    #                 response.url,
    #                 callback=self.parse_items,
    #                 meta={
    #                     'County': response.meta['County'],
    #                     'handle_redirects': False,
    #                     'handle_httpstatus_list': [302],
    #                     'retry_count': retry_count + 1
    #                 },
    #                 dont_filter=True
    #             )
    #         else:
    #             self.logger.error(f"Max retries reached for {response.url}")

    # def parse_items(self, response):
    #     if response.status == 302:
    #         location = response.headers.get('Location', b'').decode()
    #         self.logger.warning(f"Redirected to: {location}")
    #         return
    #     data =  {
    #         'Country': response.meta['County'],
    #         'Sheriff #': self.extract_with_xpath(response, '//div[@class="sale-details-list"]/div/div[contains(text(), "Sheriff #")]/following-sibling::div[@class="sale-detail-value"]'),
    #         'Sales Date': self.extract_with_xpath(response, '//div[@class="sale-details-list"]/div/div[contains(text(), "Sales Date")]/following-sibling::div[@class="sale-detail-value"]'),
    #         'Defendant': self.extract_with_xpath(response, '//div[@class="sale-details-list"]/div/div[contains(text(), "Defendant")]/following-sibling::div[@class="sale-detail-value"]/text()'),
    #         'Address': self.extract_with_xpath(response, '//div[@class="sale-details-list"]/div/div[contains(text(), "Address")]/following-sibling::div[@class="sale-detail-value"]'),
    #         'Description': self.extract_with_xpath(response, '//div[@class="sale-details-list"]/div/div[contains(text(), "Description")]/following-sibling::div[@class="sale-detail-value"]//text()'),
    #         'Approx. Upset*': self.extract_with_xpath(response, '//div[@class="sale-details-list"]/div/div[contains(text(), "Approx. Upset*")]/following-sibling::div[@class="sale-detail-value"]//text()'),
    #         'URL': response.url
    #     }
    #     if all(v is None for k, v in data.items() if k not in ['Country', 'URL']):
    #         retry_count = response.meta.get('retry_count', 0)
    #         if retry_count < 3:
    #             self.logger.warning(f"Empty data, retrying ({retry_count + 1}) for {response.url}")
    #             yield response.follow(
    #                 response.url,
    #                 callback=self.parse_items,
    #                 meta={
    #                     'County': response.meta['County'],
    #                     'handle_redirects': False,
    #                     'handle_httpstatus_list': [302],
    #                     'retry_count': retry_count + 1
    #                 },
    #                 dont_filter=True  # разрешает повторные запросы к тому же URL
    #             )
    #         else:
    #             self.logger.error(f"Max retries reached for {response.url}")
    #     else:
    #         yield data

    # def start_requests(self) -> Iterable[Request]:
    #     urls = ["https://salesweb.civilview.com/Sales/SalesSearch?countyId=2",
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=10',
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=7',
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=15',
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=73',
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=8',
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=9',
    #             'https://salesweb.civilview.com/Sales/SalesSearch?countyId=17',
    #             ]
    #     for i in urls:
    #
    #
    #
    # def check_and_save_sheriff_num(self, sheriff_num):
    #     filename = 'sheriff_nums.txt'
    #     if not os.path.exists(filename):
    #         open(filename, 'w').close()
    #
    #     with open(filename, 'r', encoding='utf-8') as f:
    #         saved_nums = set(line.strip() for line in f)
    #
    #     if sheriff_num not in saved_nums:
    #         with open(filename, 'a', encoding='utf-8') as f:
    #             f.write(sheriff_num + '\n')
    #         return True
    #     else:
    #         return False
    #
    # def parse(self, response):
    #     all_urls = response.xpath('//table[@class="table table-striped "]/tr')#[0:1]
    #     county = response.xpath('//main[@class="search-container"]/table/tr/th/h1/text()').get().split(',')[0] #<main class="search-container">
    #     for i in all_urls:
    #         each_url = response.urljoin(i.xpath(".//a/@href").get())
    #         sheriff_num = i.xpath('./td[2]/text()').get().strip(' ')
    #         if sheriff_num:
    #             # sheriff_num = sheriff_num.strip()
    #             if self.check_and_save_sheriff_num(sheriff_num):
    #                 print(f"New: {sheriff_num} — {each_url}")
    #             # each_url = 'https://salesweb.civilview.com/Sales/SaleDetails?PropertyId=1565421567'
    #                 yield response.follow(each_url, meta={'County': county},callback=self.parse_items)
    #             else:
    #                 print(f"Passed (already exists): {sheriff_num}")
    # #
    # def extract_with_xpath(self, response, *xpaths):
    #     for xpath in xpaths:
    #         data = response.xpath(f'normalize-space({xpath})').get()
    #         if data:
    #             return data.strip()
    #         return None
    #
    # def parse_items(self, response):
    #     # print(response.text)
    #     yield {
    #         'Country':  response.meta['County'],
    #         'Sheriff #': self.extract_with_xpath(response,'//div[@class="sale-details-list"]/div/div[contains'
    #                                                       '(text(), "Sheriff #")]/following-sibling::div[@class="sale-detail-value"]') or None,
    #         'Sales Date': self.extract_with_xpath(response,'//div[@class="sale-details-list"]/div/div[contains('
    #                                                        'text(), "Sales Date")]/following-sibling::div[@class="sale-detail-value"]') or None,
    #         'Defendant':self.extract_with_xpath(response,'//div[@class="sale-details-list"]/div/div[contains('
    #                                                      'text(), "Defendant")]/following-sibling::div[@class="sale-detail-value"]/text()') or None,
    #         'Address': self.extract_with_xpath(response,'//div[@class="sale-details-list"]/div/div[contains('
    #                                                     'text(), "Address")]/following-sibling::div[@class="sale-detail-value"]') or None,
    #         'Description': self.extract_with_xpath(response,'//div[@class="sale-details-list"]/div/div[contains('
    #                                                         'text(), "Description")]/following-sibling::div[@class="sale-detail-value"]//text()') or None,
    #         'Approx. Upset*': self.extract_with_xpath(response,'//div[@class="sale-details-list"]/div/div['
    #                                                            'contains(text(), "Approx. Upset*")]/following-sibling::div[@class="sale-detail-value"]//text()') or None,
    #         'URL': response.url
    #     }
