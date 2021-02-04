#!/usr/bin/env python3
# coding: utf-8

"""
    获取主营业务数据

    返回数据样例: samples/business.json
"""

import logging
import pymongo
import requests

from download.eastmoney.stock import db
from util.string import str_to_float, str_to_percent


def get_business(session, stock_code, market):
    code = "{}{}".format(market, stock_code)
    url = "http://f10.eastmoney.com/BusinessAnalysis/BusinessAnalysisAjax?code={}".format(code)
    headers = {
        "Accept": "*/*",
        "Referer": "http://f10.eastmoney.com/f10_v2/BusinessAnalysis.aspx?code={}".format(code),
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/88.0.4324.96 Safari/537.36",
    }
    params = {
        "code": code,
    }
    resp = session.get(url, headers=headers, params=params)
    data = resp.json()
    return data["zygcfx"][0:2]


def _str_to_float(s):
    if s == "-" or s == "--":
        return 0.0
    if s[-2:] == u"万亿":
        return float(s[0:-2]) * (10 ** 12)
    return str_to_float(s)


def _filter_business(business):
    business_list = []
    for b in business:
        date = b["rq"]
        by_industry = [
            {
                "name": hy["zygc"],
                "income": _str_to_float(hy["zysr"]),
                "income_percent": str_to_percent(hy["srbl"]),
                "profit": _str_to_float(hy["zylr"]),
                "profit_percent": str_to_percent(hy["lrbl"]),
                "gross_profit_rate": str_to_percent(hy["mll"]),
            }
            for hy in b.get("hy", [])
        ]
        by_product = [
            {
                "name": cp["zygc"],
                "income": _str_to_float(cp["zysr"]),
                "income_percent": str_to_percent(cp["srbl"]),
                "profit": _str_to_float(cp["zylr"]),
                "profit_percent": str_to_percent(cp["lrbl"]),
                "gross_profit_rate": str_to_percent(cp["mll"]),
            }
            for cp in b.get("cp", [])
        ]
        business_list.append(
            {
                "date": date,
                "by_industry": by_industry,
                "by_product": by_product,
            }
        )
    return business_list


def _find_filter():
    return {
        # "business": {"$exists": 0},
    }


def get_and_store_business():
    sess = requests.Session()

    write_op_list = []
    stock_cols = db.Stock.find(
        filter=_find_filter(),
        projection=["market", "code"],
    )
    for stock in stock_cols:
        market = "sh" if stock["market"] == "kcb" else stock["market"]
        try:
            business_list = _filter_business(get_business(sess, stock["code"], market))
            write_op_list.append(
                pymongo.UpdateOne(
                    {"_id": stock["_id"]},
                    {"$set": {"business": business_list}},
                )
            )
        except Exception as e:
            logging.info(stock)
            logging.exception(e)

    db.Stock.bulk_write(write_op_list)


if __name__ == "__main__":
    get_and_store_business()

    # stock = {
    #     "_id": "600028",
    #     "market": "sh",
    #     "code": "600028",
    # }
    # business_list = _filter_business(get_business(requests.Session(), stock["code"], stock["market"]))
    # print(business_list)
