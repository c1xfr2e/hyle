#!/usr/bin/env python3
# coding: utf-8


from phainomena import db
import pymongo


REPORT_DATE = "2020-12-31"


SAMPLE = {
    "name": "金螳螂",
    "code": "002081",
    "position": [
        {
            "fund_code": "001221",
            "fund_name": "广发工程基建指数",
            "fund_size": 18.3,
            "volume": 1000,
            "volume_in_float": 0.2,
        }
    ],
    "enter": [],
    "exit": [],
    "inc_dec": [],
}


all_stock_fund_position = {}


def _aggregate_fund_position(fund):
    for p in fund["position_by_date"][0]["position"]:
        stock_position_list = all_stock_fund_position.setdefault(p["code"], [])
        stock_position_list.append(
            {
                "co_id": fund["co_id"],
                "co_name": fund["co_name"],
                "fund_code": fund["code"],
                "fund_name": fund["name"],
                "fund_size": fund["size"],
                "percent": p["percent"],
                "volume": p["volume"],
                "volume_in_float": p.get("volume_in_float", 0),
            }
        )


def obtain_all_stock_fund_position():
    fund_list = list(
        db.Fund.find(
            {
                "$where": "this.position_by_date.length>1",
                "position_by_date.0.date": REPORT_DATE,
            }
        )
    )
    for fund in fund_list:
        _aggregate_fund_position(fund)


if __name__ == "__main__":
    stocks_dict = {st["_id"]: st for st in list(db.Stock.find(projection=["name"]))}

    obtain_all_stock_fund_position()

    write_op_list = []
    for stock_code, fund_position in all_stock_fund_position.items():
        if stock_code not in stocks_dict:
            continue
        stock = stocks_dict[stock_code]
        fund_position.sort(key=lambda x: x["volume_in_float"], reverse=True)
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": stock_code},
                {
                    "$set": {
                        "name": stock["name"],
                        "position": fund_position,
                    }
                },
                upsert=True,
            )
        )
    db.StockFundPosition.bulk_write(write_op_list)
