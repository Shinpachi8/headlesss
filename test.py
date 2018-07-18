import asyncio
import time
import re
import json
import sys
import threading
from queue import Queue
from multiprocessing import Process
from pyppeteer.launcher import connect
from threading import Thread
from lib.RedisUtil import RedisConf,RedisUtils
# from bs4 import BeautifulSoup as bs
from lib.headlesscrower import HeadlessCrawler
from lib.commons import TURL, hashmd5, get_basedomain, argsparse
from lib.MongoUtil import MongoConf, MongoUtils
from lib.UrlDeDuplicate import UrlPattern
from multi_process import AdvancedConcurrencyManager
#from pyppeteer.network_manager import Request




class SpiderWork(object):
    '''
    这个类是一个单页面爬取的类，保存链接至mongo
    '''
    def __init__(self, wsaddr, url, taskname, basedomain=1, cookie=None, goon=False, mongodb='spider', redisdb=1):
        '''
        :param wsaddr:　websocket address of headless chrome
        :param url: url to spider 
        :param taskname: taskname, used at redis pattern 
        :param cookie: the file contains the cookie
        :param goon: if continue the spider
        :param basedomian: the level of fetch domain from url
        :param mongodb: the mongodb to save
        '''
        self.wsaddr = wsaddr
        self.url = url
        self.taskname = taskname
        self.basedomain = basedomain
        self.cookie = cookie
        self.goon = goon
        self.mongodb = mongodb
        # host, port, db
        mongoconf = MongoConf('127.0.0.1', 27017, mongodb)
        self.mongoutil = MongoUtils(mongoconf)
        redisconf = RedisConf(taskname, db=redisdb)
        self.redisutil = RedisUtils(redisconf)
        self.domain = get_basedomain(url, basedomain)

    def fetchCookie(self):
        cookie = None
        try:
            with open(self.cookie, 'r') as f:
                cookie = json.load(f)
        except Exception as e:
            msg = '[fetchCookie] [Error] ' + repr(e)
            print(msg)
            cookie = None
        return cookie


    def sameOrigin(self, url, domain):
        try:
            turl = TURL(url)
            #print("turl.netloc ={}  domain={}".format(turl.netloc, domain))
            assert turl.netloc.find(domain) >= 0, '{} is not belongs {}'.format(url, domain)
            assert turl.is_block_host() == False, '{} is block host'.format(url)
            assert turl.is_block_path() == False, '{} is block path'.format(url)
            assert turl.is_ext_static() == False, '{} is static extention'.format(url)
            return True
        except Exception as e:
            return False

    async def _spider(self):

        redisutil = self.redisutil
        if not self.goon:
            print("start from new url.....")
            cookie = self.fetchCookie()
            a = HeadlessCrawler(wsaddr, url, cookie=cookie)
            await a.spider()
            for url in a.collect_url:
                u = url['url']
                if not self.sameOrigin(u, self.domain):
                    continue

                method = url['method']
                pattern = UrlPattern(u).get_pattern()
                pattern_md5 = hashmd5(pattern)
                if 'request' in url:
                    result = json.dumps(url)
                    redisutil.insert_result(result)
                    redisutil.set_url_scanned(method, pattern_md5)
                else:

                    if redisutil.is_url_scanned(method, pattern_md5):
                        pass
                    else:
                        task = json.dumps(url)
                        redisutil.insert_one_task(task)
                        redisutil.set_url_scanned(method, pattern_md5)
                        self.mongoutil.save(url)

        tasks = [asyncio.ensure_future(self.worker()) for i in range(10)]
        # print(tasks)
        await asyncio.wait(tasks)

    async def worker(self):
        redisutil = self.redisutil
        cookie = self.fetchCookie()
        if goon:
            pass
        while True:
            if redisutil.task_counts == 0:
                break

            task = redisutil.fetch_one_task()
            url = json.loads(task)
            # 同源
            u = url['url']
            print("=========================fetched Form Redis: {}==================".format(redisutil.result_counts))
            depth = url['depth']
            if depth > 3: # 超过四层就退出
                print("---------------depth > 3-------------")
                continue


            a = HeadlessCrawler(self.wsaddr, u, cookie=cookie, depth=url['depth']+1)
            await a.spider()
            for url in a.collect_url:
                u = url['url']

                if not self.sameOrigin(u, self.domain):
                    continue
                pattern = UrlPattern(u).get_pattern()
                pattern_md5 = hashmd5(pattern)
                method = url['method']

                if 'request' in url:
                    result = json.dumps(url)
                    redisutil.insert_result(result)
                    redisutil.set_url_scanned(method, pattern_md5)
                else:
                    if redisutil.is_url_scanned(method, pattern_md5):
                        pass
                    else:
                        task = json.dumps(url)
                        redisutil.insert_one_task(task)
                        redisutil.set_url_scanned(method, pattern_md5)
                        redisutil.save(url)

    async def _closePage(self):
        '''
        超时之后可能不会关闭Page，如果不自动关闭会导致过多的page页
        '''
        browser = async connect(browserWSEndpoint=self.wsaddr)
        pages = await browser.pages()
        for page in pages:
            await page.close()




    def spider(self):
        start = time.time()
        loop = asyncio.get_event_loop()
        x = self._spider()
        try:
            tasks = [asyncio.ensure_future(x),]
            loop.run_until_complete(asyncio.wait(tasks))
        except KeyboardInterrupt as e:
            # print(asyncio.Task.all_tasks())
            for task in asyncio.Task.all_tasks():
                # print(task.cancel())
                task.cancel()
            # close pages
            closeTask = self._closePage()
            tasks = [asyncio.ensure_future(closeTask),]
            loop.run_until_complete(asyncio.wait(tasks))
            loop.stop()
            loop.run_forever()
        finally:
            loop.close()
        print(time.time() - start)




