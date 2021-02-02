#!/usr/bin/env python3
# coding: utf-8


import requests
import sys
from enum import Enum

from wild.xueqiu.cookie import get_cookies
from wild.util import parse_percent, str_to_int


session = requests.Session()


# 报告类型 (报告期)
class ReportType(Enum):
    Q1  = 'Q1'
    Q2  = 'Q2'
    Q3  = 'Q3'
    Q4  = 'Q4'
    All = 'all'


def get_finance_indicator(stock_code: str, report_type: ReportType, count: int = 5):
    """
    stock_code  -- 6 位股票代码
    report_type -- 报告类型
    count       -- 返回数量
    """
    code = '{}{}'.format('SH' if stock_code.startswith('6') else 'SZ', stock_code)
    url = 'https://stock.xueqiu.com/v5/stock/finance/cn/indicator.json'
    params = {
        'symbol': code,
        'type': report_type.value,  # all: 全部  Q4: 年报
        'is_detail': 'true',
        'count': count,  # 返回记录数量
        'timestamp': ''
    }
    headers = {
        'Accept': '*/*',
        'Referer': 'https://xueqiu.com/S/{}'.format(code),
        'Host': 'stock.xueqiu.com',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    }
    resp = session.get(url, params=params, headers=headers, cookies=get_cookies())
    return resp.json()['data']


if __name__ == '__main__':
    print(get_finance_indicator('600739', ReportType.Q4))
