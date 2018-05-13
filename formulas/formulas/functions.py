#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2016-2017 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl

"""
Python equivalents of various excel functions.
"""
import functools
import collections
import math
import numpy as np
from . import replace_empty, not_implemented, Array, wrap_func
from ..errors import FoundError
from ..tokens.operand import XlError, Error

FUNCTIONS = collections.defaultdict(lambda: not_implemented)


def raise_errors(*args):
    # noinspection PyTypeChecker
    for v in flatten(args, None):
        if isinstance(v, XlError):
            raise FoundError(err=v)


def is_number(number):
    if not isinstance(number, Error):
        try:
            float(number)
        except (ValueError, TypeError):
            return False
    return True


def flatten(l, check=is_number):
    if isinstance(l, collections.Iterable) and not isinstance(l, str):
        for el in l:
            yield from flatten(el, check)
    elif not check or check(l):
        yield l


def wrap_ufunc(func):
    """Helps call a numpy universal function (ufunc)."""

    def safe_eval(*vals):
        try:
            r = func(*map(float, vals))
            if not isinstance(r, XlError) and (np.isnan(r) or np.isinf(r)):
                r = Error.errors['#NUM!']
        except (ValueError, TypeError):
            r = Error.errors['#VALUE!']
        return r

    def wrapper(*args, **kwargs):
        args = map(replace_empty, args)
        return np.vectorize(safe_eval, otypes=[object])(*args).view(Array)

    return wrap_func(functools.update_wrapper(wrapper, func))


FUNCTIONS['ABS'] = wrap_ufunc(np.abs)
FUNCTIONS['ACOS'] = wrap_ufunc(np.arccos)
FUNCTIONS['ACOSH'] = wrap_ufunc(np.arccosh)
FUNCTIONS['ARRAY'] = lambda *args: np.asarray(args, object).view(Array)
FUNCTIONS['ARRAYROW'] = lambda *args: np.asarray(args, object).view(Array)
FUNCTIONS['ASIN'] = wrap_ufunc(np.arcsin)
FUNCTIONS['ASINH'] = wrap_ufunc(np.arcsinh)
FUNCTIONS['ATAN'] = wrap_ufunc(np.arctan)


def xarctan2(x, y):
    return x == y == 0 and Error.errors['#DIV/0!'] or np.arctan2(y, x)


FUNCTIONS['ATAN2'] = wrap_ufunc(xarctan2)
FUNCTIONS['ATANH'] = wrap_ufunc(np.arctanh)


def average(*args):
    l = list(flatten(args))
    return sum(l) / len(l)

def irr(*args):
    l = list(flatten(args))
    return np.irr(l)

def left(from_str, num_chars):
    return str(from_str)[:num_chars]


def mid(from_str, start_num, num_chars):
    return str(from_str)[(start_num-1):((start_num-1)+num_chars)]


def right(from_str, num_chars):
    out = str(from_str)[(0 - int(num_chars)):]
    return str(out)


def find(find_text, within_text, *args):
    if len(args) > 0:
        start_num = (args[0] - 1)
    else:
        start_num = 0
    return str(within_text).find(str(find_text), start_num)


def trim(text):
    return text.strip()


def replace(old_text, start_num, num_chars, new_text):
    return old_text[:(start_num - 1)] + new_text + old_text[(start_num - 1)+num_chars:]


FUNCTIONS['AVERAGE'] = wrap_func(average)
FUNCTIONS['COS'] = wrap_ufunc(np.cos)
FUNCTIONS['COSH'] = wrap_ufunc(np.cosh)
FUNCTIONS['DEGREES'] = wrap_ufunc(np.degrees)
FUNCTIONS['EXP'] = wrap_ufunc(np.exp)
FUNCTIONS['IF'] = wrap_func(lambda c, x=True, y=False: np.where(c, x, y))


def iferror(val, val_if_error):
    return np.where(iserror(val), val_if_error, val)


FUNCTIONS['IFERROR'] = iferror
FUNCTIONS['INT'] = wrap_func(int)


def iserr(val):
    try:
        b = np.asarray([isinstance(v, XlError) and v is not Error.errors['#N/A']
                        for v in val.ravel().tolist()], bool)
        b.resize(val.shape)
        return b
    except AttributeError:  # val is not an array.
        return iserr(np.asarray([[val]], object))[0][0]


FUNCTIONS['ISERR'] = iserr


def iserror(val):
    try:
        b = np.asarray([isinstance(v, XlError)
                        for v in val.ravel().tolist()], bool)
        b.resize(val.shape)
        return b
    except AttributeError:  # val is not an array.
        return iserror(np.asarray([[val]], object))[0][0]


FUNCTIONS['ISERROR'] = iserror
FUNCTIONS['LOG'] = wrap_ufunc(np.log10)
FUNCTIONS['LN'] = wrap_ufunc(np.log)


def xmax(*args):
    raise_errors(args)
    return max(flatten(args))


FUNCTIONS['MAX'] = wrap_func(xmax)


def xmin(*args):
    raise_errors(args)
    return min(flatten(args))


FUNCTIONS['MIN'] = wrap_func(xmin)


def xmod(x, y):
    return y == 0 and Error.errors['#DIV/0!'] or np.mod(x, y)


FUNCTIONS['MOD'] = wrap_ufunc(xmod)
FUNCTIONS['PI'] = lambda: math.pi


def xpower(number, power):
    if number == 0:
        if power == 0:
            return Error.errors['#NUM!']
        if power < 0:
            return Error.errors['#DIV/0!']
    return np.power(number, power)


FUNCTIONS['POWER'] = wrap_ufunc(xpower)
FUNCTIONS['RADIANS'] = wrap_ufunc(np.radians)
FUNCTIONS['SIN'] = wrap_ufunc(np.sin)
FUNCTIONS['SINH'] = wrap_ufunc(np.sinh)


def xsumproduct(*args):
    # Check all arrays are the same length
    # Excel returns #VAlUE! error if they don't match
    raise_errors(args)
    assert len(set(arg.size for arg in args)) == 1
    inputs = []
    for a in args:
        a = a.ravel()
        x = np.zeros_like(a, float)
        b = np.vectorize(is_number)(a)
        x[b] = a[b]
        inputs.append(x)

    return np.sum(np.prod(inputs, axis=0))


FUNCTIONS['SUMPRODUCT'] = wrap_func(xsumproduct)
FUNCTIONS['SQRT'] = wrap_ufunc(np.sqrt)


def xsum(*args):
    raise_errors(args)
    return sum(list(flatten(args)))


FUNCTIONS['SUM'] = wrap_func(xsum)
FUNCTIONS['TAN'] = wrap_ufunc(np.tan)
FUNCTIONS['TANH'] = wrap_ufunc(np.tanh)
FUNCTIONS.update({
    'LEFT': wrap_func(left),
    'MID': wrap_func(mid),
    'RIGHT': wrap_func(right),
    'FIND': wrap_func(find),
    'TRIM': wrap_func(trim),
    'LEN': lambda x: len(str(x)),
    'REPLACE': wrap_func(replace),
    'UPPER': lambda x: str(x).upper(),
    'LOWER': lambda x: str(x).lower()
})
