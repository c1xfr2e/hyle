#!/usr/bin/env python3
# coding: utf-8

"""
    基金最新持仓更新
"""

import pymongo
from enum import Enum

from eastmoney.fund import db


REPORT_DATE = "2020-12-31"

# 持仓变动类型
class PositionChange(Enum):
    Open = "open"  # 建仓
    Inc = "inc"  # 加仓
    Dec = "dec"  # 减仓
    Clear = "clear"  # 清仓


def diff_position(new_position, old_position):
    new = {p["code"]: p for p in new_position}
    old = {p["code"]: p for p in old_position}
    new_stock_codes = set(new) - set(old)
    delete_stock_codes = set(old) - set(new)
    update_stock_codes = set(old) & set(new)

    change_list = []

    for c in new_stock_codes:
        pos = new[c]
        change_list.append(
            {
                "type": "open",
                "name": pos["name"],
                "code": pos["code"],
                "volume": pos["value"],
                "value": pos["value"],
                "percent": pos["percent"],
            }
        )

    for c in delete_stock_codes:
        pos = old[c]
        change_list.append(
            {
                "type": "clear",
                "name": pos["name"],
                "code": pos["code"],
                "volume": pos["value"],
                "value": pos["value"],
                "percent": pos["percent"],
            }
        )

    for c in update_stock_codes:
        pnew, pold = new[c], old[c]
        volume_change = pnew["volume"] * 10000 - pold["volume"] * 10000
        if volume_change == 0:
            continue
        change_list.append(
            {
                "type": "inc" if volume_change > 0 else "dec",
                "name": pnew["name"],
                "code": pnew["code"],
                "volume": abs(round(volume_change / 10000, 2)),
                "value": abs(round(pnew["value"] - pold["value"], 2)),
                "percent": abs(round(pnew["percent"] - pold["percent"], 2)),
            }
        )

    type_sort_keys = {
        "open": 300,
        "inc": 200,
        "dec": 100,
        "clear": 0,
    }
    change_list.sort(key=lambda x: type_sort_keys[x["type"]] + x["percent"], reverse=True)

    return change_list


def store_position_change_list(mongo_col, funds):
    ops = [
        pymongo.UpdateOne(
            {"_id": f["_id"]},
            {"$set": {"position_change": f["position_change"]}},
        )
        for f in funds
    ]
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    funds = db.Fund.find(
        filter={
            "$where": "this.position.length>1",
            "position.0.date": REPORT_DATE,
        }
    )

    funds = list(funds)
    position_change_list = []
    for f in funds:
        position = f["position"]
        change = diff_position(position[0]["position"], position[1]["position"])
        f["position_change"] = change

    store_position_change_list(db.Fund, funds)
