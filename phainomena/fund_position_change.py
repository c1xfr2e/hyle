#!/usr/bin/env python3
# coding: utf-8

"""
    基金最新持仓更新
"""

import pymongo
from enum import Enum

from phainomena import db


REPORT_DATE = "2020-12-31"

# 持仓变动类型
class PositionChange(Enum):
    Enter = "enter"  # 新进
    Inc = "inc"  # 加仓
    Dec = "dec"  # 减仓
    Exit = "exit"  # 清仓


def diff_position(new_position, old_position):
    new_dict = {p["code"]: p for p in new_position}
    old_dict = {p["code"]: p for p in old_position}

    enter_stock_codes = set(new_dict) - set(old_dict)
    exit_stock_codes = set(old_dict) - set(new_dict)
    inc_dec_stock_codes = set(old_dict) & set(new_dict)

    enter_list, inc_dec_list, exit_list = [], [], []

    for c in enter_stock_codes:
        pos = new_dict[c]
        enter_list.append(
            {
                "name": pos["name"],
                "code": pos["code"],
                "volume": pos["volume"],
                "value": pos["value"],
                "volume_in_float": pos.get("volume_in_float", 0.0),
                "percent": pos["percent"],
            }
        )

    for c in exit_stock_codes:
        pos = old_dict[c]
        exit_list.append(
            {
                "name": pos["name"],
                "code": pos["code"],
                "volume": pos["volume"],
                "value": pos["value"],
                "volume_in_float": pos.get("volume_in_float", 0.0),
                "percent": pos["percent"],
            }
        )

    for c in inc_dec_stock_codes:
        pnew, pold = new_dict[c], old_dict[c]
        volume_change = pnew["volume"] * 10000 - pold["volume"] * 10000
        if volume_change == 0:
            continue
        inc_dec_list.append(
            {
                "name": pnew["name"],
                "code": pnew["code"],
                "volume": round(volume_change / 10000, 2),
                "value": round(pnew["value"] - pold["value"], 2),
                "volume_in_float": round(pnew.get("volume_in_float", 0.0) - pold.get("volume_in_float", 0.0), 3),
                "percent": round(pnew["percent"] - pold["percent"], 2),
                "percent_new": pnew["percent"],
                "percent_old": pold["percent"],
            }
        )

    enter_list.sort(key=lambda x: x["percent"], reverse=True)
    inc_dec_list.sort(key=lambda x: x["percent"], reverse=True)
    exit_list.sort(key=lambda x: x["percent"], reverse=True)

    return enter_list, inc_dec_list, exit_list


def _write_op(fund, enter_list, inc_dec_list, exit_list):
    return pymongo.UpdateOne(
        {"_id": fund["_id"]},
        {
            "$set": {
                "date": fund["position_by_date"][0]["date"],
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
            "$where": "this.position_by_date.length>1",
            "position_by_date.0.date": REPORT_DATE,
        }
    )

    write_op_list = []
    for f in funds:
        enter, inc_dec, exit_ = diff_position(
            f["position_by_date"][0]["position"],
            f["position_by_date"][1]["position"],
        )
        write_op_list.append(_write_op(f, enter, inc_dec, exit_))

    db.FundPositionChange.bulk_write(write_op_list)
