#!/usr/bin/env python3
# coding: utf-8

"""
    获取股息率

    返回数据样例: samples/dividend.json
"""

import pymongo
import requests

from download.eastmoney.stock import db
from util.progress_bar import print_progress_bar


def _to_float(s):
    if not s or s == "-" or s == "--":
        return 0.0
    return float(s)


def get_dividend_history(session, stock_code):
    url = "http://dcfm.eastmoney.com/EM_MutiSvcExpandInterface/api/js/get"
    headers = {
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/88.0.4324.146 Safari/537.36",
        "Accept": "*/*",
        "Referer": "http://data.eastmoney.com/",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    }
    params = {
        "st": "ReportingPeriod",
        "sr": "-1",
        "ps": "10",
        "p": "1",
        "type": "DCSOBS",
        "cmd": stock_code,
        "token": "894050c76af8597a853f5b408b759f5d",
    }
    resp = session.get(url, headers=headers, params=params)
    data = resp.json()
    return data


def _extract(dividend_data):
    return [
        {
            "date": d["ReportingPeriod"][0:10],
            "percent": round(_to_float(d.get("GXL", 0.0)) * 100, 2),
        }
        for d in dividend_data
    ]


def get_and_store_dividend():

    ses = requests.Session()
    write_op_list = []
    stock_cols = list(db.Stock.find(projection=["code"]))
    progress_total = len(stock_cols)
    print_progress_bar(0, progress_total, length=50)
    for i, stock in enumerate(stock_cols):
        dividend_history = _extract(get_dividend_history(ses, stock["code"]))
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": stock["_id"]},
                {"$set": {"dividend_history": dividend_history}},
            )
        )
        print_progress_bar(i + 1, progress_total, length=50)

    db.Stock.bulk_write(write_op_list)


if __name__ == "__main__":
    get_and_store_dividend()
