"""
    Baostock 获取历史A股K线数据

    文档: http://baostock.com/baostock/index.php/Python_API%E6%96%87%E6%A1%A3
"""

import arrow
import baostock
import logging
import pymongo
from datetime import datetime

import db
from util.progress_bar import print_progress_bar


def get_kline_history(code, frequency, begin, end):
    rs = baostock.query_history_k_data_plus(
        "{market}.{stock}".format(market="sh" if code[0] == "6" else "sz", stock=code),
        "date,open,close,high,low,volume,amount,turn,pctChg,preclose,tradestatus",
        start_date=begin.strftime("%Y-%m-%d"),
        end_date=end.strftime("%Y-%m-%d"),
        frequency=frequency,
    )
    if rs.error_code != "0":
        logging.error("query_history_k_data_plus failed: %s %s", rs.error_code, rs.error_msg)
    kline_list = []
    while rs.next():
        row = rs.get_row_data()
        if row[-1] == "0":  # 停牌时 tradestatus 为 0
            continue
        kline_list.append(
            {
                "datetime": row[0],
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": 0 if row[5] == "" else float(row[5]),
                "amount": 0 if row[6] == "" else float(row[6]),
                "turnover": 0 if row[7] == "" else float(row[7]),
                "change": 0 if row[8] == "" else float(row[8]),
                "preclose": 0 if row[9] == "" else float(row[9]),
            }
        )
    return kline_list


if __name__ == "__main__":
    stocks = list(db.Stock.find(projection=["name"]))

    lg = baostock.login()
    if lg.error_code != "0":
        logging.error("login failed: %s %s", lg.error_code, lg.error_msg)
        exit

    begin = arrow.now().shift(years=-1).datetime
    end = datetime.now()

    progress_total = len(stocks)

    write_op_list = []

    for i, st in enumerate(stocks):
        klines = get_kline_history(st["_id"], "d", begin, end)
        if not klines:
            continue
        write_op_list.append(
            pymongo.UpdateOne(
                {"_id": st["_id"]},
                {
                    "$set": {
                        "name": st["name"],
                        "latest": klines[-1]["datetime"],
                        "day": klines,
                    }
                },
                upsert=True,
            )
        )
        print_progress_bar(i + 1, progress_total, length=40)

    db.Kline.bulk_write(write_op_list)

    baostock.logout()
