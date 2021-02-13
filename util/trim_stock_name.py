import pymongo

URI = "mongodb://localhost:27017"
cli = pymongo.MongoClient(URI)["hyle"]
Stock = cli["stock"]

write_op_list = []

for st in list(Stock.find(projection=["name"])):
    write_op_list.append(
        pymongo.UpdateOne(
            {"_id": st["_id"]},
            {
                "$set": {"name": st["name"].replace(" ", "")},
            },
        )
    )

Stock.bulk_write(write_op_list)
