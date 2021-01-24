#!/usr/bin/env python3
# coding: utf-8
"""
    获取某家基金公司旗下的基金列表（按资产规模排序）
"""

import logging
from enum import Enum

import pymongo
from bs4 import BeautifulSoup


# 机构类型
class FondType(Enum):
    Stock = "001"  # 股票型
    Hybrid = "002"  # 混合型


def _to_float(text):
    if not text or text == "-":
        return 0.0
    return float(text)


def _parse_tr(tr):
    tds = tr.find_all("td")
    # <td class="fund-name-code">
    #   <a>基金名</a>
    #   <a>基金代码</a>
    # </td>
    a = tds[0].findChildren()
    return dict(
        name=a[0].text,
        code=a[1].text,
        size=_to_float(tds[8].text),
        manager=tds[9].text.strip().split(" ")[0],
    )


def get_fund_list(session, gsid, fund_type):
    url = "http://fund.eastmoney.com/Company/home/KFSFundNet"
    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Referer": "http://fund.eastmoney.com/Company/{gsid}.html".format(gsid=gsid),
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/87.0.4280.141 Safari/537.36",
    }
    params = {
        "gsid": gsid,
        "fundType": fund_type,
    }
    resp = session.get(url, headers=headers, params=params)

    html = BeautifulSoup(resp.content, features="html.parser")
    trs = html.find("tbody").find_all("tr")
    funds = []
    for tr in trs:
        f = _parse_tr(tr)
        f["co_id"] = gsid
        f["type"] = {"001": "stock", "002": "hybrid"}.get(fund_type, "")
        funds.append(f)
    funds.sort(reverse=True, key=lambda x: x["size"])
    return funds


def store_fund_list(mongo_col, fund_list, co_name):
    ops = []
    for f in fund_list:
        # 跳过B类，C类基金
        if f["name"][-1] in "BC":
            continue
        f["co_name"] = co_name
        ops.append(
            pymongo.UpdateOne(
                {"_id": f["code"]},
                {"$set": f},
                upsert=True,
            )
        )
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-t", "--type", help="基金类型: 001(股票型) 002(混合型)", type=str, default="001")
    args = parser.parse_args()

    import requests
    from eastmoney import db

    companies = db.FundCompany.find({})
    sess = requests.Session()
    for co in companies:
        stock_funds = get_fund_list(sess, co["gsid"], args.type)
        if not stock_funds:
            logging.warning("no stock funds", co["gsid"], co["name"])
            continue
        store_fund_list(db.Fund, stock_funds, co["name"])
