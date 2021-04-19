#!/usr/bin/env python3
# coding: utf-8

"""
    统计基金公司整体持仓

    Preconditions:
        - mongodb documents: fund_company, fund
        - fund 中已有 position_history 数据
"""

import pymongo

import db


def _add_position(cur, p, fund):
    return {
        "name": p["name"],
        "code": p["code"],
        "quantity": cur.get("quantity", 0) + p["quantity"],
        "value": cur.get("value", 0) + p["value"],
        "float_percent": cur.get("float_percent", 0) + p.get("float_percent", 0),
        "net_percent": cur.get("net_percent", 0) + p["net_percent"],
        "funds": cur.get("funds", []) + [{"name": fund["name"], "code": fund["code"]}],
    }


def aggregate_fund_position_history(fund_list):
    """
    把多家基金的持仓历史累加，形成统一的 position

    Args:
        fund_list: 基金列表

    Returns:
        position_history dict, key 为 date, value 为 position dict:
            {
                "2020-12-31": {
                    "600001": {"name": ..., "code": ...}
                }
            }
    """
    position_history_dict = {}
    for fund in fund_list:
        for ph in fund["position_history"]:
            position_dict = position_history_dict.setdefault(ph["date"], {})
            for p in ph["position"]:
                position_dict[p["code"]] = _add_position(
                    position_dict.setdefault(p["code"], {}),
                    p,
                    fund,
                )
    return position_history_dict


def _position_dict_to_list(position_dict):
    lst = list(position_dict.values())
    lst.sort(
        key=lambda x: x["float_percent"] * 100000 + x["net_percent"],
        reverse=True,
    )
    return lst


def _round_floats(position):
    for p in position:
        p["quantity"] = round(p["quantity"], 2)
        p["value"] = round(p["value"], 2)
        p["float_percent"] = round(p["float_percent"], 3)
        p["net_percent"] = round(p["net_percent"], 2)
    return position


def _write_op(company, position_history_list):
    return pymongo.UpdateOne(
        {
            "_id": company["_id"],
        },
        {
            "$set": {
                "co_name": company["name"],
                "co_size": company["size"],
                "position_history": position_history_list,
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
        fund_list = list(db.Fund.find(_fund_filter()))
        position_history_dict = aggregate_fund_position_history(fund_list)
        # 转成 list 保存
        position_history_list = [
            {
                "date": date,
                "position": _round_floats(_position_dict_to_list(position_history_dict[date])),
            }
            for date in sorted(position_history_dict.keys(), reverse=True)
        ]
        write_op_list.append(_write_op(co, position_history_list))
    db.FundCompanyPosition.bulk_write(write_op_list)
