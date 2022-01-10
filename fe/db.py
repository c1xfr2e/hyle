#!/usr/bin/env python3
# coding: utf-8

import pymongo


URI = "mongodb://localhost:27017"
DB = "hyle"

cli = pymongo.MongoClient(URI)[DB]

FundHouse = cli["fund_house"]
Fund = cli["fund"]
Stock = cli["stock"]
StockFundPosition = cli["stock_fund_position"]
FundHousePosition = cli["fund_house_position"]
FundHousePositionChange = cli["fund_house_position_change"]

Kline = cli["kline"]
