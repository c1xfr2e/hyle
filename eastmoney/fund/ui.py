#!/usr/bin/env python3
# coding: utf-8

import jinja2
import os

from eastmoney.fund import db


REPORT_DATE = "2020-12-31"

TEMPLATE = """
# 基金持仓变动 {{report_date}}

{% for fund in fund_list %}
### {{fund.name}} {{fund.code}}

| 操作 |股票 | 代码 | 股数（万） | 市值（万）| 净值比 |
|:------|:------ |:------|:------|:------|:------|
{% for pc in fund.position_change %}
| <span style="color:{{pc.color}}">{{pc.operation}}</span> | {{pc.name}} | {{pc.code}} | {{pc.volume}} | {{pc.value}} | {{pc.percent}}% |
{% endfor %}

{% endfor %}
"""


def _exclude(fund):
    if not f.get("position_change"):
        return True
    names = ["上证50", "沪深300", "中证500", "联接", "300ETF", "500ETF"]
    for n in names:
        if n in fund["name"]:
            return True
    return False


if __name__ == "__main__":
    # fund = db.Fund.find_one({"_id": "164205"})
    # for pc in fund["position_change"]:
    #     pc["operation"] = {
    #         "open": "新进",
    #         "inc": "加仓",
    #         "dec": "减仓",
    #         "clear": "退出",
    #     }[pc["type"]]
    # tpl = jinja2.Template(TEMPLATE, trim_blocks=True)
    # text = tpl.render(
    #     fund=fund,
    #     report_date="2020-12-31",
    #     position_changes=fund["position_change"],
    # )
    # print(text, end="")

    col_funds = db.Fund.find({})
    fund_list = []
    for f in col_funds:
        if _exclude(f):
            continue
        for pc in f["position_change"]:
            pc["operation"] = {"open": "新进", "inc": "加仓", "dec": "减仓", "clear": "退出"}[pc["type"]]
            pc["color"] = {
                "open": "#d50000",
                "inc": "#f06292",
                "dec": "#26a69a",
                "clear": "green",
            }[pc["type"]]
        fund_list.append(f)

    tpl = jinja2.Template(TEMPLATE, trim_blocks=True)
    text = tpl.render(
        report_date=REPORT_DATE,
        fund_list=fund_list,
    )

    outdir = "./output"
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    with open("./output/position-change-{}.md".format(REPORT_DATE), "w", encoding="utf-8") as f:
        f.write(text)
