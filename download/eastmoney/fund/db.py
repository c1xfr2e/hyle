#!/usr/bin/env python3
# coding: utf-8

import pymongo


URI = "mongodb://localhost:27017"
DB = "hyle"

cli = pymongo.MongoClient(URI)[DB]

FundHouse = cli["fund_house"]
Fund = cli["fund"]
Stock = cli["stock"]
