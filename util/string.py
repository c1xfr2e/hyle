#!/usr/bin/env python3
# coding: utf-8

from decimal import Decimal


CN_MONEY_UNIT = {
    u"元": 1,
    u"万": 10 ** 4,
    u"亿": 10 ** 8,
}


def str_to_percent(text):
    if not text[-1] == "%":
        return 0.0
    return float(text[0:-1])


def parse_number_text(s: str):
    """
    Convert string to number:
        '21.62亿' --> 21.62 * 10^8
        '3215万' --> 3215 * 10^5
    """

    # TODO: Check regex match numbers: \-?[0-9]*(\.[0-9]*)?

    if not s[-1] in CN_MONEY_UNIT:
        return Decimal(s)
    unit = CN_MONEY_UNIT.get(s[-1])
    return Decimal(s[0:-1]) * Decimal(unit)


def str_to_int(s):
    num = parse_number_text(s)
    return int(num) if num is not None else 0


def str_to_float(s):
    num = parse_number_text(s)
    return float(num) if num is not None else 0.0


def number_or_zero(data, conv, zero=0):
    try:
        return conv(data)
    except Exception:
        return zero


if __name__ == "__main__":
    n = parse_number_text("21.62亿".decode("utf8"))
    assert n == int(21.62 * 10 ** 8)
    n = parse_number_text("3215万")
    assert n == 3215 * 10 ** 4

    try:
        _ = parse_number_text("-")
    except Exception as e:
        print(e)
