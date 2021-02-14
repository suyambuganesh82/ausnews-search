# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from RISJbot.loaders import NewsLoader
# Note: mutate_selector_del_xpath is somewhat naughty. Read its docstring.
from RISJbot.utils import mutate_selector_del
from scrapy.linkextractors import LinkExtractor
from itemloaders.processors import Identity, TakeFirst
from itemloaders.processors import Join, Compose, MapCompose
from datetime import datetime


class BuzzfeedNewsCrawlSpider(CrawlSpider):
    allowed_domains = ['buzzfeed.com']

    rules = (
        Rule(LinkExtractor(allow=r'^https?://(www\.)?buzzfeed.com/[a-z]+/[-a-z0-9]+$',
                           deny= r'^https?://(www\.)?buzzfeed.com/(about|help|tools)/'),
             callback='parse_page'),
    )

    def parse_page(self, response):
        s = response.selector
        # Remove any content from the tree before passing it to the loader.
        # There aren't native scrapy loader/selector methods for this.        
        mutate_selector_del(s, 'xpath', '//*[contains(@class, "print") or contains(@class, "hidden")]') # Physical print only

        l = NewsLoader(selector=s)

        # Remove referer params from end of URLs
        l.add_xpath('url', 'head/link[@rel="canonical"]/@href')

        # Add a number of items of data that should be standardised across
        # providers. Can override these (for TakeFirst() fields) by making
        # l.add_* calls above this line, or supplement gaps by making them
        # below.
        l.add_fromresponse(response)
        l.add_htmlmeta()
        l.add_schemaorg(response)
        l.add_opengraph()
        l.add_scrapymeta(response)

        l.add_xpath('bodytext', '//div[@data-print="body"]/*[not(contains(@class, "user-bio") or contains(@class, "_shares") or contains(@class, "inline-promo"))]//text()')
        l.add_xpath('bodytext', '//div[contains(@class, "_item_text")]//text()')
        l.add_xpath('bodytext', '//article//*[contains(@class, "subbuzz-text") or '
                                             'contains(@class, "subbuzz__title")]//text()')

        # BF helpfully includes a unix timestamp in its metadata.
        ts = s.xpath('//time/@data-unix').extract_first()
        if ts:
            l.add_value('modtime', datetime.fromtimestamp(int(ts)).isoformat())
 
        return l.load_item()