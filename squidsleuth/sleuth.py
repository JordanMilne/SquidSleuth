import collections
import hashlib
import logging
import re
import threading
import time

from requests_futures.sessions import FuturesSession
from six.moves.urllib import parse as urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .parsers import parse_active_requests, parse_domain_from_uri
from .db import SeenRequest


LOG = logging.getLogger(__name__)


class RequestTracker(object):
    """
    A simple tracker for requests that we've seen recently

    Requests that we haven't seen recently will get dropped so we don't leak
    memory.
    """
    def __init__(self, maxlen=25000):
        self._counter = collections.Counter()
        self._deque = collections.deque()
        self.maxlen = maxlen
        self.hits = 0
        self.misses = 0
        self.hash_key = self._default_hash_key

    def __len__(self):
        return len(self._deque)

    def __contains__(self, item):
        return self.hash_key(item) in self._counter

    @property
    def hitrate(self):
        if not self.hits:
            return 0
        return float(self.hits) / (self.hits + self.misses)

    def _pop_old(self):
        while len(self._deque) > self.maxlen:
            old_hash = self._deque.popleft()
            ref_count = self._counter[old_hash] - 1
            if not ref_count:
                del self._counter[old_hash]
            else:
                self._counter[old_hash] = ref_count

    @staticmethod
    def _default_hash_key(obj):
        return hashlib.sha1(repr(obj)).digest()

    def track(self, req):
        req_hash = self.hash_key(req)

        in_counter = req_hash in self._counter

        self._deque.append(req_hash)
        self._counter.update({req_hash: 1})
        self._pop_old()

        if in_counter:
            self.hits += 1
            return True
        else:
            self.misses += 1
            return False


class Sleuth(object):
    MAX_REQUESTS = 10
    BASE_URL_RE = re.compile(r"(\w+://[^/]+/)squid-internal-mgr")

    def __init__(self, proxy_host, conn_str):
        self.proxy_host = proxy_host
        self.req_session = FuturesSession(max_workers=self.MAX_REQUESTS*2)
        self.base_url = None
        engine = create_engine(conn_str)
        self._sess_maker = sessionmaker(bind=engine)
        self.req_session.proxies = {"http": proxy_host, "https": proxy_host}
        self._reqTracker = RequestTracker()
        self._activeRequests = 0
        self._seenRequests = 0
        self._responseLock = threading.Lock()

    def _make_request(self, url, cb):
        future = self.req_session.get(url)
        self._activeRequests += 1
        future.add_done_callback(cb)
        return future

    def _scrape_active_requests(self):
        return self._make_request(self.base_url + "squid-internal-mgr/active_requests",
                                  self._handle_active_requests_response)

    def _handle_active_requests_response(self, fut):
        sess = None
        LOG.debug("Handling active requests response")
        try:
            sess = self._sess_maker()
            resp = fut.result()
            with self._responseLock:
                if resp.status_code == 200:
                    parsed_reqs = parse_active_requests(resp.content)
                    for req in parsed_reqs:
                        if not self._reqTracker.track(req):
                            self._log_request(req, sess)
                else:
                    LOG.warn("Proxy returned bad response")
        finally:
            self._activeRequests -= 1
            sess.commit()

    def _log_request(self, req, sess):
        self._seenRequests += 1
        domain = parse_domain_from_uri(req["uri"])
        req_row = SeenRequest(domain=domain, **req)
        sess.add(req_row)

    def _check_base_url(self, base_url):
        resp = self.req_session.get(base_url + "squid-internal-mgr/menu").result()
        if resp.status_code != 200:
            if "<body id=ERR_ACCESS_DENIED>" not in resp.text:
                return False, None
            return False, resp.text
        elif "Cache Manager Interface" not in resp.text:
            return False, None
        return True, None

    def _setup(self):
        parsed = urlparse.urlparse(self.proxy_host)
        port_segment = ":" + str(parsed.port) if parsed.port else ""
        parsed = parsed._replace(netloc="localhost" + port_segment, path="/")
        guessed_base_url = urlparse.urlunparse(parsed)
        valid, resp = self._check_base_url(guessed_base_url)
        if valid:
            self.base_url = guessed_base_url
        else:
            if not resp:
                raise Exception("Not a Squid server?")

            base_url_res = re.search(self.BASE_URL_RE, resp)
            if not base_url_res:
                raise Exception("Couldn't detect base URL?")
            guessed_base_url = base_url_res.group(1)
            valid, resp = self._check_base_url(guessed_base_url)
            if valid:
                self.base_url = guessed_base_url
            else:
                raise Exception("No access to squid-internal-mgr ;(")

    def _tick(self):
        if self._activeRequests > self.MAX_REQUESTS:
            LOG.debug("sleeping")
            time.sleep(0.01)
            return
        LOG.info("Scraping %r", (self._activeRequests, self._reqTracker.hitrate, self._seenRequests))
        self._scrape_active_requests()
        time.sleep(0.275)

    def run(self):
        self._setup()
        while True:
            self._tick()
