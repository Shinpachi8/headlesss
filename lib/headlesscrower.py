import asyncio
import pyppeteer
import time
import traceback
# import urlparse
import os
import json
import re
import hashlib
from urllib import parse as urlparse
import sys
from pyppeteer.launcher import connect
from pyppeteer import launch
# from pyppeteer.network_manager import Response
from bs4 import BeautifulSoup as bs
from pyee import EventEmitter
# from config import *


async def mutationobserver(page):
    '''
    mutation observer the dom change
    '''
    # dismiss the dialog
    # result = await page.evaluate('''()=>123123''')
    jsfunc_str = '''()=>{
        window.EVENTS = [];
        window.EVENTS_HISTORY = [];
        window.LINKS = [];
        window.nodes = [];
        var MutationObserver = window.MutationObserver;
        var callback = function (records) {
            records.forEach(function (record) {
                //console.info('Mutation type: ', record.type);
                if (record.type == 'attributes') {
                    //console.info("Mutation attributes:", record.target[record.attributeName]);
                    window.LINKS.push(record.target[record.attributeName]);
                } else if (record.type == 'childList') {
                    for (var i = 0; i < record.addedNodes.length; ++i) {
                        //console.log("recode.addedNodes[i]", record.addedNodes[i].innerHTML);
                        var node = record.addedNodes[i];
                        if (node.src || node.href) {
                            window.LINKS.push(node.src || node.href);
                            //console.info('Mutation AddedNodes:', node.src || node.href);
                            };

                        try{
                            var a_tag = record.addedNodes[i].querySelectorAll('a');

                            for(var j = 0; j < a_tag.length; ++j){
                                var a = a_tag[j];
                                if (a.src || a.href) {
                                    window.LINKS.push(a.src || a.href);
                                    //console.log('Mutation AddedNodes:', a.src || a.href);
                                    };
                            }

                        }catch(err){
                            console.log(err);
                        }

                    }
                }
            });
        };
        var option = {
            'childList': true,
            'subtree': true,
            'attributes': true,
            'attributeFilter': ['href', 'src']
        };
        var mo = new MutationObserver(callback);
        mo.observe(document, option);

        Element.prototype._addEventListener = Element.prototype.addEventListener;
        Element.prototype.addEventListener = function (a, b, c) {
            var hash = a + this.tagName + '|' + this.className + '|' + this.id + '|' + this.tabIndex;
            if (window.EVENTS_HISTORY.indexOf(hash) < 0) {
                window.EVENTS.push({"event": a, "element": this});
                window.EVENTS_HISTORY.unshift(hash);
                //console.info('addEventListener:', a, this);
            }
            this._addEventListener(a, b, c);
        };

    }'''

    # 这个函数只是劫持了window.location函数，并没有真正的去请求，所以request并没有Hook住这里的请求
    hook_windows = '''hook_window = ()=> {
        //console.log('hook_window function executed!!!');
        //window.openlinks = [];
        window.Redirects = [];
        var oldLocation = window.location;
        var fakeLocation = Object();
        fakeLocation.replace = fakeLocation.assign = function (value) {
            console.log("new link: " + value);
        };
        fakeLocation.reload = function () {};
        fakeLocation.toString = function () {
            return oldLocation.toString();
        };
        Object.defineProperties(fakeLocation, {
            'href': {
                'get': function () { return oldLocation.href; },
                'set': function (value) {window.Redirects.push(value); console.log("new link: " + value); }
            },
            // hash, host, hostname ...
        });
        var replaceLocation = function (obj) {
            Object.defineProperty(obj, 'location', {
                'get': function () { return fakeLocation; },
                'set': function (value) {window.Redirects.push(value); console.log("new link: " + value); }
            });
        };

        replaceLocation(window);
        addEventListener('DOMContentLoaded', function () {
            replaceLocation(document);
        })
    }
    '''

    # hook window.open function，防止别人hook
    # 设置时间为0
    hook_open = """() => {

            window.open = function(url) { console.log('hook before defineProperty'); };
            Object.defineProperty(window, 'open', {
                value: window.open,
                writable: false,
                configurable: false,
                enumerable: true
            });
            window.open = function(url) { console.log(url);  window.Redirects.push(url); console.log(JSON.stringify(window.openlinks)); };

            window.__originalSetTimeout = window.setTimeout;
            window.setTimeout = function() {
                arguments[1] = 0;
                return window.__originalSetTimeout.apply(this, arguments);
            };
            window.__originalSetInterval = window.setInterval;
            window.setInterval = function() {
                arguments[1] = 0;
                return window.__originalSetInterval.apply(this, arguments);
            };

            }"""
    #print(dir(page))
    await page.evaluateOnNewDocument(hook_windows)
    await page.evaluateOnNewDocument(jsfunc_str)
    await page.evaluateOnNewDocument(hook_open)
    # jsfunc_str_exec = '''monitor()'''
    # result2 = await page.evaluate(jsfunc_str_exec)
    print('获取事件被触发后的节点属性变更更信息')




