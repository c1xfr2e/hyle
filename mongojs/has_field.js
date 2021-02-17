
db.stock_fund_position.find(
  {"by_company.80053708": {"$exists": 1}}
)
