#!/usr/bin/env python3
# coding: utf-8

"""
    获取基金公司列表（按资产规模排序）
"""

import json


def get_fund_companies(session):
    url = "http://fund.eastmoney.com/Data/FundRankScale.aspx"
    headers = {
        "Accept": "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://fund.eastmoney.com/company/default.html",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    }
    resp = session.get(url, headers=headers)

    # 返回数据的格式为: var json={datas:[['80000080','山西证券股份有限公司', ...}
    # 用单引号替换双引号
    text = '{"datas"' + resp.text[15:].replace("'", '"')

    # 按管理规模从高到低排序
    fund_co_list = json.loads(text)["datas"]
    fund_co_list.sort(reverse=True, key=lambda x: 0.0 if not x[7] else float(x[7]))

    return fund_co_list


if __name__ == "__main__":
    import requests

    fund_co_list = get_fund_companies(requests.Session())
    for f in fund_co_list[0:20]:
        print(f[0], f[1], f[7])
