#!/usr/bin/env python3
# coding: utf-8

import pymongo


URI = "mongodb://localhost:27017"
DB = "hyle"

cli = pymongo.MongoClient(URI)[DB]

FundCompany = cli["fund_company"]
Fund = cli["fund"]
Stock = cli["stock"]

FundPositionChange = cli["fund_position_change"]
FundCompanyPosition = cli["fund_company_position"]
