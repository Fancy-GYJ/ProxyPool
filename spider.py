from utils import get_page
import re
import sys
from config2 import *
from db import RedisClient
from colorama import Fore
from concurrent.futures import ThreadPoolExecutor
from test_proxy_vaild import test_proxy_vaild
# from scheduler import Scheduler


# import pyquery as pq


class PoolEmptyError(Exception):
    def __init__(self):
        Exception.__init__(self)

    def __str__(self):
        return repr('代理池已经枯竭')


class ProxyMetaClass(type):
    def __new__(cls, name, bases, attrs):
        count = 0
        attrs['__CrawlFunc__'] = []
        for k, v in attrs.items():
            if 'crawl_' in k:
                attrs['__CrawlFunc__'].append(k)
                count += 1
        attrs['__CrawlFuncCount__'] = count
        return type.__new__(cls, name, bases, attrs)


class Crawler(object, metaclass=ProxyMetaClass):
    def get_proxies(self, callback):
        for proxy in eval("self.{}()".format(callback)):
            yield proxy


    def crawl_xicidaili(self):
        for page in range(1, 10):
            start_url = 'http://www.xicidaili.com/nn/{}'.format(page)
            html = get_page(start_url)
            if html:
                find_trs = re.compile('<tr class.*?>(.*?)</tr>', re.S)
                trs = find_trs.findall(html)
                for tr in trs:
                    find_ip = re.compile('<td>(\d+\.\d+\.\d+\.\d+)</td>')
                    re_ip_address = find_ip.findall(tr)
                    find_port = re.compile('<td>(\d+)</td>')
                    re_port = find_port.findall(tr)
                    for address, port in zip(re_ip_address, re_port):
                        address_port = address + ':' + port
                        yield address_port.replace(' ', '')

    def crawl_iphai(self):
        for page in range(10):
            start_url = 'http://www.iphai.com/free/%s' % (page)
            html = get_page(start_url)
            if html:
                find_tr = re.compile('<tr>(.*?)</tr>', re.S)
                trs = find_tr.findall(str(html))
                for s in range(1, len(trs)):
                    find_ip = re.compile('<td>\s+(\d+\.\d+\.\d+\.\d+)\s+</td>', re.S)
                    re_ip_address = find_ip.findall(trs[s])
                    find_port = re.compile('<td>\s+(\d+)\s+</td>', re.S)
                    re_port = find_port.findall(trs[s])
                    for address, port in zip(re_ip_address, re_port):
                        address_port = address + ':' + port
                        print(address_port)
                        yield address_port.replace(' ', '')


class PoolGetter(object):
    def __init__(self):
        self.redis = RedisClient()
        self.crawler = Crawler()

    def is_over_threshold(self):
        if self.redis.count() >= POOL_UPPER_THRESHOLD:
            return True
        else:
            return False

    def test_proxy_add(self, proxy):
        if test_proxy_vaild(proxy):
            print(Fore.GREEN + "成功获取到代理IP", proxy)
            self.redis.add(proxy)

    def run(self):
        print("[-]代理池获取器开始执行")
        if not self.is_over_threshold():
            for callback_label in range(self.crawler.__CrawlFuncCount__):
                callback = self.crawler.__CrawlFunc__[callback_label]
                proxies = self.crawler.get_proxies(callback)
                sys.stdout.flush()
                with ThreadPoolExecutor(ThreadCount) as pool:
                    pool.map(self.test_proxy_add, proxies)


def is_crawelr_ok():
    crawler = Crawler()
    for callback_label in range(crawler.__CrawlFuncCount__):
        callback = crawler.__CrawlFunc__[callback_label]
        proxies = crawler.get_proxies(callback)
        for item in proxies:
            print(item)


def is_pool_ok():
    proxyPool = PoolGetter()
    proxyPool.run()
    print("proxy count:", proxyPool.redis.count())


if __name__ == '__main__':

    # is_crawelr_ok()
    is_pool_ok()




