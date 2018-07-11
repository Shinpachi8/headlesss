#!/usr/bin/python
# -*- coding:utf-8 -*-
#
"""
Copyright (c) 2016-2017 twi1ight@t00ls.net (http://twi1ight.com/)
See the file 'doc/COPYING' for copying permission
"""
import redis

class RedisConf(object):
    def __init__(self, taskname, db=0):
        self.db = db
        self.taskname = taskname
        self.task_result = taskname + ':result'
        self.task_scanned = taskname + ':scanned'
        self.task_unscan = taskname + ':unscan'
        self.task_pattern = taskname + ':pattern'
        self.



class RedisUtils(object):
    def __init__(self, conf=RedisConf('test')):
        """
        :param tld: scan same top-level-domain subdomains. Scan only subdomain itself when tld=False.
        :param db: redis db number.
        :return: :class:RedisUtils object
        :rtype: RedisUtils
        """
        self.db = conf.db
        self.l_url_unscan =conf.task_unscan
        self.l_url_result = conf.task_result
        self.h_url_scanned = conf.task_scanned
        self.h_url_pattern = conf.task_pattern
        self.redis_client = None
        self.connect()

    @property
    def connected(self):
        try:
            self.redis_client.ping()
            return True
        except:
            logger.exception('connect to redis failed!')
            return False

    def connect(self):
        try:
            self.redis_client = redis.StrictRedis(host=RedisConf.host, port=RedisConf.port,
                                                  db=self.db, password=RedisConf.password,
                                                  socket_keepalive=True)
        except:
            logger.exception('connect redis failed!')

    def close(self):
        self.redis_client.connection_pool.disconnect()

    def fetch_one_task(self, timeout=0):
        """
        :param timeout: default 0, block mode
        :return:
        """
        _, url = self.redis_client.brpop(self.l_url_unscan, timeout)
        return url

    def insert_one_task(self, task):
        """
        :param timeout: default 0, block mode
        :return:
        """
        return self.redis_client.lpush(self.l_url_unscan, task)

    def fetch_one_result(self, timeout=0):
        """
        :param timeout: default 0, block mode
        :return:
        """
        return self.redis_client.lpush(self.l_url_result, timeout)

    @property
    def result_counts(self):
        """
        :return: The total number of left results
        """
        return self.redis_client.llen(self.l_url_result)

    @property
    def task_counts(self):
        """
        :return: The total number of left tasks
        """
        return self.redis_client.llen(self.l_url_unscan)

    def insert_result(self, result):
        self.redis_client.lpush(self.l_url_result, result)



    def set_url_scanned(self, mehtod, pattern):
        """
        :param url: URL class instance
        :return:
        """
        key = '{}/{}'.format(mehtod, pattern)
        self.redis_client.hsetnx(self.h_url_scanned, key, '*')

    def is_url_scanned(self, mehtod, pattern):
        """
        :param url: URL class instance
        :return:
        """
        key = '{}/{}'.format(method, pattern)
        return self.redis_client.hexists(self.h_url_scanned, key)



    def flushdb(self):
        self.redis_client.flushdb()
