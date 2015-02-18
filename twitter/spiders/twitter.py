import scrapy
import json

from datetime import datetime
from scrapy.shell import inspect_response
from scrapy.selector import Selector, HtmlXPathSelector
from scrapy.http import Request


class TwitterSpider(scrapy.Spider):
    name = 'twitter'
    allowed_domains = ['twitter.com']
    # start_urls = ['https://twitter.com/i/profiles/show/Britanniacomms/timeline?composed_count=0&contextual_tweet_id=567296595495247872&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&last_note_ts=631&latent_count=0&since_id=567305261145391105']
    # start_urls = ['https://twitter.com/Britanniacomms']
    # Colombian2014
    # Britanniacomms
    # Econsultancy
    start_urls = ['https://twitter.com/i/profiles/show/Econsultancy/timeline']
    mask = 'https://twitter.com/i/profiles/show/Econsultancy/timeline?contextual_tweet_id=%s&max_id=%s'
    i = 0
    page = 0

    # def __init__(self, *args, **kwargs):
    def parse(self, response):
        d = json.loads(response.body)
        sel = HtmlXPathSelector(text=d['items_html'])
        divs = sel.xpath('//div[@class="Grid"]')
        if len(divs) == 0:
            return

        self.page += 1
        print 'PAGE: %s' % self.page
        item_id = 0
        max_id = None
        # print 'HAS %s' % d['has_more_items']
        # if not d['has_more_items']:
        #     print 'HAS NO MORE ITEMS'
        #     return
        if 'max_id' in d.keys():
            max_id = d['max_id']

        for div in divs:
            name = div.xpath('.//span[@class="ProfileTweet-screenname u-dir"]/text()').extract()
            item_id = div.xpath('.//div[@data-item-id]/@data-item-id').extract()[0]
            if not max_id:
                max_id = item_id

            t = ''
            real_date = div.xpath('.//span[@class="u-floatLeft"]/a/span[@data-time]/@data-time').extract()[0]
            try:
                t = div.xpath('.//span[@class="u-floatLeft"]/a/span[@data-time]/text()').extract()[0].strip()
                print '@%s tweet id: %s. Time: %s. %s' % \
                      (''.join(name).strip(), item_id, t,
                       datetime.fromtimestamp(int(real_date)))
            except Exception, e:
                print 'Error with id %s: %s' % (item_id, str(e))

        if self.i < 100 and max_id:
            self.i += 1
            yield Request(self.mask % (int(item_id), int(max_id)),
                          callback=self.parse)
        # inspect_response(response, self)
