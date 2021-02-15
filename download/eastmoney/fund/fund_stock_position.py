#!/usr/bin/env python3
# coding: utf-8

"""
    获取基金股票持仓
"""

import logging
import pymongo
from bs4 import BeautifulSoup


def _to_float(text):
    if not text or text in ["-", "--", "---"]:
        return 0.0
    return float(text)


def _to_percent(text):
    if not text[-1] == "%":
        return 0.0
    return float(text[0:-1])


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
        percent=_to_percent(tds[-3].text),
        volume=_to_float(tds[-2].text.replace(",", "")),
        value=_to_float(tds[-1].text.replace(",", "")),
    )


def get_fund_stock_position(session, fund_code):
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

    position_by_date_list = []
    html = BeautifulSoup(resp.content, features="html.parser")
    divs = html.find_all("div", "box")
    for div in divs:
        position = []
        date = div.find("font").text
        trs = div.find("tbody")("tr")
        for tr in trs:
            tr_data = _parse_tr(tr)
            if not tr_data:
                continue
            position.append(tr_data)
        position_by_date_list.append(
            dict(
                date=date,
                position=position,
            )
        )

    return position_by_date_list


def set_position_volume_in_float(stock_profile_dict, fund_position_list):
    for fp in fund_position_list:
        if not fp["position_by_date"]:
            continue
        for position_by_date in fp["position_by_date"]:
            for st in position_by_date["position"]:
                if st["code"] not in stock_profile_dict:
                    st["volume_in_float"] = 0.0
                    continue
                st["volume_in_float"] = round(st["volume"] * 10000 * 100 / stock_profile_dict[st["code"]]["float_shares"], 3)


def store_fund_stock_position_list(mongo_col, stock_position_list):
    op_list = []
    for sp in stock_position_list:
        op_list.append(
            pymongo.UpdateOne(
                {"_id": sp["fund_id"]},
                {"$set": {"position_by_date": sp["position_by_date"]}},
                upsert=True,
            )
        )
    mongo_col.bulk_write(op_list)


def _fund_filter():
    return {"position_by_date.0": {"$exists": 0}}


if __name__ == "__main__":
    import requests
    from download.eastmoney.fund import db
    from util.progress_bar import print_progress_bar

    sess = requests.Session()

    funds = list(db.Fund.find(_fund_filter(), projection=["_id", "name"]))

    progress_total = len(funds)
    print_progress_bar(0, progress_total, length=40)

    all_position_by_date = []
    for i, f in enumerate(funds):
        position_by_date = get_fund_stock_position(sess, f["_id"])
        if len(position_by_date) == 0:
            logging.warning("empty position_by_date: {} {}".format(f["_id"], f["name"]))
            continue
        all_position_by_date.append(
            {
                "fund_id": f["_id"],
                "position_by_date": position_by_date,
            }
        )
        print_progress_bar(i + 1, progress_total, length=40)

    stock_profiles = {st["_id"]: st["profile"] for st in db.Stock.find(projection=["profile"])}
    set_position_volume_in_float(stock_profiles, all_position_by_date)

    store_fund_stock_position_list(db.Fund, all_position_by_date)
