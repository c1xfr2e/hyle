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

import db
from download.xueqiu.cookie import get_cookies


def _parse_data(d):
    return dict(
        total_value=d["market_capital"],
        float_value=d["float_market_capital"],
        total_shares=d["total_shares"],
        float_shares=d["float_shares"],
        pb=d["pb"],
        pe_lyr=d["pe_lyr"],
        pe_ttm=d["pe_ttm"],
        pe_forecast=d["pe_forecast"],
        eps=d["eps"],
        navps=d["navps"],
        dividend_yield=d["dividend_yield"],
        pledge_ratio=d["pledge_ratio"],
        goodwill_in_net_assets=d["goodwill_in_net_assets"],
        price=d["last_close"],
        avg_price=d["avg_price"],
        change=d["percent"],
        amount=d["amount"],
        volume=d["volume"],
        volume_percent=d["volume_ratio"],
        amplitude=d["amplitude"],
        high_52_week=d["high52w"],
        low_52_week=d["low52w"],
        update_time=datetime.now(),
    )


def get_stock_profile(session, stock_code):
    """拉取股票基本信息

    Args:
        stock_code: 6 位股票代码

    Returns:
        dict of stock profile
    """
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
    return _parse_data(resp.json()["data"]["quote"])


def _try_get(session, stock_code):
    try:
        return get_stock_profile(session, stock_code)
    except Exception as e:
        logging.error("_try_get failed: {}".format(stock_code))
        logging.exception(e)
        return None


def _get_and_store(stock_codes):
    failed_stock_codes = []
    write_op_list = []
    ses = requests.Session()
    for code in stock_codes:
        p = _try_get(ses, code)
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

    db.Stock.bulk_write(write_op_list)
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
        failed_codes = _get_and_store(stock_codes)
        if not failed_codes:
            break
        stock_codes = failed_codes

        time.sleep(BACKOFF_TIME)
