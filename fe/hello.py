from flask import Flask, g, jsonify, request, render_template

from . import db


def create_app():
    app = Flask(__name__)

    from . import api

    app.register_blueprint(api.bp)

    return app


app = create_app()


@app.route("/fundco/position")
def list_fund_company_position():
    co_pos_list = list(db.FundCompanyPosition.find(projection=["co_name"]))
    return render_template("fund_co_pos.html", co_list=co_pos_list)