async def worker(conf, wsaddr, cookie=None, domain='', goon=False, mongo=None):
    redis_util = RedisUtils(conf)
    mongoutil = mongo
    if goon:
        pass
    # print("wsaddr={}\ndomain={}".format(wsaddr, domain))
    while True:
        # 退出条件？如果用广度优先遍历，那么深度到一定程序如4层，就可以退出了
        # 或者redis的任务为0了,就可以退出了
        if redis_util.task_counts == 0:
            break
        # if unscan_queue.empty():
        #     break
        task = redis_util.fetch_one_task()
        # task = unscan_queue.get()
        url = json.loads(task)
        # 同源
        u = url['url']
        print("=========================fetched Form Redis: {}==================".format(redis_util.result_counts))
        depth = url['depth']
        if depth > 3: # 超过四层就退出
            print("---------------depth > 3-------------")
            continue


        a = HeadlessCrawler(wsaddr, u, cookie=cookie, depth=url['depth']+1)
        await a.spider()
        for url in a.collect_url:
            u = url['url']

            if not sameOrigin(u, domain):
                continue
            pattern = UrlPattern(u).get_pattern()
            pattern_md5 = hashmd5(pattern)
            method = url['method']

            if 'request' in url:
                result = json.dumps(url)
                # # 插入结果，后续可以直接插入到Mongo里
                redis_util.insert_result(result)
                redis_util.set_url_scanned(method, pattern_md5)
            else:
                if redis_util.is_url_scanned(method, pattern_md5):
                    # print("[Pattern Found] [{}]".format(pattern))
                    pass
                else:
                    task = json.dumps(url)
                    redis_util.insert_one_task(task)
                    redis_util.set_url_scanned(method, pattern_md5)
                    mongoutil.save(url)
                # unscan_queue.put(task)
                # scanned_set.add( pattern + "|" + pattern_md5)



def sameOrigin(url, domain):
    try:
        turl = TURL(url)
        #print("turl.netloc ={}  domain={}".format(turl.netloc, domain))
        assert turl.netloc.find(domain) >= 0, '{} is not belongs {}'.format(url, domain)
        assert turl.is_block_host() == False, '{} is block host'.format(url)
        assert turl.is_block_path() == False, '{} is block path'.format(url)
        assert turl.is_ext_static() == False, '{} is static extention'.format(url)
        return True
    except Exception as e:
        return False


