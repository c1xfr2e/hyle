#!/usr/bin/env python3
# coding: utf-8

import pymongo


URI = "mongodb://localhost:27017"
DB = "hyle"

cli = pymongo.MongoClient(URI)[DB]

# 基金公司
FundHouse = cli["fund_house"]

# 基金
Fund = cli["fund"]

# 基金持仓变动
FundPositionChange = cli["fund_position_change"]

# 基金公司持仓
FundHousePosition = cli["fund_house_position"]

# 基金公司持仓变动
FundHousePositionChange = cli["fund_house_position_change"]

# 股票基本信息
Stock = cli["stock"]

# 股票基金持仓情况
StockFundPosition = cli["stock_fund_position"]

# K线
Kline = cli["kline"]
