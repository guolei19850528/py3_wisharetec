import os
import unittest

import diskcache

from py3_wisharetec.scaasp.admin import Admin


class MyTestCase(unittest.TestCase):
    def test_scaasp(self):
        cache = diskcache.Cache(directory=os.path.join(os.getcwd(), "runtime", "diskcache", "default"))
        admin=Admin(
            username="test_1",
            password="guolei_123",
            cache=cache,
        )
        print(admin.login_with_cache().query_communit_with_paginator(params={"curPage":1,"pageSize":10}))
        self.assertTrue(True, "ok")  # add assertion here


if __name__ == '__main__':
    unittest.main()
