#!/usr/bin/env bash

. ./venv/bin/activate

echo "#下载沪深股票列表"
python3 -m download.eastmoney.stock.stock_list

echo "#下载基金持仓"
python3 -m download.eastmoney.fund.fund_position
