#!/usr/bin/env python3
# coding: utf-8

import pymongo

import db
from setting import REPORT_DATE


ALL_STOCKS_DICT = {st["_id"]: st for st in list(db.Stock.find(projection=["name", "profile"]))}


def _aggregate_fund_position(stock_entry_dict, fund):
    for p in fund["position_history"][0]["position"]:
        stock_entry = stock_entry_dict.setdefault(p["code"], {})
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


def _aggregate_fund_position_change(stock_entry_dict, fund_change):
    for e in fund_change["enter"]:
        stock_entry = stock_entry_dict.setdefault(e["code"], {})
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
        stock_entry = stock_entry_dict.setdefault(e["code"], {})
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
        stock_entry = stock_entry_dict.setdefault(i["code"], {})
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


def _aggregate_all_stock_fund_position(stock_entry_dict):
    fund_list = list(db.Fund.find({"position_history.0.date": REPORT_DATE}))
    for fund in fund_list:
        _aggregate_fund_position(stock_entry_dict, fund)


def _aggregate_all_stock_fund_position_change(stock_entry_dict):
    change_list = list(db.FundPositionChange.find({"date": REPORT_DATE}))
    for change in change_list:
        _aggregate_fund_position_change(stock_entry_dict, change)


def process_by_each_fund():
    stock_entry_dict = {}

    _aggregate_all_stock_fund_position(stock_entry_dict)
    _aggregate_all_stock_fund_position_change(stock_entry_dict)

    write_op_list = []
    for code, stock in ALL_STOCKS_DICT.items():
        if code not in stock_entry_dict:
            continue

        stock_entry = stock_entry_dict[code]
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


ENTRY = {
    "summary": {
        "fund_size": 0.0,
        "quantity": 0.0,
        "quantity_change": 0.0,
        "net_percent": 0.0,
        "percent_change": 0.0,
    },
    "latest": [],
    "enter": [],
    "exit": [],
    "inc_dec": [],
}

import copy


def _aggregate_fund_position_of_company_by_stock(stock_entry_dict, company):
    funds_list_of_company = list(
        db.Fund.find(
            {"co_id": company["_id"], "position_history.0.date": REPORT_DATE},
        )
    )
    for fund in funds_list_of_company:
        for p in fund["position_history"][0]["position"]:
            entry = stock_entry_dict.setdefault(p["code"], copy.deepcopy(ENTRY))
            entry["summary"]["fund_size"] += fund["size"]
            entry["summary"]["quantity"] += p["quantity"]
            entry["summary"]["net_percent"] += p["net_percent"]
            entry["latest"].append(
                {
                    "fund_code": fund["code"],
                    "fund_name": fund["name"],
                    "fund_size": fund["size"],
                    "net_percent": p["net_percent"],
                    "quantity": p["quantity"],
                }
            )

    for entry in stock_entry_dict.values():
        entry["summary"]["fund_size"] = round(entry["summary"]["fund_size"], 2)
        entry["summary"]["quantity"] = round(entry["summary"]["quantity"], 2)
        entry["summary"]["net_percent"] = round(entry["summary"]["net_percent"], 2)


def _aggregate_fund_position_postion_of_company_by_stock(stock_entry_dict, company):
    fund_position_change_list_of_company = list(
        db.FundPositionChange.find(
            {"co_id": company["_id"], "date": REPORT_DATE},
        )
    )
    for position_change in fund_position_change_list_of_company:
        for c in position_change["enter"]:
            entry = stock_entry_dict.setdefault(c["code"], copy.deepcopy(ENTRY))
            entry["enter"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": c["net_percent"],
                    "quantity": c["quantity"],
                }
            )
            entry["summary"]["quantity_change"] += c["quantity"]
            entry["summary"]["percent_change"] += c["net_percent"]
        for c in position_change["exit"]:
            entry = stock_entry_dict.setdefault(c["code"], copy.deepcopy(ENTRY))
            entry["exit"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": c["net_percent"],
                    "quantity": c["quantity"],
                }
            )
            entry["summary"]["quantity_change"] -= c["quantity"]
            entry["summary"]["percent_change"] -= c["net_percent"]
        for c in position_change["inc_dec"]:
            entry = stock_entry_dict.setdefault(c["code"], copy.deepcopy(ENTRY))
            entry["inc_dec"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "fund_size": position_change["size"],
                    "net_percent": c["net_percent"],
                    "quantity": c["quantity"],
                }
            )
            entry["summary"]["quantity_change"] += c["quantity"]
            entry["summary"]["percent_change"] += c["net_percent"]

    for stock_code, entry in stock_entry_dict.items():
        quantity_change = round(entry["summary"]["quantity_change"], 2)
        entry["summary"]["quantity_change"] = quantity_change
        if stock_code in ALL_STOCKS_DICT:
            entry["summary"]["volume_in_float_change"] = round(
                quantity_change * 10000 * 100 / ALL_STOCKS_DICT[stock_code]["profile"]["float_shares"],
                3,
            )
        entry["summary"]["percent_change"] = round(entry["summary"]["percent_change"], 2)


def process_by_each_company(company):
    stock_entry_dict = {}
    write_op_list = []

    _aggregate_fund_position_of_company_by_stock(stock_entry_dict, company)
    _aggregate_fund_position_postion_of_company_by_stock(stock_entry_dict, company)

    for code, entry in stock_entry_dict.items():
        if code not in ALL_STOCKS_DICT:
            continue

        entry["name"] = company["name"]
        if company.get("logo"):
            entry["logo"] = company["logo"]

        entry["latest"].sort(key=lambda x: x["quantity"], reverse=True)
        entry["enter"].sort(key=lambda x: x["quantity"], reverse=True)
        entry["exit"].sort(key=lambda x: x["quantity"], reverse=True)
        entry["inc_dec"].sort(key=lambda x: x["quantity"], reverse=True)

        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": code},
                {
                    "$set": {
                        "name": ALL_STOCKS_DICT[code]["name"],
                        "by_company.{}".format(company["_id"]): entry,
                    }
                },
                upsert=True,
            )
        )

    db.StockFundPosition.bulk_write(write_op_list)


if __name__ == "__main__":
    company_list = list(db.FundCompany.find())
    for co in company_list:
        process_by_each_company(co)