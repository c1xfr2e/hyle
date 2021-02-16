from flask import abort, Flask, render_template

from . import color, db


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


def _company_dict_to_list(by_company_dict):
    list_ = []
    for co_id, co_entry in by_company_dict.items():
        co_entry["id"] = co_id
        list_.append(co_entry)
    list_.sort(
        key=lambda x: x["summary"]["volume"] if x["summary"]["volume"] != 0 else x["summary"]["volume_change"],
        reverse=True,
    )
    return list_


def _format_inc_text(val, inc):
    return '{} (<span style="color:{color}">+{}</span>)'.format(val, inc, color=color.Increase)


def _format_dec_text(val, dec):
    return '{} (<span style="color:{color}">{}</span>)'.format(val, dec, color=color.Decrease)


def _format_inc_dec_number(item, inc_dec, float_shares):
    volume_in_float_change = round(inc_dec["volume"] * 10000 * 100 / float_shares, 3)
    if inc_dec["volume"] > 0:
        item["change_type"] = "加仓"
        item["volume"] = _format_inc_text(item["volume"], inc_dec["volume"])
        item["volume_in_float"] = _format_inc_text(item["volume_in_float"], volume_in_float_change)
    else:
        item["change_type"] = "减仓"
        item["volume"] = _format_dec_text(item["volume"], inc_dec["volume"])
        item["volume_in_float"] = _format_dec_text(item["volume_in_float"], volume_in_float_change)


def _to_display_list(company, stock_profile):
    summary = company["summary"]
    summary["volume_in_float"] = round(summary["volume"] * 10000 * 100 / stock_profile["float_shares"], 3)

    display_funds = []
    enter_dict = {i["fund_code"]: i for i in company["enter"]}
    inc_dec_dict = {i["fund_code"]: i for i in company["inc_dec"]}

    for p in company["latest"]:
        fund_code = p["fund_code"]
        item = {
            "code": p["fund_code"],
            "name": p["fund_name"],
            "fund_size": p["fund_size"],
            "volume": p["volume"],
            "volume_in_float": round(p["volume"] * 10000 * 100 / stock_profile["float_shares"], 3),
            "percent": p["percent"],
        }
        if fund_code in enter_dict:
            item["change_type"] = "新进"
        if fund_code in inc_dec_dict:
            _format_inc_dec_number(item, inc_dec_dict[fund_code], stock_profile["float_shares"])
        display_funds.append(item)

    for p in company["exit"]:
        display_funds.append(
            {
                "code": p["fund_code"],
                "name": p["fund_name"],
                "fund_size": p["fund_size"],
                "volume": p["volume"],
                "volume_in_float": round(p["volume"] * 10000 * 100 / stock_profile["float_shares"], 3),
                "percent": p["percent"],
                "change_type": "退出",
            }
        )

    return {
        "name": company["name"],
        "funds": display_funds,
        "summary": summary,
    }


CHANGE_TYPE_STYLES = {
    "新进": "color:{};font-weight: bold;".format(color.Enter),
    "退出": "color:{};font-weight: bold;".format(color.Exit),
    "加仓": "color:{}".format(color.Increase),
    "减仓": "color:{}".format(color.Decrease),
}

REPORT_DATE = "2020-12-31"


@app.route("/stock/<id_>/fundpos")
def get_stock_fund_position(id_):
    stock = db.Stock.find_one({"_id": id_})
    col = db.StockFundPosition.find_one({"_id": id_})
    if not stock or not col:
        abort(404, description="{} not found".format(id_))

    company_list = _company_dict_to_list(col["by_company"])
    display_list = [_to_display_list(co, stock["profile"]) for co in company_list]

    render_param = {
        "stock_name": " ".join([c for c in stock["name"]]),
        "stock_code": id_,
        "report_date": REPORT_DATE,
        "company_list": display_list,
        "change_type_styles": CHANGE_TYPE_STYLES,
    }
    return render_template("stock_fund_pos.html", **render_param)
