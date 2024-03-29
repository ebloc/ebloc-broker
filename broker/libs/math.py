#!/usr/bin/env python3

from broker._utils.tools import log


def _percent(amount, ratio) -> float:
    return float(format(amount * ratio / 100, ".2f"))


def _percent_change(initial: float, final=None, change=None, decimal: int = 2) -> float:
    try:
        initial = float(initial)
        if final:
            final = float(final)
        if change:
            change = float(change)
    except ValueError as e:
        raise e

    try:
        if change:
            return round(change / abs(initial) * 100, decimal)
        else:
            return round((final - initial) / abs(initial) * 100, decimal)
    except:
        return 0.0


def percent_change(initial, change, _decimal=8, end=None, is_arrow=True) -> float:
    try:
        initial = float(initial)
        change = float(change)
    except ValueError as e:
        raise e

    change = "{0:.8f}".format(float(change))
    # percent = round((float(change)) / abs(float(initial)) * 100, 8)
    percent = _percent_change(initial=initial, change=change, decimal=_decimal)
    if percent == -0.0:
        change = 0.0
        _color = "white"
    elif percent > 0:
        _color = "green"
    else:
        _color = "red"

    if abs(float(change)) < 0.1:
        change = "{0:.8f}".format(float(change))
    else:
        change = "{0:.2f}".format(float(change))

    if is_arrow:
        log(f"{format(initial, '.4f')} => ", end="")
        log(f"{format(float(initial) + float(change), '.4f')} ", "blue", end="")

    if float(change) >= 0:
        change = " " + change

    if is_arrow:
        log(f"{change}({format(float(percent), '.2f')}%) ", _color, end=end)
    else:
        log(f"({format(float(percent), '.2f')}%) ", _color, end=end)

    return percent
