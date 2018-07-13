#!/usr/bin/env python
# coding=utf-8

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


                        var a_tag = record.addedNodes[i].querySelectorAll('a');

                        for(var j = 0; j < a_tag.length; ++j){
                            var a = a_tag[j];
                            if (a.src || a.href) {
                                window.LINKS.push(a.src || a.href);
                                //console.log('Mutation AddedNodes:', a.src || a.href);
                                };
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

hook_open  = """() => {

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


if __name__ == '__main__':
    print(js_getevent_func)
