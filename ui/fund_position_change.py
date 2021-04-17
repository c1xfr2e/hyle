#!/usr/bin/env python3
# coding: utf-8

import jinja2
import os

from phainomena import db
from setting import REPORT_DATE


TEMPLATE = """
# 基金持仓变动 {{report_date}}

{% for fund in fund_list %}
### {{fund.name}} {{fund._id}} <span style="color:dodgerblue">{{fund.size}}亿</span>

| 操作 | 股票 | 代码 | 占流通比 | 净值比 | 净值比变动 |
|:------|:------|:------|:------|:------|:------|
{% for pc in fund.display_position_change %}
| <span style="color:{{pc.color}}">{{pc.operation}}</span> | {{pc.name}} | {{pc.code}} | {{pc.float_percent}}% | {{pc.percent_new}}%| {{pc.net_percent}}% |
{% endfor %}

{% endfor %}
"""


def _exclude_fund(fund):
    names = ["上证50", "沪深300", "中证500", "300ETF", "500ETF"]
    for n in names:
        if n in fund["name"]:
            return True
    return False


def _fund_filter():
    return {
        "size": {"$gte": 3.0},
    }


# TODO: UI feature
def _exclude_position_change(pc):
    if pc["float_percent"] > 0.05:
        return False
    if abs(pc["net_percent"]) < 1.0:
        return True
    return False


OPERATION_COLORS = {
    "enter": "#d50000",
    "inc": "#f06292",
    "dec": "#26a69a",
    "exit": "green",
}

if __name__ == "__main__":
    position_changes = db.FundPositionChange.find(_fund_filter())
    display_fund_list = []
    for pc in position_changes:
        if _exclude_fund(pc):
            continue
        display_position_change = []
        for enter in pc["enter"]:
            if _exclude_position_change(enter):
                continue
            enter["operation"] = "新进"
            enter["color"] = OPERATION_COLORS["enter"]
            display_position_change.append(enter)
        if not display_position_change:
            continue
        display_position_change.sort(key=lambda x: x["float_percent"], reverse=True)
        pc["display_position_change"] = display_position_change
        display_fund_list.append(pc)

    tpl = jinja2.Template(TEMPLATE, trim_blocks=True)
    text = tpl.render(
        report_date=REPORT_DATE,
        fund_list=display_fund_list,
    )

    outdir = "./output"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    with open("./output/position-change-{}.md".format(REPORT_DATE), "w", encoding="utf-8") as f:
        f.write(text)
