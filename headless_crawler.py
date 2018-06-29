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
from bs4 import BeautifulSoup as bs
from pyee import EventEmitter

#from pyppeteer.network_manager import Request

'''
cookie = {'_ga': 'GA1.2.1789303611.1527950632',
    '_gh_sess':     'a0MrNVVTU1BHcGRzcTlhRFUrY0hUS3hEVXd4Q1cwNGdrSjJhREFNcmIzVUR2VitHVVRVS2NPUGxFU3NIaENYV1F5NU44WndpT3NvanNZMWZPUFRKSDZ1SVROT0JtbTFaMzZDM0RTQ0p6K2swR1RtdUdkallWRlVPcVZWNThucjJYcms1UjRXZjRkNGlFSDNkcXFpb3ZYUlBvSmpmeW9sTFRtMlluRXduN05JQ2I1T244T2dIRVBkWlcxZWxzMWJTWUJsdHgrOGhhakhrMDdyTXFIUlo5WmVFRlZ0TVpmend3U2o5RCtqSE05U1hFanlpeFJvTU9wdFNaODVNQlllcWRWWnA2Ujh3eWpIcEhacDRqM0RXS0d2blJ2Y2hzMmUwNkFkcUs2ZXYybUlRVUZnQmxlYk5JL3dSOGNtbzVZdHkwaU96bkJQU3lXN3pLdTljb2FvWWNnPT0tLTRPUElrZ3FSenUyVHNFTC9lejBPeFE9PQ%3D%3D--eef41280eaaad02932850454ed45288c1194bf94',
    '_octo': 'GH1.1.727260551.1527950632',
    'dotcom_user': 'Shinpachi8',
    'logged_in': 'yes',
    'user_session': 'NqtE4KhUYKb_p8ib1W2XhRgTDNBmt78ZaOYSySh_QL6u9M4Q'}
'''

cookie = [{'name': 'logged_in', 'value': 'yes'}, {'name': '_ga', 'value': 'GA1.2.1789303611.1527950632'}, {'name': '_octo', 'value': 'GH1.1.727260551.1527950632'}, {'name': 'user_session', 'value': 'NqtE4KhUYKb_p8ib1W2XhRgTDNBmt78ZaOYSySh_QL6u9M4Q'}, {'name': 'dotcom_user', 'value': 'Shinpachi8'}, {'name': '_gh_sess', 'value':
    'a0MrNVVTU1BHcGRzcTlhRFUrY0hUS3hEVXd4Q1cwNGdrSjJhREFNcmIzVUR2VitHVVRVS2NPUGxFU3NIaENYV1F5NU44WndpT3NvanNZMWZPUFRKSDZ1SVROT0JtbTFaMzZDM0RTQ0p6K2swR1RtdUdkallWRlVPcVZWNThucjJYcms1UjRXZjRkNGlFSDNkcXFpb3ZYUlBvSmpmeW9sTFRtMlluRXduN05JQ2I1T244T2dIRVBkWlcxZWxzMWJTWUJsdHgrOGhhakhrMDdyTXFIUlo5WmVFRlZ0TVpmend3U2o5RCtqSE05U1hFanlpeFJvTU9wdFNaODVNQlllcWRWWnA2Ujh3eWpIcEhacDRqM0RXS0d2blJ2Y2hzMmUwNkFkcUs2ZXYybUlRVUZnQmxlYk5JL3dSOGNtbzVZdHkwaU96bkJQU3lXN3pLdTljb2FvWWNnPT0tLTRPUElrZ3FSenUyVHNFTC9lejBPeFE9PQ%3D%3D--eef41280eaaad02932850454ed45288c1194bf94'}]


ee = EventEmitter()
@ee.on('onclick')
async def eeclick(page, jsstr):
    await page.evaluate(jsstr)

