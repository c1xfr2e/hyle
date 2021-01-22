#!/usr/bin/env python3
# coding: utf-8

"""
    获取基金公司列表（按资产规模排序）
"""

import json
import pymongo
from datetime import datetime


def _to_float(text):
    return float(text) if text else 0.0


def get_fund_company_list(session):
    url = "http://fund.eastmoney.com/Data/FundRankScale.aspx"
    headers = {
        "Accept": "*/*; q=0.01",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/87.0.4280.141 Safari/537.36",
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
    ret_list = json.loads(text)["datas"]
    co_list = [
        dict(
            gsid=i[0],
            name=i[9],
            size=_to_float(i[7]),
            regdate=datetime.strptime(i[2], "%Y-%m-%d"),
        )
        for i in ret_list
    ]
    co_list.sort(key=lambda x: x["size"], reverse=True)

    return co_list


def save_fund_company_list(col, co_list):
    ops = [
        pymongo.UpdateOne(
            {"_id": i["gsid"]},
            {"$set": i},
            upsert=True,
        )
        for i in co_list
    ]
    col.bulk_write(ops)


if __name__ == "__main__":
    import requests
    from eastmoney import db

    fund_co_list = get_fund_company_list(requests.Session())
    save_fund_company_list(db.FundCompany, fund_co_list[0:20])
