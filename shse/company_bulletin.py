#!/usr/bin/env python3
# coding: utf-8

"""
Query stock list from sse.com.cn.

返回数据格式：

"""

import logging
import requests
from collections import namedtuple
from typing import Dict, List


def get_company_bulletin_list(pageNo: int, pageSize: int):
    url = 'http://query.sse.com.cn/security/stock/queryCompanyBulletin.do'
    headers = {
        'Referer': 'http://www.sse.com.cn/disclosure/listedinfo/announcement/',  # 必须有 Referer， 否则调用非法
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    params = {
        'securityType': '0101,120100,020100,020200,120200',
        'reportType2': 'DQBG',
        'reportType': 'ALL',
        'beginDate': '2019-08-19',
        'endDate': '2019-08-20',
        'isPagination': 'true',
        'pageHelp.pageSize': pageSize,
        'pageHelp.pageCount': 50,
        'pageHelp.pageNo': 1,
        'pageHelp.beginPage': pageNo,
        'pageHelp.cacheSize': 1,
        'pageHelp.endPage': 5
    }
    resp = requests.get(url, headers=headers, params=params)
    if not resp.ok:
        logging.error('request failed: url=%s, response=%s', url, resp)
        resp.raise_for_status()
        return None
    data = resp.json()
    return data


if __name__ == '__main__':
    data = get_company_bulletin_list(1, 50)
    print(data)
