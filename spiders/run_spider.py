#
# from datetime import datetime
# from scrapy.crawler import CrawlerProcess
# from Sales.Sales.spiders.S import SSpider  # Импортируй свой класс
#
# now = datetime.now().strftime('%Y-%m-%d_%H-%M')
# filename = f'results_{now}.csv'
#
# process = CrawlerProcess(settings={
#     'FEEDS': {
#         filename: {
#             'format': 'csv',
#             'encoding': 'utf8',
#             'overwrite': True,
#         }
#     }
# })
#
# process.crawl(SSpider)
# process.start()