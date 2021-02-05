#!/usr/bin/env python3
# coding: utf-8

"""
调用 <东方财富> web 接口获取一只股票的机构持仓情况 (各类机构的持仓比例)

返回数据格式:
    见 samples/main_positions.json
"""

import requests

from collections import namedtuple
from datetime import date, datetime
from enum import Enum
from typing import List

from util import to_percent


# 机构类型
class InstitutionType(Enum):
    Fund = "基金"
    Insurance = "保险"
    OFII = "QFII"
    SocialSecurity = "社保基金"
    Securities = "券商"
    Trust = "信托"
    Other = "其他机构"


# 机构持仓情况
InstitutionPosition = namedtuple(
    "InstitutionPosition",
    [
        "type",  # 机构类型
        "number",  # 机构家数
        "amount",  # 持股数量
        "proportion",  # 占流通股本比例
    ],
)


session = requests.Session()


def get_institution_positions(stock_code, date) -> List[InstitutionPosition]:
    """获取机构持仓情况

    stock_code -- 6 位股票代码
    date       -- 截止日期
    """
    url = "http://f10.eastmoney.com/ShareholderResearch/MainPositionsHodlerAjax"
    params = {
        "code": "{}{}".format("SH" if stock_code.startswith("6") else "SZ", stock_code),
        "date": datetime.strftime(date, "%Y-%m-%d"),
    }
    resp = session.get(url, params=params)
    data = resp.json()
    institution_positions = [
        InstitutionPosition(
            type=r["jglx"],
            number=0 if r["ccjs"] == "--" else int(r["ccjs"]),
            amount=0 if r["ccgs"] == "--" else int(r["ccgs"]),
            proportion=0 if r["zltgbl"] == "--" else to_percent(r["zltgbl"]),
        )
        for r in data
    ]
    return institution_positions


if __name__ == "__main__":
    print(get_institution_positions("300413", date(2019, 6, 30)))
