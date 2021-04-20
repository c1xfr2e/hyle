from flask import render_template

from . import db
from .app import app
from .setting import REPORT_DATE


@app.route("/fundco/position")
def list_fund_company_position():
    co_pos_list = list(
        db.FundCompanyPosition.find(
            {"position_history.0.date": REPORT_DATE},
            projection=["co_name"],
        )
    )
    return render_template("fund_co_pos.html", co_list=co_pos_list)
