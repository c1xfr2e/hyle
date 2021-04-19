#!/usr/bin/env python3
# coding: utf-8

"""
    比较基金公司最新两季持仓，得出持仓变动并保存

    Preconditions:
        - mongodb documents: fund_company_position

    document 格式:
        {
            "_id": "80001234",
            "co_name": "广发基金",
            "co_size": 1230.0,
            "enter": [
                {
                    "name": "金螳螂",
                    "code": "002081",
                    "net_percent": 0.2,
                    "quantity": 1200,
                    "funds": [
                        {
                            "name": "广发工程基金",
                            "code": "123012"
                        }
                    ],
                }
            ],
            "exit": [],
        }
"""

import pymongo

import db
from setting import REPORT_DATE


def diff_company_position(new_position, old_position):
    """
    比较两个基金公司持仓, 得出新进、退出列表

    Args:
        new_position: 新持仓
        old_position: 旧持仓

    Returns:
        enter_list:  新进列表
        exit_list: 退出列表
    """

    new_dict = {p["code"]: p for p in new_position}
    old_dict = {p["code"]: p for p in old_position}

    enter_stock_codes = set(new_dict) - set(old_dict)
    exit_stock_codes = set(old_dict) - set(new_dict)

    enter_list = [
        {
            "code": code,
            "name": new_dict[code]["name"],
            "net_percent": new_dict[code]["net_percent"],
            "quantity": new_dict[code]["quantity"],
            "funds": new_dict[code]["funds"],
        }
        for code in enter_stock_codes
    ]
    enter_list.sort(key=lambda x: x["net_percent"], reverse=True)

    exit_list = [
        {
            "code": code,
            "name": old_dict[code]["name"],
            "net_percent": old_dict[code]["net_percent"],
            "quantity": old_dict[code]["quantity"],
            "funds": old_dict[code]["funds"],
        }
        for code in exit_stock_codes
    ]
    exit_list.sort(key=lambda x: x["net_percent"], reverse=True)

    return enter_list, exit_list


if __name__ == "__main__":
    co_position_change_doc_list = []
    co_positions = list(db.FundCompanyPosition.find().sort("size", pymongo.DESCENDING))

    for cop in co_positions:
        position_history = cop["position_history"]
        if len(position_history) < 2 or position_history[0]["date"] != REPORT_DATE:
            continue
        enter_list, exit_list = diff_company_position(
            position_history[0]["position"],
            position_history[1]["position"],
        )
        co_position_change_doc_list.append(
            {
                "_id": cop["_id"],
                "co_name": cop["co_name"],
                "co_size": cop["co_size"],
                "enter": enter_list,
                "exit": exit_list,
            }
        )

    ops = [
        pymongo.UpdateOne(
            {"_id": doc["_id"]},
            {"$set": doc},
            upsert=True,
        )
        for doc in co_position_change_doc_list
    ]
    db.FundCompanyPositionChange.bulk_write(ops)
