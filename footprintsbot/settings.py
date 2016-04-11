# Scrapy settings for footprintsbot project

SPIDER_MODULES = ['footprintsbot.spiders']
NEWSPIDER_MODULE = 'footprintsbot.spiders'
DEFAULT_ITEM_CLASS = 'footprintsbot.items.Issue'

DOWNLOAD_HANDLERS = {'s3': None,}
COOKIES_ENABLED = True
COOKIES_DEBUG = True

#ITEM_PIPELINES = {'footprintsbot.pipelines.FilterWordsPipeline': 1}
