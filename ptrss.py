#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Tony Liu'

'''
rss
'''
import os
import re
import sqlite3
import time
import random
from lxml import etree

import feedparser
import requests
import yaml


## 禁用ssl-warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RssDB():
    def __init__(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rss.db')
        self.conn = sqlite3.connect(path)
        self.csr = self.conn.cursor()

    def init_db(self):
        '''
        初始化sqlite
        '''
        #self.csr.execute("drop table torrents")
        cnt = self.csr.execute("select count(*) from sqlite_master where type='table' and name='torrents';").fetchone()[0]
        if cnt == 0:
            self.csr.execute(''' create table torrents (
                id          text primary key not null,
                title       text not null,
                size      real  not null,
                gmt_create  timestamp  not null
            );''')

    def insert(self, data):
        try:
            self.csr.execute("insert into torrents values(?,?,?,?)", data)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)

    def fetchone(self, key):
        return self.csr.execute("select * from torrents where id=?", (key, )).fetchone()

    def scale(self, key):
        return self.csr.execute("select count(*) from torrents where id=?", (key,)).fetchone()[0]
    
    def fetchall(self):
        return self.csr.execute("select * from torrents").fetchall()

    def close(self):
        try:
            self.csr.close()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass
        

class Rss():
    UNIT = 1024*1024*1024 ## 以GB为单位
    DISCOUNT = {
        'free': 'free',
        'twoup': '2x',
        'twoupfree': '2xfree',
        'thirtypercent': '30%',
        'halfdown': '50%',
        'twouphalfdown': '2x50%'
    }

    def __init__(self, config):
        self.config = dict(config)
        if not self.config.get('download'):
            self.config['download'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'torrents')
        self.config.setdefault('user-agent', '')
        self.config.setdefault('discount', None)
        self.config.setdefault('title', None)
        self.config.setdefault('size', {'min': 0, 'max': -1})
        self.config['size'].setdefault('min', 0)
        self.config['size'].setdefault('max', -1)
        print(self.config)

        self.headers = {
            'cookie': self.config['cookie'],
            'user-agent': self.config['user-agent']
        }

    def _request(self, url):
        resp = requests.get(url, headers=self.headers, verify=False, allow_redirects=False, timeout=30)
        if resp.status_code == 302:
            raise RuntimeError("网站无法登陆, 更新cookie~~")
        return resp

    def _check(self, entry):
        print('----------------{}----------------'.format(entry.title))

        # 查询数据库
        if 1 == rssdb.scale(entry.id):
            return False
        # 新增
        rssdb.insert((entry.id, entry.title, entry.links[1]['length'], time.time()))

        # 判断标题
        if self.config['title']:
            flag = False
            for title in self.config['title']:
                if title in entry.title:
                    flag = True
                    break
            if not flag:
                print('标题不匹配')
                return False

        # 获取文件大小 GB 两位小数
        size = round((entry.links[1]['length'] / self.UNIT), 2)
        print(size)
        max_ = self.config['size']['max']
        min_ = self.config['size']['min']
        if -1 == max_:
            if size < min_:
                print('文件过小')
                return False
        else:
            if size < min_ or size > max_:
                print('文件大小不匹配')
                return False
        
        # # //tr/text()
        # result = html.xpath('//td[@id="outer"]/table[1]/tr')
        # print(result)
        # # for tr in result:
        # #     print(tr.xpath('td[1]/text()'))
        
        # print('---------------------------')
        # print(result[2].xpath('td[2]/text()'))

        # peer信息
        # result = html.xpath('//div[@id="peercount"]/b/text()')
        # print(re.search(r'(\d+)\w*', result[0], re.S).group(1))
        # print(re.search(r'(\d+)\w*', result[1], re.S).group(1))

        # 优惠信息
        if self.config['discount']:
            resp = self._request(entry.link)
            html = etree.HTML(resp.text)
            result = html.xpath('//h1[@id="top"]/b/font/@class')
            print(result)
            if result:
                discount = self.DISCOUNT.get(result[0], None)
                if discount not in self.config['discount']:
                    print('优惠信息不匹配')
                    return False
            else:
                print('无优惠信息')
                return False
        
        return True


    def download(self):
        resp = self._request(self.config['rss'])
        feed = feedparser.parse(resp.text)
        for e in feed.entries:
            time.sleep(random.randint(1,4))
            if self._check(e):
                resp = self._request(e['links'][1]['href'])
                if resp.status_code == 200 and resp.headers.get('Content-Disposition'):
                    with open(os.path.join(self.config['download'], e.id + '.torrent'), "wb") as f:
                        f.write(resp.content)
                else:
                    print(resp.status_code, resp.text)
    

if __name__ == '__main__':
    yamlpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')

    # 读取配置文件
    tasks = None
    with open(yamlpath, 'r', encoding='utf-8') as f:
        tasks = yaml.safe_load(f.read())
    if not tasks:
        raise RuntimeError("请正确配置yaml文件")

    rssdb = RssDB()
    try:
        rssdb.init_db()
        # print(rssdb.fetchall())
        
        for k, v in tasks.items():
            print('----------------{}----------------'.format(k))
            if v.get('rss') is None or v.get('cookie') is None:
                raise RuntimeError("任务[{}] 需要'rss', 'cookie'配置项".format(k))
            try:
                rss = Rss(v)
                rss.download()
            except Exception as err:
                print(k, err)
    finally:
        rssdb.close()