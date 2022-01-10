#!/usr/bin/env python3
# coding: utf-8

"""
    对比基金最新两季持仓，得出持仓变动

    Preconditions:
        - mongodb documents: fund
        - fund 中已有 position_history 数据
"""

import pymongo
from enum import Enum

import db
from setting import REPORT_DATE

# 持仓变动类型
class PositionChange(Enum):
    Enter = "enter"  # 新进
    Inc = "inc"  # 加仓
    Dec = "dec"  # 减仓
    Exit = "exit"  # 退出


def diff_fund_position(new, old):
    """
    比较两个基金持仓, 得出 diff

    Args:
        new: 新持仓
        old: 旧持仓

    Returns:
        enter_list:  新进列表
        inc_dec_list: 增减仓列表
        exit_list: 退出列表
    """
    new_dict = {p["code"]: p for p in new}
    old_dict = {p["code"]: p for p in old}

    enter_codes = set(new_dict) - set(old_dict)
    exit_codes = set(old_dict) - set(new_dict)
    inc_dec_codes = set(old_dict) & set(new_dict)

    enter_list, inc_dec_list, exit_list = [], [], []

    for code in enter_codes:
        p = new_dict[code]
        enter_list.append(
            {
                "name": p["name"],
                "code": p["code"],
                "quantity": p["quantity"],
                "value": p["value"],
                "float_percent": p["float_percent"],
                "net_percent": p["net_percent"],
            }
        )

    for code in exit_codes:
        p = old_dict[code]
        exit_list.append(
            {
                "name": p["name"],
                "code": p["code"],
                "quantity": p["quantity"],
                "value": p["value"],
                "float_percent": p["float_percent"],
                "net_percent": p["net_percent"],
            }
        )

    for code in inc_dec_codes:
        pnew, pold = new_dict[code], old_dict[code]
        quantity_change = pnew["quantity"] * 10000 - pold["quantity"] * 10000
        if quantity_change == 0:
            continue
        inc_dec_list.append(
            {
                "name": pnew["name"],
                "code": pnew["code"],
                "quantity": round(quantity_change / 10000, 2),
                "value": round(pnew["value"] - pold["value"], 2),
                "float_percent": round(pnew["float_percent"] - pold["float_percent"], 3),
                "net_percent": round(pnew["net_percent"] - pold["net_percent"], 2),
                "net_percent_new": pnew["net_percent"],
                "net_percent_old": pold["net_percent"],
            }
        )

    enter_list.sort(key=lambda x: x["net_percent"], reverse=True)
    inc_dec_list.sort(key=lambda x: x["net_percent"], reverse=True)
    exit_list.sort(key=lambda x: x["net_percent"], reverse=True)

    return enter_list, inc_dec_list, exit_list


def _write_op(fund, enter_list, inc_dec_list, exit_list):
    return pymongo.UpdateOne(
        {"_id": fund["_id"]},
        {
            "$set": {
                "house_id": fund["house_id"],
                "co_name": fund["co_name"],
                "date": fund["position_history"][0]["date"],
                "name": fund["name"],
                "size": fund["size"],
                "manager": fund["manager"],
                "enter": enter_list,
                "exit": exit_list,
                "inc_dec": inc_dec_list,
            }
        },
        upsert=True,
    )


if __name__ == "__main__":
    funds = db.Fund.find(
        {
            "$where": "this.position_history.length>1",
            "position_history.0.date": REPORT_DATE,
        }
    )

    write_op_list = []
    for f in funds:
        enter, inc_dec, exit_ = diff_fund_position(
            f["position_history"][0]["position"],
            f["position_history"][1]["position"],
        )
        write_op_list.append(_write_op(f, enter, inc_dec, exit_))

    db.FundPositionChange.bulk_write(write_op_list)
