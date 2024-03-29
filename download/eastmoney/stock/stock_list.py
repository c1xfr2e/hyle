#!/usr/bin/env python3
# coding: utf-8

"""
    get 沪深股票列表
    数据保存到 mongodb 的 stock collection
"""

import pymongo
import requests
from datetime import datetime
from typing import Dict, List

import db


def get_stock_total(session):
    """ get 沪深股票总数 """

    url = "http://3.push2.eastmoney.com/api/qt/clist/get"
    headers = {
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)",
        "Accept": "*/*",
        "Referer": "http://quote.eastmoney.com/",
    }
    params = {
        "pn": 1,
        "pz": 1,
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
    }
    resp = session.get(url, headers=headers, params=params)
    return resp.json()["data"]["total"]


def get_stock_list_by_page(session, page_no, page_size) -> List[Dict]:
    """
    分页 get 沪深股票列表

    Args:
        page_no: 页号 (首页为 1)
        page_size:   页大小

    Returns:
        股票列表, 带基本信息, 见 samples/stock_list.json

        fetch("http://62.push2.eastmoney.com/api/qt/clist/get?cb=jQuery1124021881304596364082_1690103811240&pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152&_=1690103811241", {
        "headers": {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8"
        },
        "referrer": "http://quote.eastmoney.com/center/gridlist.html",
        "referrerPolicy": "unsafe-url",
        "body": null,
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
        });

    Updates:
        2023-07-23:
            停牌的股票没有数据, 返回的都是"-". 只能再用雪球的 stock_profile 再挨个取.
    """

    url = "http://62.push2.eastmoney.com/api/qt/clist/get"
    headers = {
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)",
        "Accept": "*/*",
        "Referer": "http://quote.eastmoney.com/center/gridlist.html",
    }
    params = {
        "pn": page_no,
        "pz": page_size,
        "po": "1",
        "np": "1",
        "fid": "f20",  # 按市值排序
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f2,f3,f4,f5,f6,f7,f8,f12,f13,f14,f20,f21,f38,f39,f37,f23,f114,f9,f26,f112",
    }
    resp = session.get(url, headers=headers, params=params)
    return resp.json()["data"]["diff"]


def _parse_fields(data):
    return {
        "code": data["f12"],
        "name": data["f14"].replace(" ", ""),
        "market": "sh" if data["f13"] == 1 else "sz",
        "list_date": data["f26"],
        "total_value": data["f20"],
        "float_value": data["f21"],
        "total_shares": data["f38"],
        "float_shares": data["f39"],
        "roe": data["f37"],
        "eps": data["f112"],
        "pb": data["f23"],
        "pe_lyr": data["f114"],
        "pe_forecast": data["f9"],
        "price": data["f2"],
        "change": data["f3"],
        "volume": data["f5"],
        "amount": data["f6"],
        "amplitude": data["f7"],
        "turnover": data["f8"],
    }


def get_stock_list() -> List[Dict]:
    ses = requests.Session()
    stock_list = []
    total = get_stock_total(ses)
    page_no = 1
    page_size = 500
    total_page = (total + page_size - 1) // page_size
    while page_no <= total_page:
        data = get_stock_list_by_page(ses, page_no, page_size)
        page_no += 1
        stock_list.extend([_parse_fields(d) for d in data])
    return stock_list


if __name__ == "__main__":
    stock_list = get_stock_list()
    op_list = []
    for stock in stock_list:
        doc = {
            "code": stock["code"],
            "name": stock["name"],
            "market": stock["market"],
            "list_date": stock["list_date"],
            "profile": stock,
            "update_time": datetime.now(),
        }
        stock_code = stock["code"]
        del stock["code"]
        del stock["name"]
        del stock["market"]
        del stock["list_date"]
        op_list.append(
            pymongo.UpdateOne(
                {"_id": stock_code},
                {"$set": doc},
                upsert=True,
            )
        )
    db.Stock.bulk_write(op_list)
