#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo

from phainomena import db


REPORT_DATE = "2020-12-31"

fund_position_change = {
    "enter": [
        {
            "name": "金螳螂",
            "code": "002081",
            "volume": 10000,
            "value": 1000025,
            "volume_in_float": 0.25,
            "total_percent": 6.6,
            "fund_count": 5,
        }
    ],
    "exit": [],
}


def diff_co_stock_position_change(new, old, co_stock_position):
    enter_stock_codes = set(new) - set(old)
    # exit_stock_codes = set(old) - set(new)

    enter_list, exit_list = [], []

    for code in enter_stock_codes:
        volume, value, volume_in_float = 0.0, 0.0, 0.0
        fund_stock_position = co_stock_position[code]
        for fsp in fund_stock_position:
            sp = fsp["position"]
            volume += sp["volume"]
            value + sp["value"]
            volume_in_float += sp["volume_in_float"]
        enter_list.append(
            {
                "code": code,
                "name": fund_stock_position[0]["position"]["name"],
                "volume": volume,
                "value": value,
                "volume_in_float": volume_in_float,
                "total_percent": None,
                "fund_count": len(fsp),
            }
        )

    return enter_list, exit_list


def obtain_company_position_change(report_date):
    co_position_change_list = []
    co_position_col = db.FundCompanyPosition.find().sort({"size": -1})
    for cop in co_position_col:
        list_by_date = cop["list_by_date"]
        if len(list_by_date) < 2:
            continue
        change = diff_co_stock_position_change(list_by_date[0], list_by_date[1])
        co_position_change_list.append(change)

    return co_position_change_list


if __name__ == "__main__":
    co_position_change_list = obtain_company_position_change(REPORT_DATE)
    ops = [
        pymongo.UpdateOne(
            {"co_id": r["co_id"], "date": r["date"]},
            {"$set": r},
            upsert=True,
        )
        for r in co_position_change_list
    ]
    db.CompanyPositionUpdate.bulk_write(ops)
