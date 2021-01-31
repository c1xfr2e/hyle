#!/usr/bin/env python3
# coding: utf-8

"""
    获取股票题材

    返回数据格式:
        见 samples/topics.json
"""


def get_web_topics(session, stock_code, market):
    stock_code = "{}{}".format(market, stock_code)
    url = "http://f10.eastmoney.com/CoreConception/CoreConceptionAjax"
    headers = {
        "Accept": "*/*",
        "Referer": "http://f10.eastmoney.com/CoreConception/Index?type=web&stock_code={}".format(stock_code),
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) Chrome/76.0.3809.100 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    params = {
        "code": stock_code,
    }
    resp = session.get(url, headers=headers, params=params)
    data = resp.json()

    return data["hxtc"]


def _filter_topics(topics):
    ITEMS_TO_KEEP = 4
    return [
        {
            "title": t["gjc"],
            "content": t["ydnr"],
        }
        for t in topics[0:ITEMS_TO_KEEP]
    ]


if __name__ == "__main__":
    import pymongo
    import requests
    from eastmoney.stock import db

    sess = requests.Session()

    write_op_list = []
    stock_cols = db.Stock.find(projection=["market", "code"])
    for stock in stock_cols:
        market = "sh" if stock["market"] == "kcb" else stock["market"]
        topics_list = _filter_topics(get_web_topics(sess, stock["code"], market))
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": stock["_id"]},
                {"$set": {"topic_detail": topics_list}},
            )
        )

    db.Stock.bulk_write(write_op_list)
