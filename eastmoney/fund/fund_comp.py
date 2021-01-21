#!/usr/bin/env python3
# coding: utf-8

"""
    请求基金公司列表
"""

import json
from pprint import pprint


def get_fund_companies(session):
    url = "http://fund.eastmoney.com/Data/FundRankScale.aspx"
    headers = {
        "Accept": "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://fund.eastmoney.com/company/default.html",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8 %d\n",
    }
    resp = session.get(url, headers=headers)

    # 返回数据的格式为: var json={datas:[['80000080','山西证券股份有限公司', ...}
    # 用单引号替换双引号
    text = '{"datas"' + resp.text[15:].replace("'", '"')

    return json.loads(text)["datas"]


if __name__ == "__main__":
    import requests

    fund_comp_list = get_fund_companies(requests.Session())
    for f in fund_comp_list:
        print(f[0], f[1])
