#!/bin/env python
# coding=utf-8
from __future__ import print_function, division

import datetime as dt
import unittest

from squidsleuth import parsers, sleuth


class ParserTests(unittest.TestCase):
    def test_parse_cache_objects(self):
        buf = b"""KEY 3882356D0002E51DE3F7EC0176FE5FFC
\tSTORE_OK      IN_MEMORY     SWAPOUT_NONE PING_DONE
\tCACHABLE,DISPATCHED,VALIDATED
\tLV:1451201123 LU:1451201130 LM:-1        EX:1453571570
\t0 locks, 0 clients, 1 refs
\tSwap Dir -1, File 0XFFFFFFFF
\tGET http://foo.com/
\tvary_headers: accept-encoding="gzip,%20deflate"
\tinmem_lo: 0
\tinmem_hi: 69347
\tswapout: 0 bytes queued

KEY 38E2CC042B8059E878133FB46E03DDF3
\tSTORE_OK      IN_MEMORY     SWAPOUT_NONE PING_NONE
\tCACHABLE,VALIDATED
\tLV:1451201322 LU:1451201322 LM:-1        EX:1451301322
\t0 locks, 0 clients, 0 refs
\tSwap Dir -1, File 0XFFFFFFFF
\tGET http://foobar.com/
\tinmem_lo: 0
\tinmem_hi: 216
\tswapout: 0 bytes queued"""
        parsed = parsers.parse_cache_objects(buf)
        self.assertEqual(list(parsed), [
            {
                "key": b"3882356D0002E51DE3F7EC0176FE5FFC",
                "method": b"GET",
                "uri": b"http://foo.com/",
            },
            {
                "key": b"38E2CC042B8059E878133FB46E03DDF3",
                "method": b"GET",
                "uri": b"http://foobar.com/",
            },
        ])

    def test_parse_active_requests(self):
        buf = br"""Connection: 0x7fc76fd49428
        FD 1476, read 2942816, wrote 6506335
        FD desc: Reading next request
        in: buf 0x7fc759624ec0, offset 0, size 4096
        remote: 1.1.1.1:52023
        local: 2.2.2.2:8080
        nrequests: 7075
uri http://coolvideos.com/whatever.mp4
logType TCP_MISS
out.offset 0, out.size 0
req_sz 416
entry 0x7fc75c1f54f1/D92C432D9882D800F39A792F28C567F9
start 1451138417.204524 (0.000236 seconds ago)
username
delay_pool 0

Connection: 0x7fc773715cf3
        FD 4101, read 481, wrote 43547712
        FD desc: Reading next request
        in: buf 0x7fc7701215e0, offset 0, size 4096
        remote: 4.4.4.4:60954
        local: 5.5.5.5:8080
        nrequests: 1
uri foobar.net:443
logType TCP_MISS
out.offset 43551360, out.size 43547712
req_sz 481
entry 0x7fc76d25e431/5262A75B51CDE5C08601697FF66DE86F
start 1451138311.399619 (105.805141 seconds ago)
username
delay_pool 0"""
        parsed = parsers.parse_active_requests(buf)
        self.assertEqual(list(parsed),
            [
                {
                    "client": b"1.1.1.1",
                    "date": dt.datetime(2015, 12, 26, 14, 0, 17, 204524),
                    "uri": b"http://coolvideos.com/whatever.mp4",
                },
                {
                    "client": b"4.4.4.4",
                    "date": dt.datetime(2015, 12, 26, 13, 58, 31, 399619),
                    "uri": b"foobar.net:443",
                },
            ]
        )

    def test_parse_netdb_entries(self):
        buf = br"""Network DB Statistics:
Network                                        recv/sent     RTT  Hops Hostnames
1.1.1.1                                        0/   1     0.0   0.0 foo.com baz.com
2.2.2.2                                        0/   1     0.0   0.0 bar.com"""
        parsed = parsers.parse_netdb_entries(buf)
        self.assertSequenceEqual(list(parsed), [b"foo.com", b"baz.com", b"bar.com"])


class RequestTrackerTests(unittest.TestCase):
    def test_expiry(self):
        tracker = sleuth.RequestTracker(4)
        tracker.track("foo")
        tracker.track("bar")
        tracker.track("baz")
        tracker.track("quux")
        tracker.track("plugh")

        self.assertEqual(len(tracker), 4)
        self.assertFalse("foo" in tracker)
        self.assertTrue("bar" in tracker)

    def test_duplicate(self):
        tracker = sleuth.RequestTracker(4)
        tracker.track("bar")
        tracker.track("foo")
        tracker.track("bar")
        tracker.track("quux")
        tracker.track("plugh")
        tracker.track("thing")

        self.assertEqual(len(tracker), 4)
        self.assertTrue("bar" in tracker)
        self.assertFalse("foo" in tracker)


if __name__ == '__main__':
    unittest.main()