async def spider(wsaddr, url, taskname, cookie=None, goon=False, mongo=None):
    # 2018-07-09 先写单线程，再写成生产者和消费者
    conf = RedisConf(taskname, db=1)
    redis_util = RedisUtils(conf)
    unscan_queue = Queue()
    result_queue = Queue()
    scanned_set = set()
    domain = get_basedomain(url)
    print(domain)
    # count = 0
    # 设置domain
    redis_util.set_task_domain(domain)

    if not goon:
        print("start from new url.....")
        a = HeadlessCrawler(wsaddr, url, cookie=cookie)
        await a.spider()
        # print(a.collect_url)
        for url in a.collect_url:
            # 还可以判断一下url的类型
            u = url['url']
            # 先判断是否是同一个域名下的
            if not sameOrigin(u, domain):
                continue

            method = url['method']
            pattern = UrlPattern(u).get_pattern()
            pattern_md5 = hashmd5(pattern)
            if 'request' in url:
                result = json.dumps(url)
                # method = url['method']
                # 插入结果，后续可以直接插入到Mongo里
                redis_util.insert_result(result)
                redis_util.set_url_scanned(method, pattern_md5)
            else:

                if redis_util.is_url_scanned(method, pattern_md5):
                    pass
                else:
                    task = json.dumps(url)
                    redis_util.insert_one_task(task)
                    redis_util.set_url_scanned(method, pattern_md5)
                    mongo.save(url)

    tasks = [asyncio.ensure_future(worker(conf, wsaddr, cookie, domain, mongo=mongo)) for i in range(10)]
    # print(tasks)
    await asyncio.wait(tasks)

    '''
    threads = []
    for i in range(2):
        t = Thread(target=workthread, args=(conf, wsaddr, cookie, domain))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    '''
    # for i in range(20):
    #     # 20协程来跑
    #     await worker(redis_util, wsaddr, cookie, domain=domain)

    # while True:
    #     # 退出条件？如果用广度优先遍历，那么深度到一定程序如4层，就可以退出了
    #     # 或者redis的任务为0了,就可以退出了
    #     if redis_util.task_counts == 0:
    #         break
    #     # if unscan_queue.empty():
    #     #     break
    #     task = redis_util.fetch_one_task()
    #     # task = unscan_queue.get()
    #     url = json.loads(task)
    #     # 同源
    #     u = url['url']
    #     if not sameOrigin(u, domain):
    #         continue


    #     a = HeadlessCrawler(wsaddr, u, cookie=cookie, depth=url['depth']+1)
    #     await a.spider()
    #     for url in a.collect_url:
    #         # 还可以判断一下url的类型
    #         depth = url['depth']
    #         if depth > 3: # 超过四层就退出
    #             print("---------------depth > 3-------------")
    #             continue

    #         u = url['url']

    #         if not sameOrigin(u, domain):
    #             continue


    #         pattern = UrlPattern(u).get_pattern()
    #         pattern_md5 = hashmd5(pattern)
    #         method = url['method']

    #         if 'request' in url:
    #             result = json.dumps(url)
    #             # # 插入结果，后续可以直接插入到Mongo里
    #             redis_util.insert_result(result)
    #             redis_util.set_url_scanned(method, pattern_md5)
    #         else:
    #             if redis_util.is_url_scanned(method, pattern_md5):
    #                 pass
    #             else:
    #                 task = json.dumps(url)
    #                 redis_util.insert_one_task(task)
    #                 redis_util.set_url_scanned(method, pattern_md5)
    #             # unscan_queue.put(task)
    #             # scanned_set.add( pattern + "|" + pattern_md5)

    print("-----------done------")










def main():
    args = argsparse()

    wsaddr = args.wsaddr
    url = args.u
    cookie_file = args.cookie
    iqiyi_cookie = None
    MongoConf.db = args.mongo_db
    if cookie_file:
        with open(cookie_file, 'r') as f:
            iqiyi_cookie = json.load(f)
    #print(iqiyi_cookie)
    # print(type(iqiyi_cookie))
    mongoutil = MongoUtils(MongoConf)
    assert mongoutil.connected is True

    print(wsaddr, url)
    # with open('fetched_url.json', 'w') as f:
    #     json.dump((a.fetched_url), f)

    # wsaddr = 'ws://10.127.21.237:9222/devtools/browser/f3f68d37-aabb-43b7-9d75-986a8be08e2d'
    # url = 'http://www.iqiyi.com'
    taskname = args.taskname
    spider = SpiderWork(wsaddr, url, taskname, mongodb='spiderworktest')
    spider.spider()

    '''
    start = time.time()
    loop = asyncio.get_event_loop()
    x = spider(wsaddr, url, taskname, cookie=iqiyi_cookie, goon=False, mongo=mongoutil)
    try:
        tasks = [asyncio.ensure_future(x),]
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt as e:

        print(asyncio.Task.all_tasks())
        for task in asyncio.Task.all_tasks():
            print(task.cancel())
        loop.stop()
        loop.run_forever()
    finally:
        loop.close()
    print(time.time() - start)
    '''

if __name__ == '__main__':
    p = Process(target=main)
    p.daemon = True
    p.start()
    starttime = time.time()
    while True:
        t = time.time() - starttime
        if t > 10 * 60:
            print("timeout")
            break
        elif not p.is_alive():
            break
        else:
            time.sleep(10)
    '''
    main()
    '''


