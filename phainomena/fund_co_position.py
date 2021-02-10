#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo
from phainomena import db


SAMPLE = {
    "date": "2020-09-30",
    "position": [
        {
            "name": "金螳螂",
            "code": "002081",
            "volume": 10000,
            "value": 1000025,
            "volume_in_float": 0.25,
            "total_percent": 6.6,
            "funds": [
                {
                    "name": "广发中证工程基建指数",
                    "code": "002001",
                },
                {
                    "name": "天弘文化新兴产业",
                    "code": "001002",
                },
            ],
        }
    ],
}


def _add_position(cur, p, fund):
    return {
        "name": p["name"],
        "code": p["code"],
        "volume": cur.get("volume", 0) + p["volume"],
        "value": cur.get("value", 0) + p["value"],
        "volume_in_float": cur.get("volume_in_float", 0) + p.get("volume_in_float", 0),
        "total_percent": cur.get("total_percent", 0) + p["percent"],
        "funds": cur.get("funds", []) + [{"name": fund["name"], "code": fund["code"]}],
    }


def group_funds_position(funds_of_company):
    position_by_date_dict = {}
    for fund in funds_of_company:
        for pos_date in fund["position_by_date"]:
            stock_position_dict = position_by_date_dict.setdefault(pos_date["date"], {})
            for pos in pos_date["position"]:
                stock_position_dict[pos["code"]] = _add_position(
                    stock_position_dict.setdefault(pos["code"], {}),
                    pos,
                    fund,
                )
    return position_by_date_dict


def _position_by_date_dict_to_list(position_by_date_dict):
    list_ = list(position_by_date_dict.values())
    list_.sort(key=lambda x: x["volume_in_float"] * 100000 + x["total_percent"], reverse=True)
    return list_


def _write_op(company, position_by_date_dict):
    stock_position_list_by_date = [
        {
            "date": date,
            "position": _position_by_date_dict_to_list(position_by_date_dict[date]),
        }
        for date in sorted(position_by_date_dict.keys(), reverse=True)
    ]
    return pymongo.UpdateOne(
        {
            "_id": company["_id"],
        },
        {
            "$set": {
                "co_name": company["name"],
                "co_size": company["size"],
                "position_by_date": stock_position_list_by_date,
            }
        },
        upsert=True,
    )


if __name__ == "__main__":
    write_op_list = []
    company_list = list(db.FundCompany.find())
    for co in company_list:
        funds_of_company = list(db.Fund.find({"co_id": co["_id"]}))
        position_by_date_dict = group_funds_position(funds_of_company)
        write_op_list.append(_write_op(co, position_by_date_dict))

    db.FundCompanyPosition.bulk_write(write_op_list)
