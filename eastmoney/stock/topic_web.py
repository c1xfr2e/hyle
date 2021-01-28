#!/usr/bin/env python3
# coding: utf-8

"""
    获取股票题材

    返回数据格式:
        见 samples/topics.json
"""


def get_stock_topics(session, stock_code):
    stock_code = "{}{}".format("SH" if stock_code.startswith("6") else "SZ", stock_code)
    url = "http://f10.eastmoney.com/CoreConception/CoreConceptionAjax"
    headers = {
        "Accept": "*/*",
        "Referer": "http://f10.eastmoney.com/CoreConception/Index?type=web&stock_code={}".format(stock_code),
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) Chrome/76.0.3809.100 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    params = {
        "code": stock_code,
    }
    resp = session.get(url, headers=headers, params=params)
    data = resp.json()

    return data["hxtc"]


if __name__ == "__main__":
    import requests

    print(get_stock_topics(requests.Session(), "300058"))
