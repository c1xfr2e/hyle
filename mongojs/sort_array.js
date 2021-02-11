
db.fund.aggregate(
  { $match: {_id: "001594"} },
  { $unwind: "$position" },
  { $sort: {
    'position.date': 1
  }}
)