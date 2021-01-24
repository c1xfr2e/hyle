#!/usr/bin/env python3
# coding: utf-8

"""
    获取基金季度持仓
"""

import pymongo
from bs4 import BeautifulSoup


def _to_float(text):
    if not text or text == "-":
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
    return dict(
        code=tds[1].text,
        name=tds[2].text,
        percent=_to_percent(tds[-3].text),
        share=_to_float(tds[-2].text.replace(",", "")),
        value=_to_float(tds[-1].text.replace(",", "")),
    )


def get_holdings(session, fund_code):
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

    holdings_by_date = []
    html = BeautifulSoup(resp.content, features="html.parser")
    divs = html.find_all("div", "box")
    for div in divs:
        holdings = []
        date = div.find("font").text
        trs = div.find("tbody")("tr")
        for tr in trs:
            r = _parse_tr(tr)
            holdings.append(r)
        holdings_by_date.append(
            dict(
                date=date,
                holdings=holdings,
            )
        )

    return holdings_by_date


def store_holdings_list(mongo_col, holdings_list):
    ops = [
        pymongo.UpdateOne(
            {"_id": holdings["fund_id"]},
            {"$set": {"holdings": holdings["holdings"]}},
        )
        for holdings in holdings_list
    ]
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    import requests
    from eastmoney import db

    sess = requests.Session()

    funds = db.Fund.find(
        filter={"holdings": {"$exists": 0}},
        projection=["_id"],
    )
    holdings_list = [
        {
            "fund_id": f["_id"],
            "holdings": get_holdings(sess, f["_id"]),
        }
        for f in funds
    ]

    store_holdings_list(db.Fund, holdings_list)
