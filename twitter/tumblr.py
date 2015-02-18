import urllib
from twisted.internet import defer
from twisted.web import client, error, http
import json


class _FetcherTumblr(object):
    # baseURL = 'https://instagram.com/'
    baseDeveloperURL = 'http://api.tumblr.com/v2/'
    client_id = 'FHBOYBPFynpfihv3ZRJ6u5mnpDkWVjDrlL0KDwfEiC2kF2iLFR'
    URITemplate = None  # Override in subclass
    search_by_user = False
    maxErrs = 10
    okErrs = (http.INTERNAL_SERVER_ERROR,
              http.BAD_GATEWAY,
              http.SERVICE_UNAVAILABLE)
    params = {}

    def __init__(self, context):
        assert self.baseDeveloperURL.endswith('/')
        self.results = []
        self.errCount = 0
        self.deferred = defer.Deferred()
        context['client_id'] = self.client_id
        self.context = context

        for k, v in context.iteritems():
            context[k] = urllib.quote_plus(v)

        self.URL = self.baseDeveloperURL + (self.URITemplate % context)

    def _api_request_fail(self, failure):
        failure.trap(error.Error)

        self.errCount += 1
        if (self.errCount < self.maxErrs and
            int(failure.value.status) in self.okErrs):
            self.deferred.callback(self._deDup())
        else:
            self.deferred.errback(failure)

    def _parse(self, result):
        try:
            data = json.loads(result)
            response = ''
            if 'response' in data and 'posts' in data['response']:
                response = data['response']['posts']
            elif 'response' in data:
                response = data['response']

            if response:
                for item in response:
                    current_number = len(self.results)
                    if current_number < int(self.context['count']):
                        self.results.append(item)

                current_count = len(self.results)
                self.context['timestamp'] = self.results[current_count-1]['timestamp']
                if current_count < int(self.context['count']):
                    if (self.search_by_user):
                        self.URITemplate = 'blog/%(query)s.tumblr.com/posts/photo?api_key=%(client_id)s&before=%(timestamp)s'
                    else:
                        self.URITemplate = 'tagged?tag=%(query)s&api_key=%(client_id)s&before=%(timestamp)s'

                    self.URL = self.baseDeveloperURL + (self.URITemplate % self.context)
                    self.fetch()
                else:
                    self.deferred.callback(self._deDup())
            else:
                self.deferred.callback(self._deDup())

        except Exception:
            self.deferred.errback()

    def _deDup(self):
        raise NotImplementedError('Override _deDup in subclasses.')

    def fetch(self):
        print 'search!'
        print self.URL
        d = client.getPage(str(self.URL))
        d.addCallback(self._parse)
        d.addErrback(self._api_request_fail)

        return self.deferred


class SearchFetcherTumblr(_FetcherTumblr):
    URITemplate = 'tagged?tag=%(query)s&api_key=%(client_id)s'

    def __init__(self, context):
        """ if @ exist in the context['query'] than should search by user """
        if context['query'][0] == '@':
            self.search_by_user = True
            context['query'] = context['query'][1:]

            user_kw = {
                'user_name': context['query'],
                'client_id': self.client_id,
            }

            self.URITemplate = 'blog/%(user_name)s.tumblr.com/posts/photo?api_key=%(client_id)s' % user_kw
            self.URL = self.baseDeveloperURL + self.URITemplate

        super(SearchFetcherTumblr, self).__init__(context)

    def _deDup(self):
        return self.results
