from flask import abort, render_template

from . import color, db
from .app import app


def _company_dict_to_list(by_company_dict):
    list_ = []
    for co_id, co_entry in by_company_dict.items():
        co_entry["id"] = co_id
        list_.append(co_entry)
    list_.sort(
        key=lambda x: x["summary"]["quantity"] if x["summary"]["quantity"] != 0 else x["summary"]["quantity_change"],
        reverse=True,
    )
    return list_


def _format_inc_dec_text(val, change):
    if change > 0:
        return '{} (<span style="color:{color}">+{}</span>)'.format(val, change, color=color.Increase)
    elif change < 0:
        return '{} (<span style="color:{color}">{}</span>)'.format(val, change, color=color.Decrease)
    else:
        return val


def _format_fund_inc_dec_number(item, inc_dec, float_shares):
    float_percent_change = round(inc_dec["quantity"] * 10000 * 100 / float_shares, 3)
    if inc_dec["quantity"] > 0:
        item["change_type"] = "加仓"
        item["quantity"] = _format_inc_dec_text(item["quantity"], inc_dec["quantity"])
        item["float_percent"] = _format_inc_dec_text(item["float_percent"], float_percent_change)
    else:
        item["change_type"] = "减仓"
        item["quantity"] = _format_inc_dec_text(item["quantity"], inc_dec["quantity"])
        item["float_percent"] = _format_inc_dec_text(item["float_percent"], float_percent_change)


def _format_co_summary_inc_dec_number(summary):
    summary["quantity"] = _format_inc_dec_text(summary["quantity"], summary["quantity_change"])
    summary["float_percent"] = _format_inc_dec_text(summary["float_percent"], summary["float_percent_change"])
    summary["net_percent"] = _format_inc_dec_text(summary["net_percent"], summary["percent_change"])


def _to_display_list(company, stock_profile):
    summary = company["summary"]
    summary["float_percent"] = round(summary["quantity"] * 10000 * 100 / stock_profile["float_shares"], 3)
    _format_co_summary_inc_dec_number(summary)

    display_funds = []
    enter_dict = {i["fund_code"]: i for i in company["enter"]}
    inc_dec_dict = {i["fund_code"]: i for i in company["inc_dec"]}

    for p in company["latest"]:
        fund_code = p["fund_code"]
        item = {
            "code": p["fund_code"],
            "name": p["fund_name"],
            "fund_size": p["fund_size"],
            "quantity": p["quantity"],
            "float_percent": round(p["quantity"] * 10000 * 100 / stock_profile["float_shares"], 3),
            "net_percent": p["net_percent"],
        }
        if fund_code in enter_dict:
            item["change_type"] = "新进"
        if fund_code in inc_dec_dict:
            _format_fund_inc_dec_number(item, inc_dec_dict[fund_code], stock_profile["float_shares"])
        display_funds.append(item)

    for p in company["exit"]:
        display_funds.append(
            {
                "code": p["fund_code"],
                "name": p["fund_name"],
                "fund_size": p["fund_size"],
                "quantity": p["quantity"],
                "float_percent": round(p["quantity"] * 10000 * 100 / stock_profile["float_shares"], 3),
                "net_percent": p["net_percent"],
                "change_type": "退出",
            }
        )

    return {
        "name": company["name"],
        "logo": company.get("logo"),
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
