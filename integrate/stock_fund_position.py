#!/usr/bin/env python3
# coding: utf-8

"""
    统计每个股票的基金仓位

    Preconditions:
        - mongodb documents: stock, fund_company, fund, fund_position_change
"""

import copy
import pymongo

import db
from setting import REPORT_DATE


ALL_STOCKS_DICT = {st["_id"]: st for st in list(db.Stock.find(projection=["name", "profile"]))}

"""
def _aggregate_fund_position(stock_dict, fund):
    for p in fund["position_history"][0]["position"]:
        stock_entry = stock_dict.setdefault(p["code"], {})
        company_entry = stock_entry.setdefault(fund["co_id"], {"name": fund["co_name"]})
        latest = company_entry.setdefault("latest", [])
        latest.append(
            {
                "fund_code": fund["code"],
                "fund_name": fund["name"],
                "fund_size": fund["size"],
                "net_percent": p["net_percent"],
                "quantity": p["quantity"],
            }
        )


def _aggregate_fund_position_change(stock_dict, fund_change):
    for e in fund_change["enter"]:
        stock_entry = stock_dict.setdefault(e["code"], {})
        company_entry = stock_entry.setdefault(fund_change["co_id"], {"name": fund_change["co_name"]})
        enter_list = company_entry.setdefault("enter", [])
        enter_list.append(
            {
                "fund_code": fund_change["_id"],
                "fund_name": fund_change["name"],
                "fund_size": fund_change["size"],
                "net_percent": e["net_percent"],
                "quantity": e["quantity"],
            }
        )
    for e in fund_change["exit"]:
        stock_entry = stock_dict.setdefault(e["code"], {})
        company_entry = stock_entry.setdefault(fund_change["co_id"], {"name": fund_change["co_name"]})
        exit_list = company_entry.setdefault("exit", [])
        exit_list.append(
            {
                "fund_code": fund_change["_id"],
                "fund_name": fund_change["name"],
                "fund_size": fund_change["size"],
                "net_percent": e["net_percent"],
                "quantity": e["quantity"],
            }
        )
        pass
    for i in fund_change["inc_dec"]:
        stock_entry = stock_dict.setdefault(i["code"], {})
        company_entry = stock_entry.setdefault(fund_change["co_id"], {"name": fund_change["co_name"]})
        inc_dec_list = company_entry.setdefault("inc_dec", [])
        inc_dec_list.append(
            {
                "fund_code": fund_change["_id"],
                "fund_name": fund_change["name"],
                "fund_size": fund_change["size"],
                "net_percent": i["net_percent"],
                "quantity": i["quantity"],
            }
        )


def _aggregate_all_stock_fund_position(stock_dict):
    fund_list = list(db.Fund.find({"position_history.0.date": REPORT_DATE}))
    for fund in fund_list:
        _aggregate_fund_position(stock_dict, fund)


def _aggregate_all_stock_fund_position_change(stock_dict):
    change_list = list(db.FundPositionChange.find({"date": REPORT_DATE}))
    for change in change_list:
        _aggregate_fund_position_change(stock_dict, change)


def process_by_each_fund():
    stock_dict = {}

    _aggregate_all_stock_fund_position(stock_dict)
    _aggregate_all_stock_fund_position_change(stock_dict)

    write_op_list = []
    for code, stock in ALL_STOCKS_DICT.items():
        if code not in stock_dict:
            continue

        stock_entry = stock_dict[code]
        for co_entry in stock_entry.values():
            co_entry.get("latest", []).sort(key=lambda x: x["quantity"], reverse=True)
            co_entry.get("enter", []).sort(key=lambda x: x["quantity"], reverse=True)
            co_entry.get("exit", []).sort(key=lambda x: x["quantity"], reverse=True)
            co_entry.get("inc_dec", []).sort(key=lambda x: x["quantity"], reverse=True)

        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": code},
                {
                    "$set": {
                        "name": stock["name"],
                        "by_company": stock_entry,
                    }
                },
                upsert=True,
            )
        )

    db.StockFundPosition.bulk_write(write_op_list)
"""

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


