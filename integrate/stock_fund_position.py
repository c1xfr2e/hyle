#!/usr/bin/env python3
# coding: utf-8

"""
    统计每个股票的基金仓位

    Preconditions:
        - mongodb documents: stock, fund_house, fund, fund_position_change
"""

import copy
import pymongo

import db
from setting import REPORT_DATE


ALL_STOCKS_DICT = {st["_id"]: st for st in list(db.Stock.find(projection=["name", "profile"]))}


# 按基金公司统计的一项
COMPANY_ENTRY = {
    "summary": {
        "fund_size": 0.0,  # 持仓基金总规模
        "quantity": 0.0,  # 总持股数
        "quantity_change": 0.0,  # 总持股变化
        "net_percent": 0.0,  # 总净值
        "net_percent_change": 0.0,  # 总净值变化
    },
    "latest": [],  # 当前持仓
    "enter": [],  # 新进
    "exit": [],  # 退出
    "inc_dec": [],  # 加减仓
}


def _aggregate_fund_position(stock_dict, house):
    funds_of_house = list(
        db.Fund.find(
            {"house_id": house["_id"], "position_history.0.date": REPORT_DATE},
        )
    )
    for fund in funds_of_house:
        for p in fund["position_history"][0]["position"]:
            house_entry = stock_dict.setdefault(p["code"], copy.deepcopy(COMPANY_ENTRY))
            house_entry["summary"]["fund_size"] += fund["size"]
            house_entry["summary"]["quantity"] += p["quantity"]
            house_entry["summary"]["net_percent"] += p["net_percent"]
            house_entry["latest"].append(
                {
                    "fund_code": fund["code"],
                    "fund_name": fund["name"],
                    "fund_size": fund["size"],
                    "net_percent": p["net_percent"],
                    "quantity": p["quantity"],
                }
            )

    # 保留小数点后两位
    for house_entry in stock_dict.values():
        house_entry["summary"]["fund_size"] = round(house_entry["summary"]["fund_size"], 2)
        house_entry["summary"]["quantity"] = round(house_entry["summary"]["quantity"], 2)
        house_entry["summary"]["net_percent"] = round(house_entry["summary"]["net_percent"], 2)


def _aggregate_fund_position_change(stock_dict, house):
    fund_position_changes_of_house = list(
        db.FundPositionChange.find(
            {"house_id": house["_id"], "date": REPORT_DATE},
        )
    )
    for position_change in fund_position_changes_of_house:
        for enter in position_change["enter"]:
            house_entry = stock_dict.setdefault(enter["code"], copy.deepcopy(COMPANY_ENTRY))
            house_entry["enter"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": enter["net_percent"],
                    "quantity": enter["quantity"],
                }
            )
            house_entry["summary"]["quantity_change"] += enter["quantity"]
            house_entry["summary"]["net_percent_change"] += enter["net_percent"]
        for exit_ in position_change["exit"]:
            house_entry = stock_dict.setdefault(exit_["code"], copy.deepcopy(COMPANY_ENTRY))
            house_entry["exit"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": exit_["net_percent"],
                    "quantity": exit_["quantity"],
                }
            )
            house_entry["summary"]["quantity_change"] -= exit_["quantity"]
            house_entry["summary"]["net_percent_change"] -= exit_["net_percent"]
        for inc_dec in position_change["inc_dec"]:
            house_entry = stock_dict.setdefault(inc_dec["code"], copy.deepcopy(COMPANY_ENTRY))
            house_entry["inc_dec"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": inc_dec["net_percent"],
                    "quantity": inc_dec["quantity"],
                }
            )
            house_entry["summary"]["quantity_change"] += inc_dec["quantity"]
            house_entry["summary"]["net_percent_change"] += inc_dec["net_percent"]

    # 保留小数点后两位
    for stock_code, house_entry in stock_dict.items():
        quantity_change = round(house_entry["summary"]["quantity_change"], 2)
        house_entry["summary"]["quantity_change"] = quantity_change
        house_entry["summary"]["net_percent_change"] = round(house_entry["summary"]["net_percent_change"], 2)
        # 得出 float_percent_change
        if stock_code in ALL_STOCKS_DICT:
            house_entry["summary"]["float_percent_change"] = round(
                quantity_change * 10000 * 100 / ALL_STOCKS_DICT[stock_code]["profile"]["float_shares"],
                3,
            )


def process_by_each_house(house):
    stock_dict = {}
    write_op_list = []

    _aggregate_fund_position(stock_dict, house)
    _aggregate_fund_position_change(stock_dict, house)

    for code, house_entry in stock_dict.items():
        if code not in ALL_STOCKS_DICT:
            continue

        house_entry["name"] = house["name"]
        if house.get("logo"):
            house_entry["logo"] = house["logo"]

        house_entry["latest"].sort(key=lambda x: x["quantity"], reverse=True)
        house_entry["enter"].sort(key=lambda x: x["quantity"], reverse=True)
        house_entry["exit"].sort(key=lambda x: x["quantity"], reverse=True)
        house_entry["inc_dec"].sort(key=lambda x: x["quantity"], reverse=True)

        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": code},
                {
                    "$set": {
                        "name": ALL_STOCKS_DICT[code]["name"],
                        "by_house.{}".format(house["_id"]): house_entry,
                        "date": REPORT_DATE,
                    }
                },
                upsert=True,
            )
        )

    if write_op_list:
        db.StockFundPosition.bulk_write(write_op_list)


if __name__ == "__main__":
    houses = list(db.FundHouse.find())
    for house in houses:
        process_by_each_house(house)
