# Scrapy settings for Sales project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "Sales"

SPIDER_MODULES = ["Sales.spiders"]
NEWSPIDER_MODULE = "Sales.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "Sales (+http://www.yourdomain.com)"

# Obey robots.txt rules
# ROBOTSTXT_OBEY = False
# SCRAPEOPS_API_KEY = '2eb4ee1c-3e22-455d-84f0-a81cd0b1c0de'
# SCRAPEOPS_PROXY_ENABLED = True
# # #
# # HTTPERROR_ALLOWED_CODES = [404,403]
# # 'bypass': 'cloudflare_level_1
# DOWNLOADER_MIDDLEWARES = {
#     'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': 725,
# }
# from .spiders.S import SSpider
# from .middlewares import CustomRedirectMiddleware
#
# DOWNLOADER_MIDDLEWARES: {
#     'SSpider.middlewares.CustomRedirectMiddleware': 600,
#     'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
# }

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 1
# HTTPERROR_ALLOWED_CODES = [302]
# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 1
# RANDOMIZED_DOWNLOAD_DELAY =  True
# DOWNLOADER_MIDDLEWARES = {
#     'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
# }
# DOWNLOADER_MIDDLEWARES = {
#     'scrapy_user_agents.middleware.RandomUserAgentMiddleware': 400,
# }
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#     'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
#     'cache-control': 'no-cache',
#     'pragma': 'no-cache',
#     'priority': 'u=0, i',
#     # 'referer': 'https://salesweb.civilview.com/Home/Index?aspxerrorpath=/Sales/SaleDetails',
#     'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'document',
#     'sec-fetch-mode': 'navigate',
#     'sec-fetch-site': 'same-origin',
#     'sec-fetch-user': '?1',
#     'upgrade-insecure-requests': '1',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
#             # 'Cookie': 'ASP.NET_SessionId=3exjiebvaqegxndh0zlegkfm; AWSALB=vrjdihJupgBGiIl8J62q9nCMAgXNVMvo5H30AEdr5r9tPIrKhRx3BCQdLe4aOLja679KsC+L5wxNNc8cWfbDC6O1xjJmPZq/kwgYQ9CjpA8DPZjR+ICTeJ2hHjJY; AWSALBCORS=vrjdihJupgBGiIl8J62q9nCMAgXNVMvo5H30AEdr5r9tPIrKhRx3BCQdLe4aOLja679KsC+L5wxNNc8cWfbDC6O1xjJmPZq/kwgYQ9CjpA8DPZjR+ICTeJ2hHjJY; ASP.NET_SessionId=jx4dedeyboufvi2ooskmhq1e; AWSALB=KnsQHB5rn99zBsJqY0QQNaDC56yRWisfPVw+EbJBrqJzeBtUP80CebkzYXRm2vgoeQFeUvO/xW4b7YZsAHJiRQXDR5ZQcqZ1KIrBnplQkdGRoVVOsjW1AKN3C46W; AWSALBCORS=KnsQHB5rn99zBsJqY0QQNaDC56yRWisfPVw+EbJBrqJzeBtUP80CebkzYXRm2vgoeQFeUvO/xW4b7YZsAHJiRQXDR5ZQcqZ1KIrBnplQkdGRoVVOsjW1AKN3C46W'
#         }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "Sales.middlewares.SalesSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "Sales.middlewares.SalesDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "Sales.pipelines.SalesPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False
DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