async def mutationobserver(page):
    '''
    mutation observer the dom change
    '''
    # dismiss the dialog
    # result = await page.evaluate('''()=>123123''')
    jsfunc_str = '''monitor=()=>{
    window.EVENTS = [];
    window.EVENTS_HISTORY = [];
    window.LINKS = [];
    window.nodes = [];
    var MutationObserver = window.MutationObserver;
    var callback = function (records) {
        records.forEach(function (record) {
            console.info('Mutation type: ', record.type);
            if (record.type === 'attributes') {
                console.info("Mutation attributes:", record.target[record.attributeName]);
                window.LINKS.push(record.target[record.attributeName]);
            } else if (record.type === 'childList') {
                for (var i = 0; i < record.addedNodes.length; ++i) {
                    var node = record.addedNodes[i];
                    if (node.src || node.href) {
                        window.LINKS.push(node.src || node.href);
                        console.info('Mutation AddedNodes:', node.src || node.href);

                }
            }
        }});
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
            console.info('addEventListener:', a, this);
        }
        this._addEventListener(a, b, c);
    };

}
    '''
    print('dirpage')
    print(dir(page))
    result = await page.evaluate(jsfunc_str)
    # jsfunc_str_exec = '''monitor()'''
    # result2 = await page.evaluate(jsfunc_str_exec)
    print('获取事件被触发后的节点属性变更更信息')
    print(result)


async def hook_request(request):
    '''
    hook the request, dont know if xmlhttprequest has been hooked
    '''
    if request.resourceType in ['image', 'media', 'websocket']:
        await request.abort()
    else:
        print('hooked Url: {}'.format(request.url))
        await request.continue_()


async def hook_response(resp):
    print("resp.url = {}".format(resp.url))


async def dismiss_dialog(dialog):
    print("dialog found")
    await dialog.accept()

async def exec_events_a(page, html, tag):
    #a_handle = await page.querySelectorAll('a')
    soup = bs(html, 'html.parser')
    # base_url_tag = soup.find_all('base')
    # if base_url_tag:

    a_tag = soup.find_all(tag)

    links = []
    onevents = []
    jsfunc = []
    for a in a_tag:
        print('-----------------------')
        # pass the logout likes
        if 'logout' in a:
            continue
        #print(dir(a))

        attrs = a.attrs
        for key in attrs:
            if key in ['href', 'src']:
                if attrs[key] in ['javascript:void(0)', '#']:
                    # ignore the void press
                    continue
                elif attrs[key].startswith('http'):
                    # judge if the attrs][key] is valid through a function like : validurl()
                    links.append(attrs[key])
                else:
                    jsfunc.append(attrs[key])
            elif key.startswith('on'):
                classname = attrs['class'] if 'calss' in attrs else ''
                idname = attrs['id'] if 'id' in attrs else ''
                oneventname = key
                uniq_events = {'classname': classname, 'idname': idname, 'oneventname': oneventname, 'tagname': 'a', 'oneventvalue': attrs[key] }
                onevents.append(uniq_events)

                #if key == 'onclick':
                #    ee.emit(page, attrs[key])
                #    print('ee click')
            else:
                continue

    return (links, onevents, jsfunc)




async def get_event(page):
    js_getevent_func = '''get_event = ()=>{
    var event = {};
    var nodes = document.all;
    for(j = 0;j < nodes.length; j++) {
        attrs = nodes[j].attributes;
        for(k=0; k<attrs.length; k++) {
            if (attrs[k].nodeName.startsWith('on')) {
                if(attrs[k].nodeName in event){
                    if(attrs[k].nodeValue in event[attrs[k].nodeName]){
                        console.log(attrs[k].nodeName, attrs[k].nodeValue + ' Already Add in List');
                    }else{
                        event[attrs[k].nodeName].unshift(attrs[k].nodeValue);
                    }
                }else{
                    event[attrs[k].nodeName] = [];
                    event[attrs[k].nodeName].unshift(attrs[k].nodeValue);
                }
            }
        }
    }
    return JSON.stringify(event);
}
    '''
    result = await page.evaluate(js_getevent_func)
    result = json.loads(result)
    # result = await page.evaluate('get_event()')
    # print('found something')
    # print(result)
    return result

