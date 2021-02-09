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


def diff_co_stock_position_change(new_position_dict, old_position_dict):
    enter_stock_codes = set(new_position_dict) - set(old_position_dict)
    # exit_stock_codes = set(old_position_dict) - set(new_position_dict)

    enter_list, exit_list = [], []

    for code in enter_stock_codes:
        volume, value, volume_in_float, total_percent = 0, 0, 0, 0
        fund_position = new_position_dict[code]
        for fp in fund_position:
            sp = fp["position"]
            volume += sp["volume"]
            value += sp["value"]
            volume_in_float += sp.get("volume_in_float", 0.0)
            total_percent += sp["percent"]
        enter_list.append(
            {
                "code": code,
                "name": fund_position[0]["position"]["name"],
                "volume": round(volume, 2),
                "value": round(value, 2),
                "volume_in_float": round(volume_in_float, 2),
                "total_percent": round(total_percent, 2),
                "fund_count": len(fund_position),
            }
        )

    enter_list.sort(key=lambda x: x["volume_in_float"], reverse=True)

    return enter_list, exit_list


def obtain_company_position_change(report_date):
    co_position_change_list = []
    co_position_col = db.FundCompanyPosition.find().sort("size", pymongo.DESCENDING)
    for cop in co_position_col:
        list_by_date = cop["list_by_date"]
        if len(list_by_date) < 2 or list_by_date[0]["date"] != report_date:
            continue
        enter_list, exit_list = diff_co_stock_position_change(
            list_by_date[0]["stock_position"],
            list_by_date[1]["stock_position"],
        )
        co_position_change_list.append(
            {
                "_id": cop["_id"],
                "co_name": cop["co_name"],
                "co_size": cop["co_size"],
                "enter": enter_list,
                # "exit": exit_list,
            }
        )

    return co_position_change_list


if __name__ == "__main__":
    co_position_change_list = obtain_company_position_change(REPORT_DATE)
    ops = [
        pymongo.UpdateOne(
            {"_id": c["_id"]},
            {"$set": c},
            upsert=True,
        )
        for c in co_position_change_list
    ]
    db.FundCompanyPositionChange.bulk_write(ops)
