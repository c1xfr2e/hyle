#!/usr/bin/env python3
# coding: utf-8

"""
    获取主营业务数据

    返回数据样例: samples/business.json
"""

import pymongo
import requests

from download.eastmoney.stock import db
from util.progress_bar import print_progress_bar
from util.strconv import cn_to_float, to_percent


def _text_to_float(s):
    if s == "-" or s == "--":
        return 0.0
    return cn_to_float(s)


def get_business(session, stock_code, market):
    code = "{}{}".format(market, stock_code)
    url = "http://f10.eastmoney.com/BusinessAnalysis/BusinessAnalysisAjax?code={}".format(code)
    headers = {
        "Connection": "keep-alive",
        "Accept": "*/*",
        "Referer": "http://f10.eastmoney.com/f10_v2/BusinessAnalysis.aspx?code={}".format(code),
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/88.0.4324.96 Safari/537.36",
    }
    params = {
        "code": code,
    }
    resp = session.get(url, headers=headers, params=params)
    zygcfx = resp.json()["zygcfx"]
    if len(zygcfx) == 0:
        return None
    if len(zygcfx) >= 2:
        return [zygcfx[0], zygcfx[1]]
    else:
        return [zygcfx[0]]


def _parse_business(business):
    business_list = []
    for b in business:
        by_industry = [
            {
                "name": hy["zygc"],
                "income": _text_to_float(hy["zysr"]),
                "income_percent": to_percent(hy["srbl"]),
                "profit": _text_to_float(hy["zylr"]),
                "profit_percent": to_percent(hy["lrbl"]),
                "gross_profit_rate": to_percent(hy["mll"]),
            }
            for hy in b.get("hy", [])
        ]
        by_product = [
            {
                "name": cp["zygc"],
                "income": _text_to_float(cp["zysr"]),
                "income_percent": to_percent(cp["srbl"]),
                "profit": _text_to_float(cp["zylr"]),
                "profit_percent": to_percent(cp["lrbl"]),
                "gross_profit_rate": to_percent(cp["mll"]),
            }
            for cp in b.get("cp", [])
        ]
        business_list.append(
            {
                "date": b["rq"],
                "by_industry": by_industry,
                "by_product": by_product,
            }
        )
    return business_list


def _find_filter():
    return {}


def get_and_store_business():
    sess = requests.Session()

    write_op_list = []

    stocks = list(
        db.Stock.find(
            filter=_find_filter(),
            projection=["market", "code"],
        )
    )

    progress_total = len(stocks)
    print_progress_bar(0, progress_total, length=40)

    for i, st in enumerate(stocks):
        b = get_business(sess, st["code"], st["market"])
        if not b:
            continue
        business = _parse_business(b)
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": st["_id"]},
                {"$set": {"business": business}},
            )
        )
        print_progress_bar(i + 1, progress_total, length=40)

    db.Stock.bulk_write(write_op_list)


if __name__ == "__main__":
    get_and_store_business()

    # stock = {
    #     "_id": "600028",
    #     "market": "sh",
    #     "code": "600028",
    # }
    # business_list = _parse_business(get_business(requests.Session(), stock["code"], stock["market"]))
    # print(business_list)