async def dismiss_dialog(dialog):
    print("dialog found")
    await dialog.accept()

async def hook_error(error):
    # print("error found:  {}".format(error))
    pass

async def get_event(page):
    js_getevent_func = '''get_event = ()=>{
    var event = {};
    event['link'] = [];
    var treeWalker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_ELEMENT,
        { acceptNode: function(node) { return NodeFilter.FILTER_ACCEPT; } },
        false
    );
    while(treeWalker.nextNode()) {
        var element = treeWalker.currentNode
        var attrs = element.getAttributeNames()
        for(var i=0; i < attrs.length; i++){
            var attr_name = attrs[i];
            if(attr_name.startsWith("on")){
                // 如果有这个事件
                var attr_value = element.getAttribute(attr_name);
                //console.log("attr_name: "+ attr_name + " VS attr_value: " + attr_value);
                if(attr_name in event){
                    if(attr_value in event[attr_name]){
                        console.log("already add to event: " + attr_name + attr_value);
                    }else{
                        event[attr_name].push(attr_value);
                    }
                }else{
                    event[attr_name] = [];
                    event[attr_name].push(attr_value);
                }
            }
        }
        if(element.nodeName.toLowerCase() == 'a'){
            // check if has href attribute
            if(element.hasAttribute("href")){
                console.log("href found: " + element.getAttribute('href'));
                event['link'].push(element.getAttribute("href"));
            }
        }
    };

    return JSON.stringify(event);
}
    '''
    result = await page.evaluate(js_getevent_func)
    # print("js_getevent_func = {}".format(result))
    result = json.loads(result)
    # result = await page.evaluate('get_event()')
    # print('found something')
    # print(result)
    return result

async def hook_console(console):
    # print("console.text-------------- {}".format(console.text))
    pass







