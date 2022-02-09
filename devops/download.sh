#!/usr/bin/env bash

. ./venv/bin/activate

echo "沪深股票列表"
python3 -m download.eastmoney.stock.stock_list

echo "基金公司"
python3 -m download.eastmoney.fund.house_list

echo "基金"
python3 -m download.eastmoney.fund.fund_list

echo "基金持仓"
python3 -m download.eastmoney.fund.fund_position
