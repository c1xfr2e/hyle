from flask import Blueprint, jsonify

from . import db


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/fundco/<coid>/position")
def get_fund_house_position(coid):
    house_pos = db.FundHousePosition.find_one({"_id": coid})
    if not house_pos:
        return {}

    stock_house_pos_list = list(db.StockFundPosition.find({"by_house.{}".format(coid): {"$exists": 1}}))
    stock_house_pos_dict = {it["_id"]: it["by_house"] for it in stock_house_pos_list}

    position = house_pos["position_history"][0]["position"]
    for p in position:
        p["enter_count"] = p["exit_count"] = 0
        stock_house_pos = stock_house_pos_dict.get(p["code"])
        if not stock_house_pos:
            continue
        house_entry = stock_house_pos[coid]
        p["enter_count"] = len(house_entry["enter"])
        p["exit_count"] = len(house_entry["exit"])

    return jsonify(position)


@bp.route("/stock/kline/{sotck_code}")
def get_stock_kline(sotck_code):
    klines = db.Kline.find_one({"_id": sotck_code})
    if not klines:
        return {}
