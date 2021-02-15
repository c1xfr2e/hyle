#!/usr/bin/env python3
# coding: utf-8

"""
    获取某家基金公司旗下的基金列表（按资产规模排序）
"""

import logging
import pymongo
from bs4 import BeautifulSoup
from enum import Enum


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
    if not a:
        logging.warning("unexpected tr %s", tr)
        return None
    return dict(
        name=a[0].text,
        code=a[1].text,
        size=_to_float(tds[8].text),
        manager=tds[9].text.strip().split(" ")[0],
    )


def get_fund_list(session, co_gsid, fund_type):
    url = "http://fund.eastmoney.com/Company/home/KFSFundNet"
    headers = {
        "Host": "fund.eastmoney.com",
        "Connection": "keep-alive",
        "Accept": "text/html, */*; q=0.01",
        "Referer": "http://fund.eastmoney.com/Company/{gsid}.html".format(gsid=co_gsid),
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/87.0.4280.141 Safari/537.36",
    }
    params = {
        "gsid": co_gsid,
        "fundType": fund_type,
    }
    resp = session.get(url, headers=headers, params=params)

    html = BeautifulSoup(resp.content, features="html.parser")
    trs = html.find("tbody").find_all("tr")
    funds = []
    for tr in trs:
        f = _parse_tr(tr)
        if not f:
            continue
        f["co_id"] = co_gsid
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


def _company_filter():
    return {}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-t", "--type", help="基金类型: 001(股票型) 002(混合型)", type=str, default="002")
    args = parser.parse_args()

    import requests
    from download.eastmoney.fund import db

    companies = db.FundCompany.find(_company_filter())
    sess = requests.Session()
    for co in companies:
        if args.type in ["001", "002"]:
            funds = get_fund_list(sess, co["gsid"], args.type)
        else:
            funds = get_fund_list(sess, co["gsid"], "001") + get_fund_list(sess, co["gsid"], "002")
        if not funds:
            logging.warning("no funds: %s %s", co["gsid"], co["name"])
            continue
        store_fund_list(db.Fund, funds, co["name"])
