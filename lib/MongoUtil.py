#!/usr/bin/python
# -*- coding:utf-8 -*-
#
"""
Copyright (c) 2016-2017 twi1ight@t00ls.net (http://twi1ight.com/)
See the file 'doc/COPYING' for copying permission
"""
# from log import logger
from commons improt LogUtil
from settings import MongoConf
from pymongo import MongoClient



class MongoConf(object):
    host = '127.0.0.1'
    port = 27017
    username = None
    password = None

    db = 'tspider'
    # collection
    target = 'target'
    others = 'others'




class MongoUtils(object):
    def __init__(self, conf=mongoconf):
        self.db = mongoconf.db
        self._client = None
        self._target = None
        self._others = None
        self.logger = LogUtil(path='/tmp/mongo_log.log')
        self.connect()

    @property
    def connected(self):
        try:
            self._client.server_info()
            return True
        except:
            self.logger.exception('mongodb connection test excepiton!')
            return False

    def connect(self):
        try:
            self._client = MongoClient('mongodb://{}:{}'.format(mongoconf.host, mongoconf.port),
                                       connect=False)
            self._target = self._client[self.db][mongoconf.target]
            self._others = self._client[self.db][mongoconf.others]
        except:
            self.logger.exception('connect mongodb failed!')

    def save(self, reqdict, is_target=True, check_exists=False):
        if not self._client:
            return

        # should use redis check outside, only set check_exists to True if redis data lost
        # mongodb use too much CPU if no index created on (method, pattern)
        # db.targetresult.ensureIndex({method:1, pattern:1})
        # db.otheresult.ensureIndex({method:1, pattern:1})
        if check_exists and self.exists(reqdict, is_target):
            return
        try:
            handle = self._target if is_target else self._others
            result = handle.insert_one(reqdict)
            if result.acknowledged:
                self.logger.debug('insert success: %s' % str(result.inserted_id))
                return
            self.logger.error('insert failed: %s' % reqdict['url'])
        except:
            self.logger.exception('mongodb save exception!')

    def exists(self, reqdict, is_target=True):
        if not self._client:
            return False
        try:
            query = {'method': reqdict.get('method', ''),
                     'pattern': reqdict.get('pattern', '')}
            handle = self._target if is_target else self._others
            cursor = handle.find(query, limit=1)
            if cursor.count() > 0:
                self.logger.debug('document exists: %s-%s' % (query['method'], query['pattern']))
                return True
            else:
                return False
        except:
            self.logger.exception('mongodb exists excepiton!')
            return False

    def query(self, querystring, fields, is_target=True):
        try:
            handle = self._target if is_target else self._others
            cursor = handle.find(querystring, fields)
            for doc in cursor:
                yield doc
        except:
            self.logger.exception('mongodb query exception!')


if __name__ == '__main__':
    c = MongoUtils()
    c.save({'test': 'test1'})
    print c.exists({'test': 'test1'})
    c.save({'test': 'test2'})
    c.save({'test1': 'test3'})
