#!/usr/bin/env python3
# coding: utf-8

import pymongo


URI = "mongodb://localhost:27017"
DB = "Habermas"

cli = pymongo.MongoClient(URI)[DB]

FundCompany = cli["fund_company"]
Fund = cli["fund"]
