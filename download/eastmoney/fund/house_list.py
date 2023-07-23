#!/usr/bin/env python3
# coding: utf-8

"""
    调用 eastmoeny 接口获取基金基金公司列表（按资产规模排序）
    数据保存到 mongodb 的 fund_house collection
"""

import json
import pymongo
import requests
from datetime import datetime

from download.eastmoney.fund import db


def get_fund_house_list(session):
    """ 拉取基金公司列表 """

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
    house_list = [
        dict(
            gsid=i[0],
            name=i[9],
            size=float(i[7]) if i[7] else 0.0,
            regdate=datetime.strptime(i[2], "%Y-%m-%d"),
        )
        for i in ret_list
    ]

    return house_list


def _store_house_list(house_list):
    ops = [
        pymongo.UpdateOne(
            {"_id": house["gsid"]},
            {"$set": house},
            upsert=True,
        )
        for house in house_list
    ]
    db.FundHouse.bulk_write(ops)


if __name__ == "__main__":
    fund_house_list = get_fund_house_list(requests.Session())

    # 按规模排序
    fund_house_list.sort(key=lambda x: x["size"], reverse=True)

    # 保存规模前几的基金公司
    FUND_COMPANY_TOP_COUNT = 20

    _store_house_list(fund_house_list[0:FUND_COMPANY_TOP_COUNT])