async def hook_console(console):
    print("console.text--------------")
    print(console.text)




def md5(str):
    pass




class FrameDeal(object):
    '''
    流程上来说应该先填写form, 选择select再点击on事件
    '''
    def __init__(self, frame, fetched_url, urlqueue, pattern, timeout=10): # timeout暂定
        self.frame = frame
        self.fetched_url = fetched_url # {'static':'不触发JS时的链接', 'xhr': 'js触发的链接'} 
        self.event = []
        self.js_func_str = set()
        self.url = frame.url
        self.based_url = ''
        self.pattern = pattern
        self.urlqueue = urlqueue # 把所有的url都加到queue里
        self.scheme = urlparse.urlparse(self.url).scheme
        self.netloc = urlparse.urlparse(self.url).netloc



    async def FetchBaseUrl(self):
        html = await self.frame.content()
        soup = bs(html, 'html.parser')
        base_tags = soup.find_all('base')
        for tag in base_tags:
            if tag.has_attr('href'):
                self.based_url = tag['href']
                break
        else:
            self.based_url = self.url


    def validUrl(self, url):

        final_url = ''
        if url.startswith('http://') or url.startswith('https://'): # http://www.iqiyi.com
            final_url = url
        elif url.startswith('//'):  # //www.iqiyi.com
            final_url = self.scheme  + ':' + url
        elif url.startswith('/'): # /test.php
            final_url = self.based_url.rstrip('/') + url
        # elif url.startswith(".."): # ../test.php
        #     rindex = self.based_url.rindex('/')
        #     final_url = self.based_url[:rindex+1] + url
        else: # test.php, ../test.php
            rindex = self.based_url.rindex('/')
            final_url = self.based_url[:rindex+1] + url
            # final_url = self.based_url.rstrip('') + "" + url

        return final_url


    def sameOrign(self, url):
        '''
        判断同源
        '''
        url_netloc = urlparse.urlparse(url).netloc
        if self.netloc.find(url_netloc) > -1:
            return True
        else:
            return False


    def genPattern(self, url):
        '''
        先简单的把数字替换成digit, 先换成param试一下
        '''
        if '?' in url:
            param = url[url.rindex('?'):]
            pattern = re.sub(r'\d+', '{digit}', param)
        else:
            pattern = url
        return pattern

    async def FetchAHref(self):
        '''
        这部分是不点击即可获取的A标签中的链接, 暂时不处理img, link, 和 script的标签
        '''
        html = await self.frame.content()
        soup = bs(html, 'html.parser')
        base_tags = soup.find_all('a')
        for tag in base_tags:
            if tag.has_attr('href'):
                url = tag['href']
                # pass the javascript:
                if url.startswith('javascript'):
                    self.js_func_str.add(url)
                    continue
                url = self.validUrl(url)
                if not self.sameOrign(url):
                    continue
                self.fetched_url['static'].append(url)
                pattern = self.genPattern(url)
                print('-------------------------------------------\n')
                print('[PATTERN]: {}'.format(pattern))
                print('-------------------------------------------\n')
                if pattern is not None and pattern in self.pattern:
                    continue
                else:
                    self.pattern.add(pattern)
                    print('-------------------------------------------\n')
                    print('[ADD TO URLQUEUE]: {}'.format(url))
                    print('-------------------------------------------\n')
                    await self.urlqueue.put(url)


    async def FillInputAndSelect(self):
        '''
        看了一下，没有发现pyppeteer有获取dom树节点的api，那么只能用evaluate来执行js，填充命令了
        '''
        js_fillinput_str = '''function fillinput(){
        var inputs = document.querySelectorAll("input")
        for(var i = 0; i < inputs.length; i++){
            inp = inputs[i];
            if ('value' in inp && inp['value'] != ''){
                console.log("value not empty, continue");
                continue;
            }
            if (['text','search'].indexOf(inp['type'].toLocaleLowerCase()) > -1){
                // username
                if (inp.name.indexOf('user') > -1){
                    console.log('input username');
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
            }
        }
    }
        '''
        await self.frame.evaluate(js_fillinput_str)

    async def start(self):
        await self.FetchBaseUrl()
        await self.FetchAHref()
        await self.FillInputAndSelect()

        # frame input[type="buuton"]
        input_button = await self.frame.querySelectorAll("input[type='button']")
        for button in input_button:
            await button.click() # after click found the on event
            onevent = await get_event(self.frame) # {'onclick':[xxx,xxx], 'onmouseever':[xx,xx]}
            for key in onevent:
                if key.find('click') > -1:
                    self.event.extend(onevent[key])


        # click js func
        for js_func in self.js_func_str:
            await self.frame.evaluate(js_func)
            onevent = await get_event(self.frame) # {'onclick':[xxx,xxx], 'onmouseever':[xx,xx]}
            for key in onevent:
                if key.find('click') > -1:
                    self.event.extend(onevent[key])

        self.event = list(set(self.event))
        for func in self.event:
            await self.frame.evaluate(func)


        buttons = await self.frame.querySelectorAll("button")
        for button in buttons:
            # await asyncio.wait([
            #     self.page.waitForNavigation(waitUntil='networkidle0'),
            #     button.click(),
            # ])
            await button.click()
            if self.frame.url != self.url:
                print(self.frame.url + "frame.url")
                print(self.url + "self.url")
                # await asyncio.wait([
                #     self.frame.waitForNavigation(waitUntil='networkidle0'),
                #     self.frame.goBack(),
                # ])
                # await self.frame.goBack()






