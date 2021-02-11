import pymongo
from phainomena import db


REPORT_DATE = "2020-12-31"


def stock_fund_position(stock_code):
    # db.stock.find({"business": {$elemMatch: {"by_product": {$elemMatch: {"name": {$in: ["光学膜", "光学薄膜", "光学基膜", "反射膜"]}}}}}}, {"name": 1})
    fund_co_pos = db.FundCompanyPosition.find(
        {
            "position_by_date": {
                "$elemMatch": {
                    "$and": [
                        {
                            "date": "2020-12-31",
                        },
                        {
                            "position": {
                                "$elemMatch": {
                                    "code": stock_code,
                                },
                            },
                        },
                    ],
                },
            },
        },
        projection=["co_name"],
    )

    return list(fund_co_pos)


if __name__ == "__main__":
    fund_co_pos = stock_fund_position("601003")
    print([co["co_name"] for co in fund_co_pos])
