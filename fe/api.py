from flask import Blueprint, jsonify

from . import db


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/fundco/<coid>/position")
def get_fund_company_position(coid):
    co_pos = db.FundCompanyPosition.find_one({"_id": coid})
    if not co_pos:
        return {}

    stock_co_pos_list = list(db.StockFundPosition.find({"by_company.{}".format(coid): {"$exists": 1}}))
    stock_co_pos_dict = {it["_id"]: it["by_company"] for it in stock_co_pos_list}

    position = co_pos["position_history"][0]["position"]
    for p in position:
        p["enter_count"] = p["exit_count"] = 0
        stock_co_pos = stock_co_pos_dict.get(p["code"])
        if not stock_co_pos:
            continue
        co_entry = stock_co_pos[coid]
        p["enter_count"] = len(co_entry["enter"])
        p["exit_count"] = len(co_entry["exit"])

    return jsonify(position)


@bp.route("/stock/kline/{sotck_code}")
def get_stock_kline(sotck_code):
    klines = db.Kline.find_one({"_id": sotck_code})
    if not klines:
        return {}
