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
            "percent": 5.5,
            "volume": 1000,
            "volume_in_float": 0.2,
        }
    ],
    "enter": [
        {
            "fund_code": "001221",
            "fund_name": "广发工程基建指数",
            "percent": 5.5,
            "volume": 1000,
            "volume_in_float": 0.08,
        }
    ],
    "exit": [
        {
            "fund_code": "001221",
            "fund_name": "广发工程基建指数",
            "percent": 5.5,
            "volume": 1000,
            "volume_in_float": 0.08,
        }
    ],
    "inc_dec": [
        {
            "fund_code": "001221",
            "fund_name": "广发工程基建指数",
            "percent": -0.5,
            "volume": -1000,
            "volume_in_float": -0.08,
        }
    ],
}


all_stock_fund_position = {}
all_stock_fund_enter = {}
all_stock_fund_exit = {}
all_stock_fund_inc_dec = {}


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
                "volume_in_float": p["volume_in_float"],
            }
        )


def _aggregate_position_change(fund_change):
    for e in fund_change["enter"]:
        enter_list = all_stock_fund_enter.setdefault(e["code"], [])
        enter_list.append(
            {
                "fund_code": fund_change["_id"],
                "fund_name": fund_change["name"],
                "percent": e["percent"],
                "volume": e["volume"],
                "volume_in_float": e["volume_in_float"],
            }
        )
    for e in fund_change["exit"]:
        exit_list = all_stock_fund_exit.setdefault(e["code"], [])
        exit_list.append(
            {
                "fund_code": fund_change["_id"],
                "fund_name": fund_change["name"],
                "percent": e["percent"],
                "volume": e["volume"],
                "volume_in_float": e["volume_in_float"],
            }
        )
        pass
    for i in fund_change["inc_dec"]:
        inc_dec_list = all_stock_fund_inc_dec.setdefault(i["code"], [])
        inc_dec_list.append(
            {
                "fund_code": fund_change["_id"],
                "fund_name": fund_change["name"],
                "percent": i["percent"],
                "volume": i["volume"],
                "volume_in_float": i["volume_in_float"],
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


def obtain_all_stock_fund_position_change():
    change_list = list(
        db.FundPositionChange.find(
            {
                "date": REPORT_DATE,
            }
        )
    )
    for change in change_list:
        _aggregate_position_change(change)


if __name__ == "__main__":
    stocks_dict = {st["_id"]: st for st in list(db.Stock.find(projection=["name"]))}

    obtain_all_stock_fund_position()
    obtain_all_stock_fund_position_change()

    write_op_list = []
    for code, stock in stocks_dict.items():
        position = all_stock_fund_position.get(code, [])
        position.sort(key=lambda x: x["volume"], reverse=True)
        enter = all_stock_fund_enter.get(code, [])
        enter.sort(key=lambda x: x["volume"], reverse=True)
        exit_ = all_stock_fund_exit.get(code, [])
        exit_.sort(key=lambda x: x["volume"], reverse=True)
        inc_dec = all_stock_fund_inc_dec.get(code, [])
        inc_dec.sort(key=lambda x: x["volume"], reverse=True)
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": code},
                {
                    "$set": {
                        "name": stock["name"],
                        "position": position,
                        "enter": enter,
                        "exit": exit_,
                        "inc_dec": inc_dec,
                    }
                },
                upsert=True,
            )
        )

    db.StockFundPosition.bulk_write(write_op_list)
