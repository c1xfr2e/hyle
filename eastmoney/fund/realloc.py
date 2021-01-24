#!/usr/bin/env python3
# coding: utf-8

"""
    计算基金调仓情况
"""

import pymongo


REPORT_DATE = "2020-12-31"


def diff_holdings(new_holding, old_holding):
    old = {i["code"]: i for i in old_holding}
    new = {i["code"]: i for i in new_holding}
    new_codes = set(new) - set(old)
    deleted_codes = set(old) - set(new)
    updated_codes = set(old) & set(new)

    alloc_new = []
    for c in new_codes:
        h = new[c]
        alloc_new.append(
            {
                "name": h["name"],
                "code": h["code"],
                "volume": h["share"],
                "net_ratio": h["percent"],
            }
        )

    alloc_delete = []
    for c in deleted_codes:
        h = old[c]
        alloc_delete.append(
            {
                "name": h["name"],
                "code": h["code"],
                "volume": h["share"] * -1,
                "net_ratio": -h["percent"],
            }
        )

    alloc_update = []
    for c in updated_codes:
        ho, hn = old[c], new[c]
        vol_change = hn["share"] * 10000 - ho["share"] * 10000
        alloc_update.append(
            {
                "name": ho["name"],
                "code": ho["code"],
                "volume": round(vol_change / 10000, 2),
                "net_ratio": hn["percent"],
            }
        )

    alloc_new.sort(key=lambda x: x["net_ratio"], reverse=True)
    alloc_update.sort(key=lambda x: x["net_ratio"], reverse=True)
    alloc_delete.sort(key=lambda x: x["net_ratio"], reverse=True)

    return {"new": alloc_new, "update": alloc_update, "delete": alloc_delete}


def store_reallocs(mongo_col, reallocs):
    ops = [
        pymongo.UpdateOne(
            {"fund_id": r["fund_id"], "date": r["date"]},
            {"$set": r},
            upsert=True,
        )
        for r in reallocs
    ]
    mongo_col.bulk_write(ops)


if __name__ == "__main__":
    from eastmoney import db

    funds = db.Fund.find(
        filter={
            "$where": "this.holdings.length>1",
            "holdings.0.date": REPORT_DATE,
        }
    )

    reallocs = []
    for f in funds:
        holdings = f["holdings"]
        r = diff_holdings(holdings[0]["holdings"], holdings[1]["holdings"])
        r.update(
            date=REPORT_DATE,
            co_id=f["co_id"],
            co_name=f["co_name"],
            fund_id=f["code"],
            fund_name=f["name"],
        )
        reallocs.append(r)

    store_reallocs(db.Realloc, reallocs)
