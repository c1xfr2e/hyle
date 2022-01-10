from flask import render_template, request

from . import db
from .app import app
from .setting import REPORT_DATE


@app.route("/fundco/position")
def list_fund_house_position():
    house_pos_list = list(
        db.FundHousePosition.find(
            {"position_history.0.date": REPORT_DATE},
            projection=["house_name"],
        )
    )
    return render_template(
        "fund_house_pos.html",
        house_list=house_pos_list,
        house_id=house_pos_list[0]["_id"],
    )
