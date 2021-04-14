#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo

import db
from setting import REPORT_DATE


FUND_POSITION_CHANGE = {
    "enter": [
        {
            "name": "金螳螂",
            "code": "002081",
            "funds": ["123012", "321002", "001002"],
        }
    ],
    "exit": [],
}


def diff_company_position(new_position_dict, old_position_dict):
    enter_stock_codes = set(new_position_dict) - set(old_position_dict)
    exit_stock_codes = set(old_position_dict) - set(new_position_dict)

    enter_list = [
        {
            "code": code,
            "name": new_position_dict[code]["name"],
            "percent": new_position_dict[code]["percent"],
            "quantity": new_position_dict[code]["quantity"],
            "funds": new_position_dict[code]["funds"],
        }
        for code in enter_stock_codes
    ]
    enter_list.sort(key=lambda x: x["percent"], reverse=True)

    exit_list = [
        {
            "code": code,
            "name": old_position_dict[code]["name"],
            "percent": old_position_dict[code]["percent"],
            "quantity": old_position_dict[code]["quantity"],
            "funds": old_position_dict[code]["funds"],
        }
        for code in exit_stock_codes
    ]
    exit_list.sort(key=lambda x: x["percent"], reverse=True)

    return enter_list, exit_list


def _position_to_dict(position):
    return {p["code"]: p for p in position}


def obtain_company_position_change(report_date):
    co_position_change_list = []
    co_positions = list(db.FundCompanyPosition.find().sort("size", pymongo.DESCENDING))
    for cop in co_positions:
        position_history = cop["position_history"]
        if len(position_history) < 2 or position_history[0]["date"] != report_date:
            continue
        enter_list, exit_list = diff_company_position(
            _position_to_dict(position_history[0]["position"]),
            _position_to_dict(position_history[1]["position"]),
        )
        co_position_change_list.append(
            {
                "_id": cop["_id"],
                "co_name": cop["co_name"],
                "co_size": cop["co_size"],
                "enter": enter_list,
                "exit": exit_list,
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
