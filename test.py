import asyncio
import pyppeteer
import time
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
    jsfunc_str_exec = '''monitor()'''
    result2 = await page.evaluate(jsfunc_str_exec)
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
    nodes = document.all;
    for(j = 0;j < nodes.length; j++) {
        attrs = nodes[j].attributes;
        for(k=0; k<attrs.length; k++) {
            if (attrs[k].nodeName.startsWith('on')) {
                console.log(attrs[k].nodeName, attrs[k].nodeValue);
            }
        }
    }
}
    '''
    result = await page.evaluate(js_getevent_func)
    result = await page.evaluate('get_event()')
    print('found something')
    print(result)
    return result

async def hook_console(console):
    print("console.text--------------")
    print(console.text)




async def main():
    brower = await connect(browserWSEndpoint='ws://0.0.0.0:9222/devtools/browser/acfde542-a560-464e-bcb3-7ea19026c12d')
    #brower = await launch()
    #print(type(brower))
    page = await brower.newPage()
    await page.setRequestInterception(True)
    page.on('load',await mutationobserver(page))
    await get_event(page)
    page.on('dialog', dismiss_dialog)
    page.on('request', hook_request)
    page.on('console', hook_console)
    page.on('response', hook_response)
    #await page.goto('https://github.com')
    #await page.setCookie(*cookie)
    #await page.goto('https://github.com/settings/emails', waitUntil='networkidle0')
    #title = await page.title()
    #print(title)
    # test on testphp.vulnweb.com/AJAX/index.php

    await page.goto('http://testphp.vulnweb.com/AJAX/index.php', waitUntil='networkidle0')
    title = await page.title()
    print(title)
    await page.evaluate('console.log("console log hook test")')
    htmlhandle = await page.querySelectorAll('a')
    for i in htmlhandle:
        await asyncio.wait([
            page.waitForNavigation(waitUntil='networkidle0'),
            i.click(),
        ])
        await i.click()
        print(await page.evaluate('''()=> {return window.nodes}'''))

    print(await page.evaluate('''()=> {return window.LINKS}'''))

    print('--------click all a tag done-----------')

    html = await page.content()
    (links, onevents, jsfunc) = await exec_events_a(page, html, 'a')
    print(links)
    print(onevents)
    print(jsfunc)
    for item in onevents:
        #htmlhandle = await page.querySelector("{}[{}*={}]".format(item['tagname'], item['oneventname'], item['oneventvalue']))
        #await htmlhandle.click()
        await asyncio.wait([
            page.waitForNavigation(waitUntil='networkidle0'),
            page.evaluate(item['oneventvalue'])
            ])

    for item in jsfunc:
        await asyncio.wait([
            page.waitForNavigation(waitUntil='networkidle0'),
            page.evaluate(item)
            ])

    print('------------execute jsfunc done-----------')
    print('------------reload html-----------')
    html = await page.content()
    (links, onevents, jsfunc) = await exec_events_a(page, html, 'a')
    print(links)
    print(onevents)
    print(jsfunc)

    print('--------evaluate done---------------')
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
    await elements[0].click()


    time.sleep(3)
    #await brower.close()
    #page.close()
    #brower.close()


asyncio.get_event_loop().run_until_complete(main())

