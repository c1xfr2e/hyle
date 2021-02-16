from flask import Blueprint, jsonify

from . import db


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/fundco/<coid>/position")
def get_fund_company_position(coid):
    co_pos = db.FundCompanyPosition.find_one({"_id": coid})
    if not co_pos:
        return {}

    position = co_pos["position_by_date"][0]["position"]
    co_pos_change = db.FundCompanyPositionChange.find_one({"_id": coid})
    if co_pos_change:
        enter_dict = {e["code"]: e for e in co_pos_change["enter"]}
        exit_dict = {e["code"]: e for e in co_pos_change["exit"]}
        for p in position:
            p["enter_count"] = p["exit_count"] = 0
            if p["code"] in enter_dict:
                p["enter_count"] = len(enter_dict[p["code"]]["funds"])
            if p["code"] in exit_dict:
                p["exit_count"] = len(exit_dict[p["code"]]["funds"])

    return jsonify(position)
