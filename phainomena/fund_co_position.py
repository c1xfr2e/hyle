#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo

import db


def _add_position(cur, p, fund):
    return {
        "name": p["name"],
        "code": p["code"],
        "quantity": cur.get("quantity", 0) + p["quantity"],
        "value": cur.get("value", 0) + p["value"],
        "float_percent": cur.get("float_percent", 0) + p["float_percent"],
        "percent": cur.get("percent", 0) + p["percent"],
        "funds": cur.get("funds", []) + [{"name": fund["name"], "code": fund["code"]}],
    }


def _aggregate_funds_of_company(fund_list):
    position_history_dict = {}
    for fund in fund_list:
        for pos_date in fund["position_history"]:
            stock_position_dict = position_history_dict.setdefault(pos_date["date"], {})
            for pos in pos_date["position"]:
                stock_position_dict[pos["code"]] = _add_position(
                    stock_position_dict.setdefault(pos["code"], {}),
                    pos,
                    fund,
                )
    return position_history_dict


def _position_history_dict_to_list(position_history_dict):
    list_ = list(position_history_dict.values())
    list_.sort(
        key=lambda x: x["float_percent"] * 100000 + x["percent"],
        reverse=True,
    )
    return list_


def _round_floats(position_list):
    for p in position_list:
        p["quantity"] = round(p["quantity"], 2)
        p["value"] = round(p["value"], 2)
        p["float_percent"] = round(p["float_percent"], 3)
        p["percent"] = round(p["percent"], 2)
    return position_list


def _write_op(company, position_history_dict):
    stock_position_history = [
        {
            "date": date,
            "position": _round_floats(
                _position_history_dict_to_list(position_history_dict[date]),
            ),
        }
        for date in sorted(position_history_dict.keys(), reverse=True)
    ]
    return pymongo.UpdateOne(
        {
            "_id": company["_id"],
        },
        {
            "$set": {
                "co_name": company["name"],
                "co_size": company["size"],
                "position_history": stock_position_history,
            }
        },
        upsert=True,
    )


def _fund_filter():
    return {
        "co_id": co["_id"],
        "position_history.0": {"$exists": 1},
    }


if __name__ == "__main__":
    write_op_list = []
    for co in list(db.FundCompany.find()):
        funds_of_company = list(db.Fund.find(_fund_filter()))
        position_history_dict = _aggregate_funds_of_company(funds_of_company)
        write_op_list.append(_write_op(co, position_history_dict))
    db.FundCompanyPosition.bulk_write(write_op_list)
