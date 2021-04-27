"""
    Baostock 获取历史A股K线数据

    文档: http://baostock.com/baostock/index.php/Python_API%E6%96%87%E6%A1%A3
"""

import baostock as bs
import logging


def get_kline_history(code, frequency, begin, end):
    rs = bs.query_history_k_data_plus(
        "{market}.{stock}".format(market="sh" if code[0] == "6" else "sz", stock=code),
        "date,open,close,high,low,volume,amount,turn,pctChg,preclose,tradestatus",
        start_date=begin,
        end_date=end,
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
                "volume": float(row[5]),
                "amount": float(row[6]),
                "turnover": float(row[7]),
                "change": float(row[8]),
                "preclose": float(row[9]),
            }
        )
    return kline_list


if __name__ == "__main__":
    lg = bs.login()
    if lg.error_code != "0":
        logging.error("login failed: %s %s", lg.error_code, lg.error_msg)
        exit

    klines = get_kline_history("601328", "d", "2021-04-26", "2021-04-27")

    print(klines)

    bs.logout()
