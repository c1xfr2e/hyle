#!/usr/bin/env python3
# coding: utf-8

"""
    调用 eastmoeny 接口获取基金报告期股票持仓
    数据更新到 mongodb 的 fund collection

    Preconditions:
        - mongodb documents: fund
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
        net_percent=to_percent(tds[-3].text),
        quantity=to_float(tds[-2].text.replace(",", "")),
        value=to_float(tds[-1].text.replace(",", "")),
    )


def get_position_history_of_fund(session, fund_code, report_year):
    """
    拉取基金持仓历史数据，按报告期列表 (order by report date)

    Args:
        fund_code: 基金代码
        report_year: 报告期年份

    Returns:
        持仓历史列表: List[Dict]

    东方财富接口数据样例:
        sample/fund_position.html
    """

    url = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx"
    headers = {
        "Host": "fundf10.eastmoney.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) Chrome/87.0.4280.141 Safari/537.36",
        "Accept": "*/*",
        # "Referer": "http://fundf10.eastmoney.com/ccmx_{code}.html".format(code=fund_code),
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
    }
    params = {
        "type": "jjcc",
        "code": fund_code,
        "topline": "15",
        "year": report_year,
    }
    resp = session.get(url, headers=headers, params=params)

    # 检查 arryear 中的是否有当前年
    i = resp.text.rfind("arryear:[") + len("arryear:[")
    arryear = resp.text[i:]
    if report_year not in arryear:
        return None

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

    # if not position_history:
    #     logging.warning("empty position_history: {}\n".format(fund_code))

    return position_history


def get_position_history_of_funds(fund_list, year):
    """
    拉取多个基金的持仓历史数据
    打印进度条
    """

    sess = requests.Session()

    progress_total = len(fund_list)
    print_progress_bar(0, progress_total, length=40)

    all_data = []
    for i, f in enumerate(fund_list):
        position_history = get_position_history_of_fund(sess, f["_id"], year)
        if position_history:
            all_data.append(
                {
                    "fund_id": f["_id"],
                    "position_history": position_history,
                }
            )
        print_progress_bar(i + 1, progress_total, length=40)

    return all_data


def _merge_with_existing(fund_list, all_fund_ph):
    funds_dict = {f["_id"]: f.get("position_history") for f in fund_list}
    for fph in all_fund_ph:
        existing_ph = funds_dict[fph["fund_id"]]
        if not existing_ph:
            continue
        new_ph = fph["position_history"]
        existing_date = existing_ph[0]["date"]
        i = 0
        while i < len(new_ph) and new_ph[i]["date"] > existing_date:
            i += 1
        fph["position_history"] = new_ph[0:i] + existing_ph


def _store_all_fund_position_history(all_fund_ph):
    op_list = []
    for ph in all_fund_ph:
        op_list.append(
            pymongo.UpdateOne(
                {"_id": ph["fund_id"]},
                {"$set": {"position_history": ph["position_history"]}},
                upsert=True,
            )
        )
    if op_list:
        db.Fund.bulk_write(op_list)


if __name__ == "__main__":
    fund_list = list(
        db.Fund.find(
            {"position_history.0.date": {"$ne": REPORT_DATE}},
            projection=["_id", "name", "position_history"],
        )
    )

    all_fund_ph = get_position_history_of_funds(fund_list, REPORT_DATE[0:4])

    _merge_with_existing(fund_list, all_fund_ph)

    _store_all_fund_position_history(all_fund_ph)
