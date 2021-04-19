#!/usr/bin/env python3
# coding: utf-8

"""
    设置基金持仓中的流通股本比

    Preconditions:
        - mongodb documents: fund, stock_profile
        - fund 中已有 position_history 数据
"""

import pymongo

import db


if __name__ == "__main__":
    stocks = list(
        db.Stock.find(
            {"profile": {"$exists": 1}},
            projection=["profile"],
        )
    )
    sp_dict = {s["_id"]: s["profile"] for s in stocks}

    fund_list = list(
        db.Fund.find(
            {"position_history": {"$exists": 1}},
            projection=["position_history"],
        )
    )
    for f in fund_list:
        if not f["position_history"]:
            continue
        for ph in f["position_history"][0:2]:  # 只设置最新的两季
            for p in ph["position"]:
                if p["code"] not in sp_dict:
                    p["float_percent"] = 0.0
                    continue
                p["float_percent"] = round(p["quantity"] * 10000 * 100 / sp_dict[p["code"]]["float_shares"], 3)

    op_list = []
    for f in fund_list:
        op_list.append(
            pymongo.UpdateOne(
                {"_id": f["_id"]},
                {"$set": {"position_history": f["position_history"]}},
                upsert=True,
            )
        )
    db.Fund.bulk_write(op_list)
