#!/usr/bin/env python3
# coding: utf-8

"""
    基金公司整体调仓情况
"""

import pymongo
from phainomena import db


SAMPLE = {
    "2020-09-30": {
        "000001": [
            {
                "fund": {
                    "code": "004606",
                    "manager": "胡迪",
                    "name": "上投摩根优选多因子股票",
                },
                "position": {
                    "code": "000001",
                    "name": "平安银行",
                    "percent": 3.77,
                    "value": 76.91,
                    "volume": 5.07,
                },
            },
            {
                "fund": {
                    "code": "004738",
                    "manager": "陈圆明",
                    "name": "上投摩根安隆回报A",
                },
                "position": {
                    "code": "000001",
                    "name": "平安银行",
                    "percent": 2.53,
                    "value": 4864.41,
                    "volume": 320.66,
                },
            },
        ],
        "000002": [
            {
                "fund": {
                    "code": "004361",
                    "manager": "聂曙光",
                    "name": "上投摩根安通回报混合A",
                },
                "position": {
                    "code": "000002",
                    "name": "万科A",
                    "percent": 0.73,
                    "value": 487.27,
                    "volume": 17.39,
                },
            },
            {
                "fund": {
                    "code": "000887",
                    "manager": "聂曙光",
                    "name": "上投摩根稳进回报混合",
                },
                "position": {
                    "code": "000002",
                    "name": "万科A",
                    "percent": 2.02,
                    "value": 32.64,
                    "volume": 1.16,
                },
            },
        ],
    }
}


def group_fund_position_of_company(fund_list):
    result_dict_by_date = {}
    for fund in fund_list:
        for position in fund["position"]:
            stock_position_map = result_dict_by_date.setdefault(position["date"], {})
            for stock in position["stock"]:
                stock_pos_list = stock_position_map.setdefault(stock["code"], [])
                stock_pos_list.append(
                    {
                        "fund": {
                            "code": fund["code"],
                            "name": fund["name"],
                            "manager": fund["manager"],
                        },
                        "position": stock,
                    }
                )
    return result_dict_by_date


def _get_write_op(company, result_dict_by_date):
    list_by_date = [
        {
            "date": date,
            "stock_position": result_dict_by_date[date],
        }
        for date in sorted(result_dict_by_date.keys(), reverse=True)
    ]
    return pymongo.UpdateOne(
        {
            "_id": company["_id"],
        },
        {
            "$set": {
                "co_name": company["name"],
                "co_size": company["size"],
                "list_by_date": list_by_date,
            }
        },
        upsert=True,
    )


if __name__ == "__main__":
    write_op_list = []
    company_list = list(db.FundCompany.find())
    for co in company_list:
        fund_list = list(db.Fund.find({"co_id": co["_id"]}))
        result = group_fund_position_of_company(fund_list)
        write_op_list.append(_get_write_op(co, result))

    db.FundCompanyPosition.bulk_write(write_op_list)
