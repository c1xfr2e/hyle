#!/usr/bin/env python3
# coding: utf-8

import pymongo


URI = "mongodb://localhost:27017"
DB = "Athena"

cli = pymongo.MongoClient(URI)[DB]

Stock = cli["stock"]
