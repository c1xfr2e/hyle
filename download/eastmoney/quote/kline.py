#!/usr/bin/env python3
# coding: utf-8

"""
    get 股票历史K线
    数据保存到 mongodb 的 kline collection
"""

import arrow
import pymongo
import requests
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List

import db
from setting import REPORT_DATE
from util.progress_bar import print_progress_bar


# K线类型
class KLineType(Enum):
    Day = "101"  # 日线
    Week = "102"  # 周线


def get_kline_history(session, stock_code, kline_type, begin, end) -> List[Dict]:
    """
    get 股票历史K线

    Args:
        stock_code: 股票代码
        kline_type: KLineType
        begin: 开始日期 datetime
        end: 结束日期 datetime

    Returns:
        解析后的K线列表
    """

    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    headers = {
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)",
        "Accept": "*/*",
        "Referer": "http://quote.eastmoney.com/",
    }
    params = {
        "secid": "{market}.{stock}".format(market="1" if stock_code[0] == "6" else "0", stock=stock_code),
        "fields1": "f4,f5,f6",
        "fields2": "f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": kline_type.value,
        "fqt": 1,
        "beg": begin.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "&_": int(time.time() * 1000),
    }
    resp = session.get(url, headers=headers, params=params)
    data_klines = resp.json()["data"]["klines"]
    return [_parse_kline(k.split(",")) for k in data_klines]


def _parse_kline(k):
    return {
        "datetime": k[0],
        "open": k[1],
        "close": k[2],
        "high": k[3],
        "low": k[4],
        "volume": k[5],
        "amount": k[6],
        "amplitude": k[7],
        "change": k[8],
        "turnover": k[9],
    }


if __name__ == "__main__":
    sess = requests.Session()

    write_op_list = []

    kline_type = KLineType.Day

    begin = arrow.get(REPORT_DATE, "YYYY-MM-DD").shift(months=-3, days=1).datetime
    end = datetime.now()

    stocks = list(db.Stock.find(projection=["name"]))

    progress_total = len(stocks)
    print_progress_bar(0, progress_total, length=40)

    for i, st in enumerate(stocks):
        klines = get_kline_history(sess, st["_id"], kline_type, begin, end)
        if not klines:
            continue
        kline_field_name = {KLineType.Day: "day", KLineType.Week: "week"}[kline_type]
        doc = {
            "name": st["name"],
            "latest": klines[-1]["datetime"],
            kline_field_name: klines,
        }
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": st["_id"]},
                {"$set": doc},
                upsert=True,
            )
        )
        db.Kline.bulk_write(write_op_list)
        print_progress_bar(i + 1, progress_total, length=40)
