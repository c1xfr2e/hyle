#!/usr/bin/env python3
# coding: utf-8

"""
<东方财富> 财务分析

返回数据格式:
    见 samples/finance_analysis.json
"""

import requests


url = 'http://f10.eastmoney.com/NewFinanceAnalysis/MainTargetAjax'

params = {
    'type': '1',  # 0： 按报告期  1: 按年度
    'code': 'SZ300753'
}

headers = {
    'Accept': '*/*',
    'Referer': 'http://f10.eastmoney.com/NewFinanceAnalysis/Index?type=web&code=SZ300753',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}


def get_finance_analysis(stock_code):
    resp = requests.get(url, headers=headers, params=params)
    data = resp.json()
    print(data)
    return data


get_finance_analysis('')
