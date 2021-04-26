#!/usr/bin/env python3
# coding: utf-8

import pymongo


def _filter(t):
    if t["name"] in ["新三板", "QFII重仓", "机构重仓"]:
        return False
    return True


if __name__ == "__main__":
    stock_col = pymongo.MongoClient("mongodb://localhost:27017")["hyle"]["stock"]
    op_list = []
    for st in list(stock_col.find(projection=["topic"])):
        topic = list(filter(_filter, st["topic"]))
        op_list.append(
            pymongo.UpdateOne(
                {"_id": st["_id"]},
                {
                    "$set": {"topic": topic},
                },
            )
        )

    stock_col.bulk_write(op_list)
