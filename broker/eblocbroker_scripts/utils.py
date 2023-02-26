#!/usr/bin/python3

"""
Forked forked from https://github.com/eth-brownie/brownie/blob/master/brownie/convert/datatypes.py.
"""

# from copy import deepcopy
from decimal import Decimal, getcontext
from typing import Any, TypeVar

try:
    from vyper.exceptions import DecimalOverrideException
except ImportError:
    DecimalOverrideException = BaseException  # regular catch blocks shouldn't catch

from hexbytes import HexBytes

UNITS = {
    "cent": 0,
    "dime": 1,
    "usd": 2,
}

CentInputTypes = TypeVar("CentInputTypes", str, float, int, None)


class Cent(int):
    """Integer subclass that converts a value to cent and allows comparison against
    similarly formatted values.

    Useful for the following formats:
        * a string specifying the unit: "10 cent", "300 dime", "0.25 usd"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124\" """

    # Known typing error: https://github.com/python/mypy/issues/4290
    def __new__(cls, value: Any) -> Any:  # type: ignore
        return super().__new__(cls, _to_cent(value))  # type: ignore

    def __hash__(self) -> int:
        return super().__hash__()

    def __lt__(self, other: Any) -> bool:
        return super().__lt__(_to_cent(other))

    def __le__(self, other: Any) -> bool:
        return super().__le__(_to_cent(other))

    def __eq__(self, other: Any) -> bool:
        try:
            return super().__eq__(_to_cent(other))
        except TypeError:
            return False

    def __ne__(self, other: Any) -> bool:
        try:
            return super().__ne__(_to_cent(other))
        except TypeError:
            return True

    def __ge__(self, other: Any) -> bool:
        return super().__ge__(_to_cent(other))

    def __gt__(self, other: Any) -> bool:
        return super().__gt__(_to_cent(other))

    def __add__(self, other: Any) -> "Cent":
        return Cent(super().__add__(_to_cent(other)))

    def __sub__(self, other: Any) -> "Cent":
        return Cent(super().__sub__(_to_cent(other)))

    def to(self, unit: str) -> "Fixed":
        """
        Returns a converted denomination of the stored cent value.
        Accepts any valid ether unit denomination as string, like:
        "gcent", "milliether", "finney", "ether".

        :param unit: An ether denomination like "ether" or "gcent"
        :return: A 'Fixed' type number in the specified denomination
        """
        try:
            return Fixed(self * Fixed(10) ** -UNITS[unit])
        except KeyError:
            raise TypeError(f'Cannot convert cent to unknown unit: "{unit}". ') from None

    def decimals(self):
        return 2

    def usdt(self, balance):
        return float(balance) * (10 ** self.decimals())


def _to_cent(value: CentInputTypes) -> int:
    original = value
    if isinstance(value, bytes):
        value = HexBytes(value).hex()
    if value is None or value == "0x":
        return 0
    if isinstance(value, float) and "e+" in str(value):
        num_str, dec = str(value).split("e+")
        num = num_str.split(".") if "." in num_str else [num_str, ""]
        return int(num[0] + num[1][: int(dec)] + "0" * (int(dec) - len(num[1])))
    if not isinstance(value, str):
        return _return_int(original, value)
    if value[:2] == "0x":
        return int(value, 16)
    for unit, dec in UNITS.items():
        if " " + unit not in value:
            continue
        num_str = value.split(" ")[0]
        num = num_str.split(".") if "." in num_str else [num_str, ""]
        return int(num[0] + num[1][: int(dec)] + "0" * (int(dec) - len(num[1])))
    return _return_int(original, value)


def _return_int(original: Any, value: Any) -> int:
    try:
        return int(value)
    except ValueError:
        raise TypeError(f"Cannot convert {type(original).__name__} '{original}' to cent.")


class Fixed(Decimal):
    """
    Decimal subclass that allows comparison against strings, integers and Cent.

    Raises TypeError when operations are attempted against floats.
    """

    # Known typing error: https://github.com/python/mypy/issues/4290
    def __new__(cls, value: Any) -> Any:  # type: ignore
        return super().__new__(cls, _to_fixed(value))  # type: ignore

    def __repr__(self) -> str:
        return f"Fixed('{str(self)}')"

    def __hash__(self) -> int:
        return super().__hash__()

    def __lt__(self, other: Any) -> bool:  # type: ignore
        return super().__lt__(_to_fixed(other))

    def __le__(self, other: Any) -> bool:  # type: ignore
        return super().__le__(_to_fixed(other))

    def __eq__(self, other: Any) -> bool:  # type: ignore
        if isinstance(other, float):
            raise TypeError("Cannot compare to floating point - use a string instead")
        try:
            return super().__eq__(_to_fixed(other))
        except TypeError:
            return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, float):
            raise TypeError("Cannot compare to floating point - use a string instead")
        try:
            return super().__ne__(_to_fixed(other))
        except TypeError:
            return True

    def __ge__(self, other: Any) -> bool:  # type: ignore
        return super().__ge__(_to_fixed(other))

    def __gt__(self, other: Any) -> bool:  # type: ignore
        return super().__gt__(_to_fixed(other))

    def __add__(self, other: Any) -> "Fixed":  # type: ignore
        return Fixed(super().__add__(_to_fixed(other)))

    def __sub__(self, other: Any) -> "Fixed":  # type: ignore
        return Fixed(super().__sub__(_to_fixed(other)))


def _to_fixed(value: Any) -> Decimal:
    if isinstance(value, float):
        raise TypeError("Cannot convert float to decimal - use a string instead")

    if isinstance(value, (str, bytes)):
        try:
            value = Cent(value)
        except TypeError:
            pass
    try:
        try:
            # until vyper v0.3.1 we can mess with the precision
            ctx = getcontext()
            ctx.prec = 78
        except DecimalOverrideException:
            pass  # vyper set the precision, do nothing.
        return Decimal(value)
    except Exception as e:
        raise TypeError(f"Cannot convert {type(value).__name__} '{value}' to decimal.") from e
