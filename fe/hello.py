from flask import Flask, g, jsonify, request, render_template

from . import db


def create_app():
    app = Flask(__name__)
    return app


app = create_app()


@app.route("/fundco/<coid>/position")
def get_fund_company_position(coid):
    co_pos = db.FundCompanyPosition.find_one({"_id": coid})
    if not co_pos:
        return {}
    position = co_pos["position_by_date"][0]["position"]
    for p in position:
        p["fund_count"] = len(p["funds"])
        del p["funds"]
    return jsonify(position)


@app.route("/fundco/position")
def list_fund_company_position():
    co_pos_list = list(db.FundCompanyPosition.find(projection=["co_name"]))
    return render_template("fund_co_pos.tpl", co_list=co_pos_list)
