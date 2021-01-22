#!/usr/bin/env python3
# coding: utf-8
"""
    获取某家基金公司旗下的基金列表（按资产规模排序）
"""

from bs4 import BeautifulSoup
from enum import Enum


# 机构类型
class FondType(Enum):
    Stock = "001"  # 股票型
    Hybrid = "002"  # 混合型


def _parse_row(row):
    tds = row.find_all("td")
    a = tds[0].findChildren()  # <td class="fund-name-code">
    return dict(
        name=a[0].text,
        code=a[1].text,
        size=float(tds[8].text),
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
    rows = html.find("tbody").find_all("tr")
    funds = [_parse_row(r) for r in rows]
    funds.sort(reverse=True, key=lambda x: x["size"])
    return funds


if __name__ == "__main__":
    import requests
    from pprint import pprint

    fund_list = get_fund_list(requests.Session(), "80000251", FondType.Stock.value)
    pprint(fund_list)
