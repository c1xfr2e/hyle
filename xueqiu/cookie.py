#!/usr/bin/env python3
# coding: utf-8

"""
    调用雪球 API 之前需要先获取 cookie
"""

import requests


# 缓存 cookie
cookies = None


def get_cookies(session=None):
    """
    访问雪球首页, 获取 cookie 并保存
    """
    global cookies
    if cookies:
        return cookies
    url = "https://xueqiu.com"
    headers = {
        "Accept": "*/*",
        "Host": "xueqiu.com",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
    }
    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)
    cookies = resp.cookies
    return cookies
