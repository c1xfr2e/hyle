#!/usr/bin/env python3
# coding: utf-8

import pymongo

from download.eastmoney.fund import db
from download.eastmoney.fund.fund_stock_position import set_position_volume_in_float

if __name__ == "__main__":

    fund_list = list(db.Fund.find(projection=["position"]))
    stock_profiles = {st["_id"]: st["profile"] for st in db.Stock.find(projection=["profile"])}
    set_position_volume_in_float(stock_profiles, fund_list)

    db.Fund.bulk_write(
        [
            pymongo.UpdateOne(
                {"_id": f["_id"]},
                {"$set": {"position": f["position"]}},
            )
            for f in fund_list
        ]
    )
