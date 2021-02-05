#!/usr/bin/env python3
# coding: utf-8

"""
    获取基金持仓情况
"""

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

    stock_position_list = []
    html = BeautifulSoup(resp.content, features="html.parser")
    divs = html.find_all("div", "box")
    for div in divs:
        stock_position = []
        date = div.find("font").text
        trs = div.find("tbody")("tr")
        for tr in trs:
            tr_data = _parse_tr(tr)
            if not tr_data:
                continue
            stock_position.append(tr_data)
        stock_position_list.append(
            dict(
                date=date,
                stock=stock_position,
            )
        )

    return stock_position_list


def store_fund_stock_position_list(mongo_col, stock_position_list):
    ops = [
        pymongo.UpdateOne(
            {"_id": sp["fund_id"]},
            {"$set": {"position": sp["position"]}},
        )
        for sp in stock_position_list
    ]
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    import requests
    from download.eastmoney.fund import db

    sess = requests.Session()

    funds = db.Fund.find(projection=["_id"])
    position_list = [
        {
            "fund_id": f["_id"],
            "position": get_fund_stock_position(sess, f["_id"]),
        }
        for f in funds
    ]

    store_fund_stock_position_list(db.Fund, position_list)
