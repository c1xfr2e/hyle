#!/usr/bin/env bash

. ./venv/bin/activate

echo "#计算基金持仓中的流通比"
python3 -m integrate.float_percent

echo "#计算基金持仓变化"
python3 -m integrate.fund_position_change

echo "#计算基金公司整体持仓"
python3 -m integrate.hosue_position

echo "#计算基金公司整体持仓变化"
python3 -m integrate.house_position_change

echo "#计算股票基金仓位"
python3 -m integrate.stock_fund_position
