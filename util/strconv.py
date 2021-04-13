#!/usr/bin/env python3
# coding: utf-8


CN_MONEY_UNIT = {
    u"元": 1,
    u"千": 1000,
    u"万": 10 ** 4,
    u"亿": 10 ** 8,
    u"万亿": 10 ** 12,
}


def to_float(text):
    if not text or text in ["-", "--", "---"]:
        return 0.0
    return float(text)


def to_percent(text):
    if not text[-1] == "%":
        return 0.0
    return float(text[0:-1])


def parse_cn_text(s: str):
    """
    Parse Chinese text to number:
        '21.62亿' --> 21.62 * 10^8
        '3215万' --> 3215 * 10^5
    """
    if s[-2:] == u"万亿":
        return float(s[0:-2] * (10 ** 12))

    # TODO: Check regex match numbers: \-?[0-9]*(\.[0-9]*)?

    if not s[-1] in CN_MONEY_UNIT:
        return float(s)
    unit = CN_MONEY_UNIT.get(s[-1])
    return float(s[0:-1]) * float(unit)


def cn_to_int(s):
    # 中文转 int
    num = parse_cn_text(s)
    return int(num) if num is not None else 0


def cn_to_float(s):
    # 中文转 float
    num = parse_cn_text(s)
    return float(num) if num is not None else 0.0


if __name__ == "__main__":
    n = parse_cn_text("21.62亿")
    assert n == int(21.62 * 10 ** 8)
    n = parse_cn_text("3215万")
    assert n == 3215 * 10 ** 4

    try:
        _ = parse_cn_text("-")
    except Exception as e:
        print(e)
