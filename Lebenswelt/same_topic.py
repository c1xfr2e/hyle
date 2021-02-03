import pymongo
from eastmoney.stock import db


def match_keywords(product_list, industry_list):
    # db.stock.find({"business": {$elemMatch: {"by_product": {$elemMatch: {"name": {$in: ["光学膜", "光学薄膜", "光学基膜", "反射膜"]}}}}}}, {"name": 1})
    stocks = db.Stock.find(
        {
            "business": {
                "$elemMatch": {
                    "$or": [
                        {
                            "by_product": {
                                "$elemMatch": {
                                    "name": {
                                        "$in": product_list,
                                    },
                                },
                            }
                        },
                        {
                            "by_industry": {
                                "$elemMatch": {
                                    "name": {
                                        "$in": industry_list,
                                    },
                                },
                            },
                        },
                    ],
                },
            },
        },
        projection=["code", "name"],
    )

    return list(stocks)


if __name__ == "__main__":
    # ["光学膜", "光学薄膜", "光学基膜", "反射膜"]
    # product = ["压滤机整机", "压滤机"]
    # ["特种功能膜"]
    product = ["橱柜业务", "橱柜"]
    industry = [""]

    stocks = match_keywords(product, industry)

    print([st["name"] for st in stocks])
