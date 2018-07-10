import asyncio
import time
import re
import json
from asyncio import Queue
# from bs4 import BeautifulSoup as bs
from lib.headlesscrower import HeadlessCrawler
from lib.commons import TURL
#from pyppeteer.network_manager import Request



def get_pattern(url):
    if isinstance(url, TURL):
        pass
    else:
        url = TURL(url)
    query = url.get_query
    pattern = re.sub(r'\d+', '{digit}', query)
    url.query = pattern
    url = url.url_string()
    return url


async def test(wsaddr, url):
    # 2018-07-09 先写单线程，再写成生产者和消费者
    request_set = Queue()
    pattern_set = set()
    unrequest_set = Queue()

    a = HeadlessCrawler(wsaddr, url)
    await a.spider()
    # print(a.collect_url)
    for url in a.collect_url:
        # u = url['url']
        # u = TURL(u)
        # if u.is_ext_static() or u.is_block_path() or u.is_block_host():
        #     # 静态文件，黑名单路径，黑名单的host
        #     continue
        # pattern = get_pattern(u)
        # if pattern in pattern_set:
        #     continue
        # else:
        #     pattern_set.add(pattern)
        # if 'request' in url:
        #     request_set.put(url)
        # else:
        await unrequest_set.put(url)

    depth = 0
    print("[now] [lenth of unrequest_set] =======  {}".format(unrequest_set.qsize()))
    while not unrequest_set.empty():
        # print("[now] [lenth of unrequest_set] =======  {}".format(unrequest_set.qsize()))
        url = await unrequest_set.get()
        depth = int(url['depth'])
        if depth > 3:
            continue
        else:
            depth += 1
        url = url['url']
        pattern = get_pattern(url)
        if pattern in pattern_set:
            print("found pattern, igore URL： {}".format(u))
            continue
        else:
            pattern_set.add(pattern)


        a = HeadlessCrawler(wsaddr, url, depth=depth)
        await a.spider()
        print("===========================================\n")
        print("url: {}".format(url))
        print("len_of_a.collect_url:  {}".format(len(a.collect_url)))
        print("===========================================\n")
        for url in a.collect_url:
            u = url['url']
            if u.startswith('javascript') or u.startswith("about"):
                continue
            u = TURL(u)
            if u.is_ext_static():
                print("u.is_ext_static: {}".format(u))
                continue
            elif u.is_block_path():
                print("u.is_block_path: {}".format(u))
                continue
            elif u.is_block_host():
                print("u.is_block_host: {}".format(u))
                continue

            
            # print('pattern==={}'.format(pattern))
            if 'request' in url:
                await request_set.put(url)
                print("[now] [lenth of request_set] =======  {}".format(request_set.qsize()))
            else:
                await unrequest_set.put(url)



    print("========done=========")
    all_url = []
    while not request_set.empty():
        _ = await request_set.get()
        all_url.append(_)
    
    with open('result.json', 'w') as f:
        json.dump(all_url, f)







async def main():
    wsaddr = 'ws://10.127.21.237:9223/devtools/browser/daff194a-35c9-448e-8aa7-97883931103b'
    url = 'http://testphp.vulnweb.com/AJAX/index.php'
    # with open('fetched_url.json', 'w') as f:
    #     json.dump((a.fetched_url), f)
    await test(wsaddr, url)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
