import base64
from pprint import pprint
from asyncio import sleep

from scrapy.exporters import JsonItemExporter
import re
from scrapy.spiders import Spider
from scrapy_splash import SplashRequest, SplashResponse

from items import Place

script = """
local treat = require('treat')

function safe_find(splash, selector)
    local element = splash:select(selector)
    if element ~= nil then 
      element = element:text() 
    else
      element = ''
    end
    return element
end

function wait_css(splash, css, maxwait)
    if maxwait == nil then
        maxwait = 100
    else
        maxwait = maxwait * 10
    end

    local i=0
    while not splash:select(css) do
       if i==maxwait then
           error("Unable to find element " .. css)
       end
       i=i+1
       splash:wait(0.1)
    end
    return splash:select(css)
end

function main(splash, args)
    splash.images_enabled = false
    splash:wait(args.wait)
    assert(splash:go(args.url))
    splash:wait(1)
    splash:runjs('document.querySelector("#zV9nZe").click()')
    local href = splash:evaljs('document.querySelector(".Q2MMlc").href')
    splash:wait(1)
    assert(splash:go(href))
    local links = splash:select_all("a[role=link]")
    local results = {}
    local previous_title = ''
  
    for _, link in ipairs(links) do
      link.click()
      local title = wait_css(splash, "h2[data-attrid='title']", 10):text()
      while (previous_title == title) do
        title = splash:select("h2[data-attrid='title']"):text()
        splash:wait(0.1)
      end
      previous_title = title
      local address = safe_find(splash, '.LrzXr')
      local phone = safe_find(splash, "span[data-dtype='d3ifr']")
      local page = splash:evaljs('document.querySelector(".CL9Uqc.ab_button").href')
      local rating = safe_find(splash, '.Aq14fc')
      local reviews = safe_find(splash, '.hqzQac')
      table.insert(results, {title, address, phone, page, rating, reviews})
    end
    return treat.as_array(results)
end
"""


class Spider2(Spider):
    def __init__(self, sleep: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.sleep = sleep

    custom_settings = {
        'SPLASH_URL': 'http://localhost:8050',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 3
    }

    name = "quotes"
    allowed_domains = ['google.com']
    start_urls = ['https://www.google.com/search?q=restauracje+lodz']

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url,
                                callback=self.parse,
                                endpoint='execute',
                                args={'lua_source': script,
                                      'url': url,
                                      'timeout': 90,
                                      'wait': self.sleep})

    def parse(self, response: SplashResponse, **kwargs):
        temp = []
        for place in response.data:
            temp.append(Place(title=place['1'],
                              address=place['2'],
                              phone=place['3'],
                              page=place['4'] if 'google' not in place['4'] else None,
                              rating=place['5'],
                              reviews=re.match(r'^(\d)*', place['6'].replace('\xa0', '')).group()))
        pprint(len(temp))
