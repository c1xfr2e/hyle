import db


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
    # ["测试系统", "测试系统配件", "工业测试", "工业检测", "大功率测试电源", "小功率测试电源", "测试电源", "调测系统", "测试电源"]
    # ["光学膜", "光学薄膜", "光学基膜", "反射膜", "特种功能膜"]
    product = ["超硬材料", "超硬复合材料"]
    industry = ["超硬材料", "超硬复合材料"]

    stocks = match_keywords(product, industry)

    print([st["name"] for st in stocks])
