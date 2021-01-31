#!/usr/bin/env python3
# coding: utf-8

"""
    获取东方财富 App 股票核心题材
"""

import logging
import requests


def get_app_topics(session, stock_code, market_code):
    url = "https://emh5.eastmoney.com/api/HeXinTiCai/GetSuoShuBanKuai"
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 13_4_1 like Mac OS X) Mobile/15E148 iphonex color=b eastmoney_ios appversion_9.0.3 pkg=com.eastmoney.iphone",
        "Cache-Control": "public",
        "Accept-Language": "zh-cn",
    }
    payload = {
        "fc": "{stock}{market}".format(stock=stock_code, market=market_code),
        "platform": "ios",
        "fn": "%E8%93%9D%E8%89%B2%E5%85%89%E6%A0%87",
        "stockMarketID": "0",
        "stockTypeID": "80",
        "color": "b",
        "preload": "1",
        "Sys": "ios",
        "ProductType": "cft",
        "Version": "9.0.3",
        "DeviceType": "iOS 13.4.1",
        "DeviceModel": "iPhone10,3",
        "mobile": "",
        "mainBagVersion": "9.0.3",
        "bankocr": "1",
    }
    resp = session.post(url, headers=headers, json=payload)
    resp.encoding = "utf-8"
    return resp.json()


def _topic_filter(t):
    exclude_names = [
        "融资融券",
        "富时罗素",
        "标准普尔",
        "MSCI中国",
        "深股通",
        # "AH股",
        "创业板综",
        "50",
        "100",
        "180",
        "300",
        "380",
        "500",
    ]
    for n in exclude_names:
        if n in t["TypeName"]:
            return False
    return True


def store_app_topics(mongo_col, stock, topic_list):
    topics = [
        {
            "name": t["TypeName"],
            "reason": t["Reason"],
        }
        for t in topic_list
        if _topic_filter(t)
    ]
    r = mongo_col.update_one(
        {"_id": stock["code"]},
        {"$set": {"topic": topics}},
        upsert=True,
    )
    if r.raw_result["nModified"] != 1:
        logging.warning("Update topic failed: %s", r.raw_result)


if __name__ == "__main__":
    from eastmoney.stock import db

    sess = requests.Session()
    stock_cols = db.Stock.find(projection=["market", "code"])
    for stock in stock_cols:
        market_code = {
            "sh": "01",
            "kcb": "01",
            "sz": "02",
        }[stock["market"]]
        topic = get_app_topics(sess, stock["code"], market_code)
        store_app_topics(db.Stock, stock, topic["Result"]["SuoShuBanKuaiList"])