def _aggregate_fund_position(stock_dict, company):
    funds_of_company = list(
        db.Fund.find(
            {"co_id": company["_id"], "position_history.0.date": REPORT_DATE},
        )
    )
    for fund in funds_of_company:
        for p in fund["position_history"][0]["position"]:
            co_entry = stock_dict.setdefault(p["code"], copy.deepcopy(COMPANY_ENTRY))
            co_entry["summary"]["fund_size"] += fund["size"]
            co_entry["summary"]["quantity"] += p["quantity"]
            co_entry["summary"]["net_percent"] += p["net_percent"]
            co_entry["latest"].append(
                {
                    "fund_code": fund["code"],
                    "fund_name": fund["name"],
                    "fund_size": fund["size"],
                    "net_percent": p["net_percent"],
                    "quantity": p["quantity"],
                }
            )

    # 保留小数点后两位
    for co_entry in stock_dict.values():
        co_entry["summary"]["fund_size"] = round(co_entry["summary"]["fund_size"], 2)
        co_entry["summary"]["quantity"] = round(co_entry["summary"]["quantity"], 2)
        co_entry["summary"]["net_percent"] = round(co_entry["summary"]["net_percent"], 2)


def _aggregate_fund_position_change(stock_dict, company):
    fund_position_changes_of_company = list(
        db.FundPositionChange.find(
            {"co_id": company["_id"], "date": REPORT_DATE},
        )
    )
    for position_change in fund_position_changes_of_company:
        for enter in position_change["enter"]:
            co_entry = stock_dict.setdefault(enter["code"], copy.deepcopy(COMPANY_ENTRY))
            co_entry["enter"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": enter["net_percent"],
                    "quantity": enter["quantity"],
                }
            )
            co_entry["summary"]["quantity_change"] += enter["quantity"]
            co_entry["summary"]["net_percent_change"] += enter["net_percent"]
        for exit_ in position_change["exit"]:
            co_entry = stock_dict.setdefault(exit_["code"], copy.deepcopy(COMPANY_ENTRY))
            co_entry["exit"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": exit_["net_percent"],
                    "quantity": exit_["quantity"],
                }
            )
            co_entry["summary"]["quantity_change"] -= exit_["quantity"]
            co_entry["summary"]["net_percent_change"] -= exit_["net_percent"]
        for inc_dec in position_change["inc_dec"]:
            co_entry = stock_dict.setdefault(inc_dec["code"], copy.deepcopy(COMPANY_ENTRY))
            co_entry["inc_dec"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": inc_dec["net_percent"],
                    "quantity": inc_dec["quantity"],
                }
            )
            co_entry["summary"]["quantity_change"] += inc_dec["quantity"]
            co_entry["summary"]["net_percent_change"] += inc_dec["net_percent"]

    # 保留小数点后两位
    for stock_code, co_entry in stock_dict.items():
        quantity_change = round(co_entry["summary"]["quantity_change"], 2)
        co_entry["summary"]["quantity_change"] = quantity_change
        co_entry["summary"]["net_percent_change"] = round(co_entry["summary"]["net_percent_change"], 2)
        # 得出 float_percent_change
        if stock_code in ALL_STOCKS_DICT:
            co_entry["summary"]["float_percent_change"] = round(
                quantity_change * 10000 * 100 / ALL_STOCKS_DICT[stock_code]["profile"]["float_shares"],
                3,
            )


def process_by_each_company(company):
    stock_dict = {}
    write_op_list = []

    _aggregate_fund_position(stock_dict, company)
    _aggregate_fund_position_change(stock_dict, company)

    for code, co_entry in stock_dict.items():
        if code not in ALL_STOCKS_DICT:
            continue

        co_entry["name"] = company["name"]
        if company.get("logo"):
            co_entry["logo"] = company["logo"]

        co_entry["latest"].sort(key=lambda x: x["quantity"], reverse=True)
        co_entry["enter"].sort(key=lambda x: x["quantity"], reverse=True)
        co_entry["exit"].sort(key=lambda x: x["quantity"], reverse=True)
        co_entry["inc_dec"].sort(key=lambda x: x["quantity"], reverse=True)

        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": code},
                {
                    "$set": {
                        "name": ALL_STOCKS_DICT[code]["name"],
                        "by_company.{}".format(company["_id"]): co_entry,
                    }
                },
                upsert=True,
            )
        )

    db.StockFundPosition.bulk_write(write_op_list)


if __name__ == "__main__":
    companies = list(db.FundCompany.find())
    for co in companies:
        process_by_each_company(co)
