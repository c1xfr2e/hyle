#!/usr/bin/env python3
# coding: utf-8

"""
    从深交所官网下载深市股票列表 xlsx 文件, 读取并存入 MongoDB.
"""

import logging
import pymongo
import requests
import xlrd
from collections import namedtuple
from datetime import datetime
from typing import List


log = logging.getLogger(__name__)


def is_downloadable(url) -> bool:
    """
    Does the url contain a downloadable resource?
    """
    content_type = requests.head(url, allow_redirects=True).headers.get("content-type")
    if "text" in content_type.lower() or "html" in content_type.lower():
        return False
    return True


stock = namedtuple(
    "stock",
    [
        "code",  # 6 位代码
        "name",  # 简称
        "full_name",  # 全称
        "total_shares",  # 总股本
        "float_shares",  # 流通股本
        "industry",  # 行业
        "list_date",  # 上市日期
    ],
)


def get_stock_list() -> List[stock]:
    """
    下载 http://www.szse.cn/market/stock/list/index.html 页面的股票列表 xlsx 文件并读取
    """
    url = "http://www.szse.cn/api/report/ShowReport?SHOWTYPE=xls&CATALOGID=1110&TABKEY=tab1"
    resp = requests.get(url)
    if not resp.ok:
        log.error("request failed: url=%s, response=%s", url, resp)
        exit(-1)
    wb = xlrd.open_workbook(file_contents=resp.content)
    st = wb.sheet_by_index(0)
    stock_list = []
    for i in range(1, st.nrows):
        row = st.row(i)
        stock_list.append(
            stock(
                code=row[4].value,
                name=row[5].value,
                full_name=row[1].value,
                total_shares=int(row[7].value.replace(",", "").strip()),
                float_shares=int(row[8].value.replace(",", "").strip()),
                industry=row[17].value,
                list_date=row[6].value,
            )
        )
    return stock_list


def store_stock_list(mongo_col, stock_list):
    ops = [
        pymongo.UpdateOne(
            {"_id": stock.code},
            {
                "$set": {
                    "code": stock.code,
                    "name": stock.name,
                    "full_name": stock.full_name,
                    "total_shares": stock.total_shares,
                    "float_shares": stock.float_shares,
                    "industry": stock.industry,
                    "list_date": stock.list_date,
                    "update_time": datetime.now(),
                }
            },
            upsert=True,
        )
        for stock in stock_list
    ]
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    from szse import db

    stock_list = get_stock_list()
    store_stock_list(db.Stock, stock_list)

    # stock_list = get_stock_list()
    # print(len([s.code for s in stock_list]))
    # s = stock_list[0]
    # print(s._asdict())
