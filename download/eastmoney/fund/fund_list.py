#!/usr/bin/env python3
# coding: utf-8

"""
    获取某家基金公司旗下的基金列表（按资产规模排序）
    数据保存到 mongodb 的 fund collection

    Preconditions:
        - mongodb collection: fund_company, fund
"""

import argparse
import logging
import pymongo
import requests
from bs4 import BeautifulSoup
from enum import Enum

from download.eastmoney.fund import db
from util.strconv import to_float


# 基金类型
class FondType(Enum):
    Stock = "001"  # 股票型
    Hybrid = "002"  # 混合型


def _parse_tr(tr):
    """ 从 tr 提取基金数据并返回 """
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
        name=a[0].text,  # 基金名
        code=a[1].text,  # 基金代码
        size=to_float(tds[8].text),  # 基金规模
        manager=tds[9].text.strip().split(" ")[0],  # 基金经历
    )


def get_fund_list_of_company(session, company_id, fund_type):
    """拉取某家基金公司旗下的基金列表

    Args:
        compoany_id: 东方财富的基金公司 gsid
        fund_type: 基金类型: 001(股票型) 或 002(混合型)
    """

    url = "http://fund.eastmoney.com/Company/home/KFSFundNet"
    headers = {
        "Host": "fund.eastmoney.com",
        "Connection": "keep-alive",
        "Accept": "text/html, */*; q=0.01",
        "Referer": "http://fund.eastmoney.com/Company/{gsid}.html".format(gsid=company_id),
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/87.0.4280.141 Safari/537.36",
    }
    params = {
        "gsid": company_id,
        "fundType": fund_type,
    }
    resp = session.get(url, headers=headers, params=params)

    html = BeautifulSoup(resp.content, features="html.parser")
    trs = html.find("tbody").find_all("tr")
    fund_list = []
    for tr in trs:
        fund = _parse_tr(tr)
        if not fund:
            continue
        fund["co_id"] = company_id
        fund["type"] = {"001": "stock", "002": "hybrid"}.get(fund_type, "")
        fund_list.append(fund)
    fund_list.sort(reverse=True, key=lambda x: x["size"])

    return fund_list


def _store_fund_list(fund_list, co_name):
    op_list = []
    for fund in fund_list:
        # 跳过B类，C类基金
        if fund["name"][-1] in "BC":
            continue
        fund["co_name"] = co_name
        op_list.append(
            pymongo.UpdateOne(
                {"_id": fund["code"]},
                {"$set": fund},
                upsert=True,
            )
        )
    db.Fund.bulk_write(op_list)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-t", "--type", help="基金类型: 001(股票型) 002(混合型)", type=str, default="002")
    args = parser.parse_args()

    sess = requests.Session()

    co_list = list(db.FundCompany.find())
    for co in co_list:
        if args.type in ["001", "002"]:
            funds = get_fund_list_of_company(sess, co["gsid"], args.type)
        else:
            funds = get_fund_list_of_company(sess, co["gsid"], "001") + get_fund_list_of_company(sess, co["gsid"], "002")
        if not funds:
            logging.warning("no funds: %s %s", co["gsid"], co["name"])
            continue
        _store_fund_list(funds, co["name"])
