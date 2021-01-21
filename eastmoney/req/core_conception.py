#!/usr/bin/env python3
# coding: utf-8

"""
调用 <东方财富> web 接口获取股票题材概念

返回数据格式:
    见 samples/core_conception.json
"""


def get_core_conception(session, stock_code):
    code = '{}{}'.format('SH' if stock_code.startswith('6') else 'SZ', stock_code)
    url = 'http://f10.eastmoney.com/CoreConception/CoreConceptionAjax'
    headers = {
        'Accept': '*/*',
        'Referer': 'http://f10.eastmoney.com/CoreConception/Index?type=web&code={}'.format(code),
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    params = {
        'code': code,
    }
    resp = session.get(url, headers=headers, params=params)
    data = resp.json()

    return data['hxtc']


if __name__ == '__main__':
    import requests
    print(get_core_conception(requests.Session(), '300496'))
