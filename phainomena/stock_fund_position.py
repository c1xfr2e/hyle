#!/usr/bin/env python3
# coding: utf-8

import pymongo

from phainomena import db


REPORT_DATE = "2020-12-31"


def _aggregate_fund_position(stock_entry_dict, fund):
    for p in fund["position_by_date"][0]["position"]:
        stock_entry = stock_entry_dict.setdefault(p["code"], {})
        company_entry = stock_entry.setdefault(fund["co_id"], {"name": fund["co_name"]})
        latest = company_entry.setdefault("latest", [])
        latest.append(
            {
                "fund_code": fund["code"],
                "fund_name": fund["name"],
                "fund_size": fund["size"],
                "percent": p["percent"],
                "volume": p["volume"],
                "volume_in_float": p["volume_in_float"],
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
                "percent": e["percent"],
                "volume": e["volume"],
                "volume_in_float": e["volume_in_float"],
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
                "percent": e["percent"],
                "volume": e["volume"],
                "volume_in_float": e["volume_in_float"],
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
                "percent": i["percent"],
                "volume": i["volume"],
                "volume_in_float": i["volume_in_float"],
            }
        )


def aggregate_all_stock_fund_position(stock_entry_dict):
    fund_list = list(db.Fund.find({"position_by_date.0.date": REPORT_DATE}))
    for fund in fund_list:
        _aggregate_fund_position(stock_entry_dict, fund)


def aggregate_all_stock_fund_position_change(stock_entry_dict):
    change_list = list(db.FundPositionChange.find({"date": REPORT_DATE}))
    for change in change_list:
        _aggregate_fund_position_change(stock_entry_dict, change)


def process_by_each_fund():
    stocks = {st["_id"]: st for st in list(db.Stock.find(projection=["name"]))}

    stock_entry_dict = {}

    aggregate_all_stock_fund_position(stock_entry_dict)
    aggregate_all_stock_fund_position_change(stock_entry_dict)

    write_op_list = []
    for code, stock in stocks.items():
        if code not in stock_entry_dict:
            continue

        stock_entry = stock_entry_dict[code]
        for co_entry in stock_entry.values():
            co_entry.get("latest", []).sort(key=lambda x: x["volume"], reverse=True)
            co_entry.get("enter", []).sort(key=lambda x: x["volume"], reverse=True)
            co_entry.get("exit", []).sort(key=lambda x: x["volume"], reverse=True)
            co_entry.get("inc_dec", []).sort(key=lambda x: x["volume"], reverse=True)

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
        "volume": 0.0,
        "volume_in_float": 0.0,
    },
    "latest": [],
    "enter": [],
    "exit": [],
    "inc_dec": [],
}

import copy


def aggregate_fund_position_of_company_by_stock(stock_entry_dict, company):
    funds_list_of_company = list(
        db.Fund.find(
            {"co_id": company["_id"], "position_by_date.0.date": REPORT_DATE},
        )
    )
    for fund in funds_list_of_company:
        for p in fund["position_by_date"][0]["position"]:
            entry = stock_entry_dict.setdefault(p["code"], copy.deepcopy(ENTRY))
            entry["summary"]["fund_size"] += fund["size"]
            entry["summary"]["volume"] += p["volume"]
            entry["summary"]["volume_in_float"] += p["volume_in_float"]
            entry["latest"].append(
                {
                    "fund_code": fund["code"],
                    "fund_name": fund["name"],
                    "fund_size": fund["size"],
                    "percent": p["percent"],
                    "volume": p["volume"],
                    "volume_in_float": p["volume_in_float"],
                }
            )
    for entry in stock_entry_dict.values():
        entry["summary"]["fund_size"] = round(entry["summary"]["fund_size"], 2)
        entry["summary"]["volume"] = round(entry["summary"]["volume"], 2)
        entry["summary"]["volume_in_float"] = round(entry["summary"]["volume_in_float"], 3)


def aggregate_fund_position_postion_of_company_by_stock(stock_entry_dict, company):
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
                    "percent": c["percent"],
                    "volume": c["volume"],
                    "volume_in_float": c["volume_in_float"],
                }
            )
        for c in position_change["exit"]:
            entry = stock_entry_dict.setdefault(c["code"], copy.deepcopy(ENTRY))
            entry["exit"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "percent": c["percent"],
                    "volume": c["volume"],
                    "volume_in_float": c["volume_in_float"],
                }
            )
        for c in position_change["inc_dec"]:
            entry = stock_entry_dict.setdefault(c["code"], copy.deepcopy(ENTRY))
            entry["inc_dec"].append(
                {
                    "fund_code": position_change["_id"],
                    "fund_name": position_change["name"],
                    "percent": c["percent"],
                    "volume": c["volume"],
                    "volume_in_float": c["volume_in_float"],
                }
            )


ALL_STOCKS_DICT = {st["_id"]: st for st in list(db.Stock.find(projection=["name"]))}


def process_by_each_company(company):
    stock_entry_dict = {}
    write_op_list = []

    aggregate_fund_position_of_company_by_stock(stock_entry_dict, company)
    aggregate_fund_position_postion_of_company_by_stock(stock_entry_dict, company)

    for code, entry in stock_entry_dict.items():
        if code not in ALL_STOCKS_DICT:
            continue

        entry["name"] = company["name"]

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
