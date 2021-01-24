#!/usr/bin/env python3

from broker._utils.tools import log


def _percent_change(initial: float, final=None, change=None, decimal: int = 2):
    try:
        initial = float(initial)
        if final:
            final = float(final)
        if change:
            change = float(change)
    except ValueError:
        return None
    else:
        if change is not None:
            try:
                initial = abs(initial)
                return round(change / abs(initial) * 100, decimal)
            except:
                return 0.0

        else:
            try:
                change = final - initial
                return round(change / abs(initial) * 100, decimal)
            except:
                return 0.0


def percent_change(initial, change, _decimal=8, is_color=False, end=None, is_arrow_print=True):
    try:
        initial = float(initial)
        change = float(change)
    except ValueError:
        return None

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

    if is_arrow_print:
        log(f"{format(initial, '.4f')} => ", end="")
        log(f"{format(float(initial) + float(change), '.4f')} ", end="", color="blue")

    if float(change) >= 0:
        change = " " + change

    if is_arrow_print:
        log(f"{change}({format(float(percent), '.2f')}%) ", color=_color, end=end)
    else:
        log(f"({format(float(percent), '.2f')}%) ", color=_color, end=end)

    return percent
