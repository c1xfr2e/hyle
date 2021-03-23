#!/usr/bin/env python3
# coding: utf-8

"""
    调用 eastmoeny 接口获取基金基金公司列表（按资产规模排序）
    保存到 mongodb
"""

import json
import pymongo
import requests
from datetime import datetime

from download.eastmoney.fund import db


def _to_float(text):
    return float(text) if text else 0.0


def get_company_list(session):
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
    # 需要用单引号替换双引号，截取 json 数据
    offset = 15
    text = '{"datas"' + resp.text[offset:].replace("'", '"')

    ret_list = json.loads(text)["datas"]
    company_list = [
        dict(
            gsid=i[0],
            name=i[9],
            size=_to_float(i[7]),
            regdate=datetime.strptime(i[2], "%Y-%m-%d"),
        )
        for i in ret_list
    ]

    # 按规模排序
    company_list.sort(key=lambda x: x["size"], reverse=True)

    return company_list


def store_company_list(mongo_col, company_list):
    ops = [
        pymongo.UpdateOne(
            {"_id": co["gsid"]},
            {"$set": co},
            upsert=True,
        )
        for co in company_list
    ]
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    fund_co_list = get_company_list(requests.Session())

    # 保存规模 top 前几的基金公司
    FUND_COMPANY_TOP_COUNT = 50

    store_company_list(db.FundCompany, fund_co_list[0:FUND_COMPANY_TOP_COUNT])
