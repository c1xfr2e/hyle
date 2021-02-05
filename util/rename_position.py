#!/usr/bin/env python3
# coding: utf-8

import pymongo


if __name__ == "__main__":
    URI = "mongodb://localhost:27017"
    cli = pymongo.MongoClient(URI)["hyle"]
    Fund = cli["fund"]
    update_op_list = []
    for f in list(Fund.find(projection=["position"])):
        position = f["position"]
        for p in position:
            p["stock"] = p["position"]
            del p["position"]
        update_op_list.append(
            pymongo.UpdateOne(
                {"_id": f["_id"]},
                {
                    "$set": {"position": position},
                },
            )
        )

    Fund.bulk_write(update_op_list)
