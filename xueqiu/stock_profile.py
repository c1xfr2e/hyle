#!/usr/bin/env python3
# coding: utf-8

"""
雪球个股首页报价信息接口

返回数据格式:
    见 samples/stock_profile.json
"""

import logging
import pymongo
import requests
import time
from datetime import datetime

from xueqiu import db
from xueqiu.cookie import get_cookies


def get_stock_profile(session, stock_code):
    code = "{}{}".format("SH" if stock_code.startswith("6") else "SZ", stock_code)
    url = "https://stock.xueqiu.com/v5/stock/quote.json"
    params = {
        "symbol": code,
        "extend": "detail",
    }
    headers = {
        "Accept": "*/*",
        "Referer": "https://xueqiu.com/S/{}".format(code),
        "Host": "stock.xueqiu.com",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
    }
    resp = session.get(
        url,
        params=params,
        headers=headers,
        cookies=get_cookies(),
        allow_redirects=False,
    )
    return resp.json()["data"]["quote"]


def _extract(p):
    return dict(
        total_value=p["market_capital"],
        float_value=p["float_market_capital"],
        total_shares=p["total_shares"],
        float_shares=p["float_shares"],
        pb=p["pb"],
        pe_lyr=p["pe_lyr"],
        pe_ttm=p["pe_ttm"],
        pe_forecast=p["pe_forecast"],
        eps=p["eps"],
        navps=p["navps"],
        dividend_yield=p["dividend_yield"],
        pledge_ratio=p["pledge_ratio"],
        goodwill_in_net_assets=p["goodwill_in_net_assets"],
        price=p["last_close"],
        avg_price=p["avg_price"],
        change=p["percent"],
        amount=p["amount"],
        volume=p["volume"],
        volume_percent=p["volume_ratio"],
        amplitude=p["amplitude"],
        high_52_week=p["high52w"],
        low_52_week=p["low52w"],
        update_time=datetime.now(),
    )


def _try_get(session, stock_code):
    try:
        return _extract(get_stock_profile(session, stock_code))
    except Exception as e:
        logging.error("_try_get failed: {}".format(stock_code))
        logging.exception(e)
        return None


def _get_and_store(mongo_col, stock_codes):
    failed_stock_codes = []
    write_op_list = []
    sess = requests.Session()
    for code in stock_codes:
        p = _try_get(sess, code)
        # 保存失败的 stock code 为了 retry
        if not p:
            failed_stock_codes.append(code)
            continue
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": code},
                {
                    "$set": {"profile": p},
                },
            )
        )
        time.sleep(0.2)

    mongo_col.bulk_write(write_op_list)
    return failed_stock_codes


TRY_TIMES = 5
BACKOFF_TIME = 5


if __name__ == "__main__":
    stock_codes = [st["_id"] for st in db.Stock.find(projection=[])]
    n = TRY_TIMES
    while True:
        if n == 0:
            break
        n -= 1
        failed_codes = _get_and_store(db.Stock, stock_codes)
        if not failed_codes:
            break
        stock_codes = failed_codes

        time.sleep(BACKOFF_TIME)
