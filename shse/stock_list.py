#!/usr/bin/env python3
# coding: utf-8

"""
Query stock list from sse.com.cn.

返回数据格式：
{
    "result": [
        {
            "COMPANY_CODE": "600000",
            "SECURITY_ABBR_A": "浦发银行",
            "SECURITY_ABBR_B": "-",
            "SECURITY_CODE_A": "600000",
            "SECURITY_CODE_B": "-",
            "totalShares": "2935208.04",
            "totalFlowShares": "2810376.39",
            "NUM": "1",
            "TYPE": "主板A股",
            "LISTING_DATE": "1999-11-10"
            "endDate": "2019-08-02",
        },
    ]
}
"""

import logging
import requests
from collections import namedtuple
from typing import Dict, List

from ratelimit import limits, sleep_and_retry

log = logging.getLogger(__name__)

stock = namedtuple('stock',
    [
        'code',          # 6 位代码
        'name',          # 简称
        'total_shares',  # 总股本
        'float_shares',  # 流通股本
    ]
)

STOCK_TYPE_MAIN = 1
STOCK_TYPE_KCB = 8

@sleep_and_retry
@limits(calls=1, period=0.2)
def get_stock_list_by_page(page: int) -> List[stock]:
    url = 'http://query.sse.com.cn/security/stock/getStockListData.do'
    headers = {
        'Referer': 'http://www.sse.com.cn/assortment/stock/list/share/',  # 必须有 Referer， 否则调用非法
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    params = {
        'isPagination': 'true',
        'stockCode': '',
        'csrcCode': '',
        'areaName': '',
        'stockType': 1,  # 1: 主板A股  2: B股  8: 科创板
        'pageHelp.cacheSize': 1,
        'pageHelp.beginPage': page,  # 页数， 每次请求递增
        'pageHelp.pageSize': 50,  # 每次请求返回的股票数量， 最大50
        'pageHelp.pageNo': 1,
    }
    resp = requests.get(url, headers=headers, params=params)
    if not resp.ok:
        log.error('request failed: url=%s, response=%s', url, resp)
        resp.raise_for_status()
        return None
    result = resp.json()['result']
    return [
        stock(
            code=r['SECURITY_CODE_A'].strip(),
            name=r['SECURITY_ABBR_A'].strip(),
            total_shares=int(float(r['totalShares'].strip()) * 10000) if 'totalShares' in r else None,
            float_shares=int(float(r['totalFlowShares'].strip()) * 10000) if 'totalFlowShares' in r else None
        )
        for r in result
    ]


def get_stock_list() -> List[stock]:
    """
    循环调用 get_stock_list_by_page 获取全部股票列表
    """
    page = 1
    stock_list = []
    while True:
        p = get_stock_list_by_page(page)
        if not p:
            break
        page += 1
        stock_list.extend(p)
    return stock_list


if __name__ == '__main__':
    stock_list = get_stock_list()
    print([s.code for s in stock_list])
