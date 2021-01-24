#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo

from eastmoney import db


REPORT_DATE = "2020-12-31"


def _group_realloc(group, item):
    g = group.get(item["code"])
    if not g:
        group[item["code"]] = item
        return
    g["volume"] += item["volume"]
    g["net_ratio"] += item["net_ratio"]


def _group_co_reallocs(reallocs):
    co_new = {}
    co_delete = {}
    for r in reallocs:
        for n in r.get("new", []):
            _group_realloc(co_new, n)
        for d in r.get("delete", []):
            _group_realloc(co_delete, d)
    return {
        "new": co_new,
        "delete": co_delete,
    }


def _sort_realloc_to_list(co_realloc):
    new_list = [i for i in co_realloc["new"].values()]
    new_list.sort(key=lambda x: x["net_ratio"], reverse=True)
    co_realloc["new"] = new_list
    delete_list = [i for i in co_realloc["delete"].values()]
    delete_list.sort(key=lambda x: x["net_ratio"])
    co_realloc["delete"] = delete_list


def obtain_company_realloc(report_date):
    co_realloc_list = []
    companies = db.FundCompany.find({})
    for co in companies:
        reallocs = db.Realloc.find(
            filter={
                "co_id": co["_id"],
                "date": report_date,
            }
        )
        if not reallocs:
            continue

        co_realloc = _group_co_reallocs(reallocs)
        _sort_realloc_to_list(co_realloc)

        co_realloc["co_id"] = co["_id"]
        co_realloc["co_name"] = co["name"]
        co_realloc["date"] = report_date

        co_realloc_list.append(co_realloc)

    return co_realloc_list


if __name__ == "__main__":
    co_realloc_list = obtain_company_realloc(REPORT_DATE)
    ops = [
        pymongo.UpdateOne(
            {"co_id": r["co_id"], "date": r["date"]},
            {"$set": r},
            upsert=True,
        )
        for r in co_realloc_list
    ]
    db.CompanyRealloc.bulk_write(ops)
