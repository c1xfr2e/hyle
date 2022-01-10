#!/usr/bin/env python3
# coding: utf-8

import pymongo


def copy_habermas():
    URI = "mongodb://localhost:27017"
    cli_src = pymongo.MongoClient(URI)["Habermas"]
    cli_dst = pymongo.MongoClient(URI)["hyle"]
    Company = cli_src["company"]
    Fund = cli_src["fund"]

    company_inserts = [pymongo.InsertOne(doc) for doc in Company.find({})]
    cli_dst["fund_house"].bulk_write(company_inserts)

    fund_inserts = [pymongo.InsertOne(doc) for doc in Fund.find({})]
    cli_dst["fund"].bulk_write(fund_inserts)


def copy_athena():
    URI = "mongodb://localhost:27017"
    cli_src = pymongo.MongoClient(URI)["Athena"]
    cli_dst = pymongo.MongoClient(URI)["hyle"]
    Stock = cli_src["stock"]

    stock_inserts = [pymongo.InsertOne(doc) for doc in Stock.find({})]
    cli_dst["stock"].bulk_write(stock_inserts)


if __name__ == "__main__":
    copy_habermas()
    copy_athena()
