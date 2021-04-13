#!/usr/bin/env python3
# coding: utf-8

"""
    调用 eastmoeny 接口获取基金报告期股票持仓
    数据更新到 mongodb 的 fund collection

    Preconditions:
        - mongodb collection: fund, stock_profile
"""

import logging
import pymongo
import requests
from bs4 import BeautifulSoup

from download.eastmoney.fund import db
from setting import REPORT_DATE
from util.progress_bar import print_progress_bar
from util.strconv import to_float, to_percent


def _parse_tr(tr):
    # <tr>
    #    <td>1</td>
    #    <td><a href="http://quote.eastmoney.com/sz002352.html">002352</a></td>
    #    <td class="tol"><a href="http://quote.eastmoney.com/sz002352.html">顺丰控股</a></td>
    #    <td class="xglj"><a href="http://fundf10.eastmoney.com/ccbdxq_001975_002352.html"</td>
    #    <td> ... </td>
    #    <td class="tor">5.03%</td>
    #    <td class="tor">358.87</td>
    #    <td class="tor">31,662.68</td>
    # </tr>
    tds = tr.find_all("td")

    # 加*号代表进入上市公司的十大流通股东却没有进入单只基金前十大重仓股的个股
    if "*" in tds[0]:
        return None

    return dict(
        code=tds[1].text,
        name=tds[2].text,
        percent=to_percent(tds[-3].text),
        volume=to_float(tds[-2].text.replace(",", "")),
        value=to_float(tds[-1].text.replace(",", "")),
    )


def get_stock_position_history_of_fund(session, fund_code):
    """
    拉取基金持仓历史数据，按报告期列表 (order by report date)

    Args:
        fund_code: 基金代码

    数据样例:
        sample/fund_stock_position.html
    """

    url = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx"
    headers = {
        "Host": "fundf10.eastmoney.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/87.0.4280.141 Safari/537.36",
        "Accept": "*/*",
        "Referer": "http://fundf10.eastmoney.com/ccmx_001975.html",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    }
    params = {
        "type": "jjcc",
        "code": fund_code,
        "topline": "15",
    }
    resp = session.get(url, headers=headers, params=params)

    position_history = []

    html = BeautifulSoup(resp.content, features="html.parser")
    divs = html.find_all("div", "box")
    for div in divs:
        position_list = []
        date = div.find("font").text
        trs = div.find("tbody")("tr")
        for tr in trs:
            p = _parse_tr(tr)
            if not p:
                continue
            position_list.append(p)
        position_history.append(
            dict(
                date=date,
                position=position_list,
            )
        )

    return position_history


def get_stock_position_history_of_funds(fund_list):
    """
    拉取多个基金的持仓历史数据
    打印进度条
    """

    sess = requests.Session()

    progress_total = len(fund_list)
    print_progress_bar(0, progress_total, length=40)

    all_data = []
    for i, f in enumerate(fund_list):
        position_history = get_stock_position_history_of_fund(sess, f["_id"])
        if len(position_history) == 0:
            logging.warning("empty position_history: {} {}".format(f["_id"], f["name"]))
            continue
        all_data.append(
            {
                "fund_id": f["_id"],
                "position_history": position_history,
            }
        )
        print_progress_bar(i + 1, progress_total, length=40)

    return all_data


def _set_position_volume_in_float(position_history_list, stock_profiles):
    for i in position_history_list:
        if not i["position_history"]:
            continue
        for ph in i["position_history"]:
            for st in ph["position"]:
                if st["code"] not in stock_profiles:
                    st["volume_in_float"] = 0.0
                    continue
                st["volume_in_float"] = round(st["volume"] * 10000 * 100 / stock_profiles[st["code"]]["float_shares"], 3)


def _store_fund_stock_position_list(stock_position_list):
    op_list = []
    for sp in stock_position_list:
        op_list.append(
            pymongo.UpdateOne(
                {"_id": sp["fund_id"]},
                {"$set": {"position_history": sp["position_history"]}},
                upsert=True,
            )
        )
    db.Fund.bulk_write(op_list)


if __name__ == "__main__":
    fund_list = list(
        db.Fund.find(
            {"position_history.0.date": {"$ne": REPORT_DATE}},
            projection=["_id", "name"],
        )
    )

    all_position_history = get_stock_position_history_of_funds(fund_list)

    stock_profiles = {st["_id"]: st["profile"] for st in db.Stock.find(projection=["profile"])}
    _set_position_volume_in_float(all_position_history, stock_profiles)

    _store_fund_stock_position_list(all_position_history)