class HeadlessCrawler(object):
    '''
    this class aim to use headless chrome to spider some website
    based on python3.6 and pyppeteer
    还没想好是hook response, 还是hook requests
    '''
    def __init__(self, wsaddr, url, cookie=None, depth=1):
        '''
        后续可以添加访问黑名单,css,img,zip,and so on
        :param: wsaddr, ws地址，后期多个headless chrome，可以选择其中一个
        :param: url, 待爬取URL,
        :param: cookie, 待爬取URL的cookie, 格式如下, 可通过EditThisCookie chrome插件来导出
                [
                {
                    "domain": "testphp.vulnweb.com",
                    "hostOnly": true,
                    "httpOnly": false,
                    "name": "login",
                    "path": "/",
                    "sameSite": "no_restriction",
                    "secure": false,
                    "session": true,
                    "storeId": "0",
                    "value": "test%2Ftest",
                    "id": 1
                }
                ]
        '''
        self.url = url
        self.pattern = set()
        self.parsed_url = urlparse.urlparse(url)
        self.crawled_url = set() # 已经爬取过的URL
        self.collect_url = [] # 收集到的URL， 包括 item是：{'method'， 'url', 'data', 'headers'}
        self.cookie = cookie # cookies
        self.wsaddr = wsaddr   # websocket addr
        self.event = [] # event 事件
        self.depth = depth
        self.headers = {}
        self.reponse_url = []
        self.scheme = urlparse.urlparse(self.url).scheme
        # print('self.wsaddr')


    async def _init_page(self):
        try:
            self.brower = await connect(browserWSEndpoint=self.wsaddr)
            self.page = await self.brower.newPage()
            await self.page.setRequestInterception(True)
            #self.page.on('domcontentloaded', await hook_window(self.page))
            self.page.on('load',await mutationobserver(self.page))
            self.page.on('dialog', dismiss_dialog)
            self.page.on('error', hook_error)
            self.page.on('request', self.hook_request)
            self.page.on('console', hook_console)
            self.page.on('response', self.hook_response)
        except Exception as e:
            print("[_init_page] [Error] {}".format(repr(e)))
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            # traceback.print_exception(e)

    async def _close(self):
        await self.page.close()
        # await self.brower.close()


    async def hook_response(self, response):
        # 监听响应，并保存至mongo里
        pass


    def add_to_collect(self, item):
        if (item['url'].find('javascript') > -1) or (item['url'].find('about') > -1) or (item['url'].find('mailto') > -1):
            pass
        elif item in self.collect_url:
            pass
        else:
            self.collect_url.append(item)


    async def FetchBaseUrl(self, html):
        soup = bs(html, 'html.parser')
        base_tags = soup.find_all('base')
        for tag in base_tags:
            if tag.has_attr('href'):
                self.based_url = tag['href']
                break
        else:
            self.based_url = self.url


    async def hook_request(self, request):
        '''
        hook the request, dont know if xmlhttprequest has been hooked
        '''
        # print('request.redirectChain = {}'.format(request.redirectChain))
        image_raw_response = ('SFRUUC8xLjEgMjAwIE9LCkNvbnRlbnQtVHlwZTogaW1hZ2UvcG5nCgqJUE5HDQoaCgAAAA1JSERSAAAAAQ'
                      'AAAAEBAwAAACXbVsoAAAAGUExURczMzP///9ONFXYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAKSURBVAiZY'
                      '2AAAAACAAH0cWSmAAAAAElFTkSuQmCC')
        if request.resourceType == 'image':
            #print("request.recourceType=image, url={}".format(request.url))
            await request.respond({
                'status': 200,
                'contentType': 'image/png',
                'body': image_raw_response
              })
        elif request.resourceType in ['media', 'websocket']:
            await request.abort()
        else:
            if request.url in self.crawled_url:
                #print("request.crawled_url={}".format(request.url))
                await request.abort()
            else:
                # print('hooked Url: {}'.format(request.url))
                if not self.headers:
                    self.headers = request.headers
                #request.headers['Cookie'] = self.cookie
                #print(request.headers)
                item = {'depth': self.depth, 'url': request.url, 'method': request.method, 'data': request.postData, 'headers': request.headers, 'request':True}
                self.add_to_collect(item)
                # await asyncio.gather(
                #     self.page.waitForNavigation({"waitUntil":"networkidle0"}),
                #     request.continue_()
                # )
                await request.continue_()


    def validUrl(self, url):
        '''
        对URL进行标准化
        '''
        final_url = ''
        url = url.strip()
        if url.startswith('http://') or url.startswith('https://'): # http://www.iqiyi.com
            final_url = url
        elif url.startswith('//'):  # //www.iqiyi.com
            final_url = self.scheme  + ':' + url
        # elif url.startswith('/'): # /test.php
        #     final_url = self.url.rstrip('/') + url
        else: # test.php, ../test.php
            # origin_path = self.parsed_url.path
            # target_path = os.path.join(origin_path, url)
            final_url = urlparse.urljoin(self.based_url, url)
        #print("final_url: {}".format(final_url))
        return final_url


    async def FillInputAndSelect(self):
        '''
        看了一下，没有发现pyppeteer有获取dom树节点的api，那么只能用evaluate来执行js，填充命令了
        选择input标签，判断填的类型，填内容
        点击radio,checkbox,和select
        '''
        js_fillinput_str = '''function fillinput(){
            var inputs = document.querySelectorAll("input");
            for(var i = 0; i < inputs.length; i++){
                inp = inputs[i];
                if (['text','search'].indexOf(inp['type'].toLocaleLowerCase()) > -1){
                    // username
                    if ('value' in inp && inp['value'] != ''){
                        //console.log("value not empty, continue");
                        continue;
                    };
                    if (inp.name.indexOf('user') > -1){
                        //console.log('input username');
                        // 这里可以传入用户名
                        inp.value = 'what_ever_a';
                    }else if (inp.name.indexOf('email') > -1){
                        // 传入邮箱
                        inp.value = 'fakeuseremail@163.com';
                    }else if(inp.name.indexOf('phone') > -1){
                        // 传入手机号
                        inp.value = '13800008877';
                    }else{
                        // 剩下的就可以随便了
                        inp.value = 'test text';
                    }

                }else if (inp['type'] == 'password'){
                    inp.value = 'test password';
                }else if (inp['type'] == 'radio'){
                    //console.log('123123123123');
                    inp.checked=true;
                }else if (inp['type'] == 'checkbox'){
                    //console.log('123123123123');
                    inp.checked=true;
                }
            }

            var selects = document.getElementsByTagName('select');
            for(var i=0; i<selects.length; i++){
                var s = selects[i];
                for(var j=0; j<s.length; j++){
                    var item = s[j];
                    //console.log(item.text);
                    item.selected=true;
                }
            }
        }
        '''
        await self.page.evaluate(js_fillinput_str)


    def sameOrign(self, url):
        '''
        判断是否是同一域名，或者子域名.
        这里还可以优化成是绝对相等或者包含子域名等不同的级别
        '''
        url_netloc = urlparse.urlparse(url).netloc
        if self.parsed_url.netloc.find(url_netloc) > -1:
            return True
        else:
            return False



    async def getalllink(self, html):
        '''
        这部分是不点击即可获取的A标签中的链接, 暂时不处理img, link, 和 script的标签
        '''
        soup = bs(html, 'html.parser')
        base_tags = soup.find_all('a')
        for tag in base_tags:
            if tag.has_attr('href'):
                url = tag['href']
                # pass the javascript:
                if url.startswith('javascript'):
                    #print('url.startwith.javascript: {}'.format(url))
                    #await self.page.evaluate(url)
                    continue
                url = self.validUrl(url)
                if not self.sameOrign(url):
                    continue
                # 这里的headers后续再完善
                item = {'method': 'GET', 'headers':self.headers, 'data':None, 'url':url, 'depth': self.depth}
                self.add_to_collect(item)





    async def spider(self):
        try:
            await self._init_page()
            # print('init page donw----------------------')
            #await self.page.goto(self.url, {'waitUntil':'load', 'timeout':15000})
            # 判断cookie的格式
            try:
                pass

                if self.cookie is None:
                    pass
                elif type(self.cookie) is list: # list 格式
                    #print("cookie is list")
                    for cookie in self.cookie:
                        await self.page.setCookie(cookie)
                else: # json格式
                    cookie = json.loads(self.cookies)
                    if type(cookie) == list:
                        await self.page.setCookie(*cookie)
                    elif type(cookie) == dict:
                        await self.page.setCookie(cookie)
                    else:
                        raise Exception('cookie format error')

            except Exception as e:
                print('[ERROR]  [HeadlessCrawler][spider][setCookies]  setCookies Error, please check your cookies format')
                print(e)
                return

            # 访问URL
            await self.page.goto(self.url, {'waitUntil':'load', 'timeout':20000})
            # print(await self.page.cookies())
            #await self.page.evaluate(
            #        'document.cookie = "QC005=2e297c2e4c4776d707615ef8c2f843a8; QC006=z9mc893qf3lvb9lj917avu9r; T00404=d9f71cc5e254f427d8ad8deeeca112dd; QC173=0; P00004=-898887952.1530510174.aab7357f0a; QC160=%7B%22u%22%3A%2218510725391%22%2C%22lang%22%3A%22%22%2C%22local%22%3A%7B%22name%22%3A%22%E4%B8%AD%E5%9B%BD%E5%A4%A7%E9%99%86%22%2C%22init%22%3A%22Z%22%2C%22rcode%22%3A48%2C%22acode%22%3A%2286%22%7D%2C%22type%22%3A%22p1%22%7D; QC007=DIRECT; QC008=1530510165.1530510165.1531102822.2; nu=0; QP001=1; T00700=EgcI18DtIRAB; QC001=1; QC021=%5B%7B%22key%22%3A%22playlist%22%7D%5D; QC124=1%7C0; P00001=a5WUo0Wvm1aZ5IFw2uYzUqkOZK56NuRz5LLCEYyv1LGdRvZm2m14nPFUgfGYKvK5RDCHP70; P00003=1444386669; P00010=1444386669; P01010=1531497600; P00007=a5WUo0Wvm1aZ5IFw2uYzUqkOZK56NuRz5LLCEYyv1LGdRvZm2m14nPFUgfGYKvK5RDCHP70; P00PRU=1444386669; P00002=%7B%22uid%22%3A%221444386669%22%2C%22pru%22%3A1444386669%2C%22user_name%22%3A%2218510725391%22%2C%22nickname%22%3A%22shinpachi8%22%2C%22pnickname%22%3A%22shinpachi8%22%2C%22type%22%3A11%2C%22email%22%3A%22xiaoyan_jia1%40163.com%22%7D; P000email=xiaoyan_jia1%40163.com; QP008=960; QP007=0; QC010=46360036; QC170=0; __dfp=a0a801605d3043494885594bed84b92f81f3025593d0ea319c5e6aa109cffbf99a@1531806166483@1530510166483; QC163=1"'
            #        )
            #await self.page.reload()
            # print("self.page.reload done")
            # cookie = await self.page.cookies()
            # print(cookie)

            # event = await self.page.waitForFunction(js_getevent_func, {'timeout':'5000'})
            #print(await self.page.content())
            #print(event.toString())
            #await self._close()
            # return

            # 首先获取a 中的href值，等到所有的事件都触发了，再收集一次
            html = await self.page.content()
            await self.FetchBaseUrl(html)
            # await self.getalllink(html)

            # 获取frame
            frames = self.page.frames
            for frame in frames:
                url = self.validUrl(frame.url)
                if self.sameOrign(url):
                    item = {'method': 'GET', 'data':None, 'headers':self.headers, 'url': url, 'depth': self.depth}
                    self.add_to_collect(item)

            # print("---------------- frame done-------------------")
            # print(self.collect_url)
            # print("----------------------------------------------")
            # 获取事件:
            events = await get_event(self.page)
            for key in events:
                if key == 'link':
                    for url in events[key]:
                        # print("event:links:  {}".format(url))
                        url = self.validUrl(url)
                        item = {'method': 'GET', 'data':None, 'headers':self.headers, 'url': url, 'depth': self.depth}
                        self.add_to_collect(item)
                else:
                    self.event.extend(events[key])



            # 填充表单
            await self.FillInputAndSelect()

            # print("---------------- fill input done-------------------")
            # print(self.collect_url)
            # print("----------------------------------------------")
            # 获取事件:
            events = await get_event(self.page)
            for key in events:
                if key == 'link':
                    for url in events[key]:
                        url = self.validUrl(url)
                        if self.sameOrign(url):
                            item = {'method': 'GET', 'data':None, 'headers':self.headers, 'url': url, 'depth': self.depth}
                            self.add_to_collect(item)
                else:
                    self.event.extend(events[key])

            self.event = list(set(self.event))
            # 点击button
            input_button = await self.page.querySelectorAll("input[type='button']")
            for button in input_button:

                await button.press('ArrowLeft') # after click found the on event

            buttons = await self.page.querySelectorAll("button")
            for button in buttons:
                # print(button)
                await button.press('ArrowLeft')


            #  执行事件
            for e in self.event:
                # print(repr(e))
                e = e.strip()
                try:
                    await self.page.waitForFunction(e, {"timeout": 5000})
                except:
                    print("exec {} failed".format(repr(e)))


            # print("---------------- event done-------------------")
            # print(self.collect_url)
            # print("----------------------------------------------")

            # 获取dom变更的link
            window_link = await self.page.evaluate('window.LINKS', force_expr=True)
            if window_link:
                window_link = list(set(window_link))
                #print(window_link)
                for link in window_link:
                    if link is None or link.strip() == '#':
                        continue
                    # print("---------link--------------")
                    # print(link)
                    if link.startswith("javascript:"):
                        try:
                            await self.page.waitForFunction(link, {"timeout": 5000})
                        except Exception as e:
                            print("exec {} failed".format(repr(e)))

                        continue
                    if link.startswith("about") or link.startswith('mailto'):
                        continue
                    url = self.validUrl(link)
                    if self.sameOrign(url):
                        item = {'method': 'GET', 'headers':self.headers, 'url':url, 'data':None, 'depth': self.depth}
                        self.add_to_collect(item)

            # 获取window.location的 link
            window_locations = await self.page.evaluate('''window.Redirects''')
            if window_locations:
                window_locations = list(set(window_locations))
                for link in window_locations:

                    if link and link.startswith("javascript:"):
                        try:
                            await self.page.waitForFunction(link, {"timeout": 5000})
                        except:
                            print("exec {} failed".format(repr(e)))

                        continue
                    if link and link.startswith("about") or link.startswith('mailto'):
                        continue

                    url = self.validUrl(link)
                    if self.sameOrign(url):
                        item = {'method': 'GET', 'headers':self.headers, 'url':url, 'data':None, 'depth': self.depth}
                        self.add_to_collect(item)


            html = await self.page.content()
            await self.getalllink(html)
            # print("---------------- dom, windows.location done-------------------")
            # print(self.collect_url)
            # print("----------------------------------------------")
