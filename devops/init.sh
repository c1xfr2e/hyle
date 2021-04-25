#!/usr/bin/env bash

. ./venv/bin/activate

echo "#下载沪深股票列表"
# python3 -m download.eastmoney.stock.stock_list

echo "#下载基金持仓"
python3 -m download.eastmoney.fund.fund_position

echo "#计算基金持仓中的流通比"
python3 -m integrate.float_percent

echo "#计算基金持仓变化"
python3 -m integrate.fund_position_change

echo "#计算基金公司整体持仓"
python3 -m integrate.company_position

echo "#计算基金公司整体持仓变化"
python3 -m integrate.company_position_change

echo "#计算股票基金仓位"
python3 -m integrate.stock_fund_position
