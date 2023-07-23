#!/usr/bin/env python3
# coding: utf-8

"""
    下载公司主营产品
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


def get_product(sess, market, stock_code):
    code = "{}{}".format(market, stock_code)
    url = "http://f10.eastmoney.com/BusinessAnalysis/PageAjax?code={}".format(code)
    headers = {
        "Connection": "keep-alive",
        "Accept": "*/*",
        "Referer": "http://f10.eastmoney.com/BusinessAnalysis/Index?type=web&code={}".format(code),
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/88.0.4324.96 Safari/537.36",
    }
    resp = sess.get(url, headers=headers)
    return resp.json()["zygcfx"]


def _parse_product_data(data_list):
    if not data_list:
        return None

    first_date = data_list[0]["REPORT_DATE"]

    product_list = []
    for item in data_list:
        if item["REPORT_DATE"] != first_date:  # 只保留第一个 report date
            break
        if item["MAINOP_TYPE"] == "2":  # 产品的 MAINOP_TYPE 是 2
            product_list.append(
                {
                    "name": item["ITEM_NAME"],
                    "income": item.get("MAIN_BUSINESS_INCOME", 0),
                    "income_percent": item.get("MBI_RATIO", 0) * 100,
                    "profit": item.get("MAIN_BUSINESS_RPOFIT", 0),
                    "profit_percent": item.get("MBR_RATIO", 0) * 100,
                    "gross_profit_rate": item.get("GROSS_RPOFIT_RATIO", 0),
                }
            )
    return product_list


def get_and_store_product_list():
    ses = requests.Session()

    write_op_list = []

    stocks = list(db.Stock.find(projection=["market", "code"]))

    progress_total = len(stocks)
    print_progress_bar(0, progress_total, length=40)

    for i, st in enumerate(stocks):
        data = get_product(ses, st["market"], st["code"])
        if not data:
            continue
        product_list = _parse_product_data(data)
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": st["_id"]},
                {"$set": {"product": product_list}},
            )
        )
        print_progress_bar(i + 1, progress_total, length=40)

    db.Stock.bulk_write(write_op_list)


if __name__ == "__main__":
    get_and_store_product_list()