class HeadlessCrawler(object):
    '''
    this class aim to use headless chrome to spider some website
    based on python3.6 and pyppeteer 
    '''
    def __init__(self, url, cookies=None):
        '''
        后续可以添加访问黑名单,css,img,zip,and so on
        '''
        self.url = url
        self.executed_event = set() # 执行过的event
        self.requestd_url = set() # 请求过的url
        self.collected_url = set()
        self.urlqueue = asyncio.Queue()
        self.fetched_url = {'static':[], 'xhr':[]}
        self.pattern = set()
        

    async def _init_page(self):
        try:
            self.brower = await connect(browserWSEndpoint='ws://127.0.0.1:9222/devtools/browser/a920d29f-f918-4a65-9899-1807e3cd8e24')
            self.page = await self.brower.newPage()
            await self.page.setRequestInterception(True)
            self.page.on('load',await mutationobserver(self.page))
            await get_event(self.page)
            self.page.on('dialog', dismiss_dialog)
            self.page.on('request', self.hook_request)
            self.page.on('console', hook_console)
            self.page.on('response', hook_response)
        except Exception as e:
            print("[_init_page] [Error] {}".format(repr(e)))
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            # traceback.print_exception(e)

    async def _close(self):
        await self.page.close()
        await self.brower.close()

    async def hook_request(self, request):
        '''
        hook the request, dont know if xmlhttprequest has been hooked
        '''
        if request.resourceType in ['image', 'media', 'websocket']:
            await request.abort()
        else:
            
            if request.url in self.requestd_url:
                await request.abort()
            else:
                print('hooked Url: {}'.format(request.url))
                item = {'url': request.url, 'method': request.method, 'postData': request.postData}
                self.requestd_url.add(json.dumps(item))
                await request.continue_()


    async def test(self):
        try:
            await self._init_page()
            await self.page.goto('http://10.127.21.237/wivet/pages/7.php', waitUntil='networkidle0')
            title = await self.page.title()
            print(title)
            await self.page.evaluate('console.log("console log hook test")')
            # fech a link



            frames = self.page.frames
            print(dir(frames[0]))
            print("there total {} frames".format(len(frames)))
            for frame in frames:
                obj = FrameDeal(frame, self.fetched_url, self.urlqueue, self.pattern)
                await obj.start()
                print("after obj.start, self.fetched_url={}".format(self.fetched_url))

            while not self.urlqueue.empty():
                try:
                    url = await self.urlqueue.get()
                    print('-------------------------------------------\n')
                    print('[URL]: {}'.format(url))
                    print('-------------------------------------------\n')
                    await self.page.goto(url, waitUntil='networkidle0')
                    title = await self.page.title()
                    print(title)
                    await self.page.evaluate('console.log("console log hook test")')
                    # fech a link

                    frames = self.page.frames
                    print(dir(frames[0]))
                    print("there total {} frames".format(len(frames)))
                    for frame in frames:
                        obj = FrameDeal(frame, self.fetched_url, self.urlqueue, self.pattern)
                        await obj.start()
                        print("after obj.start, self.fetched_url={}".format(self.fetched_url))
                except Exception as e:
                    print("[Exception] [fetched_url.static] {}".format(repr(e)))

            window_link = await self.page.evaluate('''()=>{return window.LINKS}''')
            print('---------AT LAST, WINDOW.LINKS-------------')
            print(window_link)

            # html = await self.page.content()
            # # print(html)
            # (links, onevents, jsfunc) = await exec_events_a(self.page, html, 'a')
            # for link in links:
            #     self.collected_url.add(link)

            # print("links----------\n{}".format(links))
            # print("onevents----------\n{}".format(onevents))
            # print("jsfunc----------\n{}".format(jsfunc))
            # print(self.collected_url)
            # htmlhandle = await self.page.querySelectorAll('a')
            # for i in htmlhandle:
            #     # await asyncio.wait([
            #     #     self.page.waitForNavigation(waitUntil='networkidle0'),
            #     #     i.click(),
            #     # ])
            #     print(dir(i))
            #     await i.click()
            #     await get_event(self.page)
            #     # await i.click()
            #     print(await self.page.evaluate('''function(){return window.nodes}''', force_expr=False))

            # print(await self.page.evaluate('''function(){return window.LINKS}''', force_expr=False))

            print('--------click all a tag done-----------')
            # await self._close()
            await self.page.close()
            # html = await page.content()
            # (links, onevents, jsfunc) = await exec_events_a(page, html, 'a')
            # print(links)
            # print(onevents)
            # print(jsfunc)
            # for item in onevents:
            #     #htmlhandle = await page.querySelector("{}[{}*={}]".format(item['tagname'], item['oneventname'], item['oneventvalue']))
            #     #await htmlhandle.click()
            #     await asyncio.wait([
            #         page.waitForNavigation(waitUntil='networkidle0'),
            #         page.evaluate(item['oneventvalue'])
            #         ])

            # for item in jsfunc:
            #     await asyncio.wait([
            #         page.waitForNavigation(waitUntil='networkidle0'),
            #         page.evaluate(item)
            #         ])

            # print('------------execute jsfunc done-----------')
            # print('------------reload html-----------')
            # html = await page.content()
            # (links, onevents, jsfunc) = await exec_events_a(page, html, 'a')
            # print(links)
            # print(onevents)
            # print(jsfunc)

            # print('--------evaluate done---------------')
        except Exception as e:
            print('[test] [Error] {}'.format(repr(e)))
            exc_type, exc_value, exc_traceback_obj = sys.exc_info()
            traceback.print_tb(exc_traceback_obj)
            # traceback.print_exception(e)
        '''
        htmlhandle = await page.querySelectorAll('a')
        print(dir(htmlhandle[0]))
        for i in htmlhandle:
            a_properties = await i.getProperties()
            print('a_properties------------------------')
            print(a_properties)
            a_executionContent = i.executionContext
            print('---------------------')
            print(a_executionContent)
        '''

        #print(elements)
        #print(dir(elements))

async def main():
    a = HeadlessCrawler('http://testphp.vulnweb.com/AJAX/#')
    await a.test()
    with open('result.json', 'w') as f:
        json.dump(list(a.requestd_url), f)

asyncio.get_event_loop().run_until_complete(main())