#            await self._close()
            # window_link = await self.page.evaluate('window.LINKS', force_expr=True)
            # print(window_link)
            await self._close()

        except Exception as e:
            print('[test] [Error] {}'.format(repr(e)))
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            await self._close()



async def main():
    wsaddr = 'ws://10.127.21.237:9222/devtools/browser/f3f68d37-aabb-43b7-9d75-986a8be08e2d'
    iqiyi_cookie = None
    with open('iqiyi_cookie.json', 'r') as f:
        iqiyi_cookie = json.load(f)

    cookie = []
    for i in iqiyi_cookie:
        item = {}
        item['name'] = i['name']
        item['value'] = i['value']
        item['expires'] =  60 * 60 * 60
        item['domain'] = i['domain']
        print(item)
        cookie.append(i)
    #cookie = '''P00002=%7B%22uid%22%3A%221444386669%22%2C%22pru%22%3A1444386669%2C%22user_name%22%3A%2218510725391%22%2C%22nickname%22%3A%22shinpachi8%22%2C%22pnickname%22%3A%22shinpachi8%22%2C%22type%22%3A11%2C%22email%22%3A%22xiaoyan_jia1%40163.com%22%7D; P00003=1444386669; P00004=-898887952.1530510174.aab7357f0a; P00010=1444386669; P000email=xiaoyan_jia1%40163.com; P00PRU=1444386669; P01010=1531497600; QC005=2e297c2e4c4776d707615ef8c2f843a8; QC006=z9mc893qf3lvb9lj917avu9r; QC007=DIRECT; QC008=1530510165.1530510165.1531102822.2; QC021=%5B%7B%22key%22%3A%22playlist%22%7D%5D; QC124=1%7C0; QC160=%7B%22u%22%3A%2218510725391%22%2C%22lang%22%3A%22%22%2C%22local%22%3A%7B%22name%22%3A%22%E4%B8%AD%E5%9B%BD%E5%A4%A7%E9%99%86%22%2C%22init%22%3A%22Z%22%2C%22rcode%22%3A48%2C%22acode%22%3A%2286%22%7D%2C%22type%22%3A%22p1%22%7D; QC170=0; QC173=0; QP001=1; QP007=0; QP008=960; T00404=d9f71cc5e254f427d8ad8deeeca112dd; T00700=EgcI18DtIRAB; QC010=230539999; __dfp=a0a801605d3043494885594bed84b92f81f3025593d0ea319c5e6aa109cffbf99a@1531806166483@1530510166483; P00001=e42m1S8Z2RIMm2m3QxiWhHAbEm1nyG2GF54yq76z8bNiLR8bnMXK64JUKn965NScMC9i8o48; P00007=e42m1S8Z2RIMm2m3QxiWhHAbEm1nyG2GF54yq76z8bNiLR8bnMXK64JUKn965NScMC9i8o48'''

    print(wsaddr)
    a = HeadlessCrawler(wsaddr, 'http://www.iqiyi.com/', cookie=cookie)
    #a = HeadlessCrawler(wsaddr, 'https://mp.iqiyi.com/')
    await a.spider()
    test = a.collect_url
    test = [json.dumps(item) for item in test]
    with open('result.json', 'w') as f:
        json.dump(list(set(test)), f)
    # with open('fetched_url.json', 'w') as f:
     #     json.dump((a.fetched_url), f)

# asyncio.get_event_loop().run_until_complete(main())
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main())
    print('start........')
    try:
        loop.run_until_complete(task)
    except Exception as e:
        #print(asyncio.gather(*asyncio.Task.all_tasks()).cancel())
        loop.stop()
        loop.run_forever()
    finally:
        loop.close()
    '''
    asyncio.get_event_loop().run_until_complete(main())
    '''
