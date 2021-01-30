#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo

from eastmoney.fund import db


REPORT_DATE = "2020-12-31"


def _group_position_change(group, item):
    g = group.get(item["code"])
    if not g:
        group[item["code"]] = item
        return
    g["volume"] += item["volume"]
    g["net_ratio"] += item["net_ratio"]


def _group_co_position_changes(position_changes):
    co_new = {}
    co_delete = {}
    for r in position_changes:
        for n in r.get("new", []):
            _group_position_change(co_new, n)
        for d in r.get("delete", []):
            _group_position_change(co_delete, d)
    return {
        "new": co_new,
        "delete": co_delete,
    }


def _sort_position_change_to_list(co_position_change):
    new_list = [i for i in co_position_change["new"].values()]
    new_list.sort(key=lambda x: x["net_ratio"], reverse=True)
    co_position_change["new"] = new_list
    delete_list = [i for i in co_position_change["delete"].values()]
    delete_list.sort(key=lambda x: x["net_ratio"])
    co_position_change["delete"] = delete_list


def obtain_company_position_change(report_date):
    co_position_change_list = []
    companies = db.FundCompany.find({})
    for co in companies:
        position_changes = db.PositionUpdate.find(
            filter={
                "co_id": co["_id"],
                "date": report_date,
            }
        )
        if not position_changes:
            continue

        co_position_change = _group_co_position_changes(position_changes)
        _sort_position_change_to_list(co_position_change)

        co_position_change["co_id"] = co["_id"]
        co_position_change["co_name"] = co["name"]
        co_position_change["date"] = report_date

        co_position_change_list.append(co_position_change)

    return co_position_change_list


if __name__ == "__main__":
    co_position_change_list = obtain_company_position_change(REPORT_DATE)
    ops = [
        pymongo.UpdateOne(
            {"co_id": r["co_id"], "date": r["date"]},
            {"$set": r},
            upsert=True,
        )
        for r in co_position_change_list
    ]
    db.CompanyPositionUpdate.bulk_write(ops)
