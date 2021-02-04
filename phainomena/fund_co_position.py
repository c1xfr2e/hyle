#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo
from pprint import pprint
from phainomena import db


REPORT_DATE = "2020-12-31"


SAMPLE = {
    "600000": {
        "002116": {
            "code": "600000",
            "name": "江苏银行",
            "percent": 0.54,
            "volume": 959.54,
            "value": 5239.11,
        },
        "123100": {
            "code": "600000",
            "name": "江苏银行",
            "percent": 0.54,
            "volume": 959.54,
            "value": 5239.11,
        },
    }
}


def aggregate_funds_position_by_company(company, fund_list):
    results = {}
    for fund in fund_list:
        for position in fund["position"]:
            result_at_date = results.setdefault(position["date"], {})
            for stock in position["position"]:
                stock_pos_dict = result_at_date.setdefault(stock["code"], {})
                stock_pos_dict[fund["_id"]] = stock
    pprint(results)


def _run_aggregate_funds_position_by_company():
    company_cols = db.FundCompany.find({"_id": "80050229"})
    for co in company_cols:
        funds = list(db.Fund.find({"co_id": co["_id"]}))
        aggregate_funds_position_by_company(co, funds)


if __name__ == "__main__":
    _run_aggregate_funds_position_by_company()
