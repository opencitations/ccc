#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

__author__ = 'essepuntato'
import re

def lower(s):
    return s.lower(),


def split_dois(s):
    return "\"%s\"" % "\" \"".join(s.split("__")),


def remove_duplicates(res):
    res_dict = {}

    for row in res[1:]:
        t1, v1 = row[0]  # name of author 1
        t2, v2 = row[1]  # name of author 2
        t3, v3 = row[2]  # co-authorship count

        a = tuple(sorted((v1, v2)))
        if a not in res_dict:
            res_dict[a] = 0

        res_dict[a] += t3

    final_res = []
    for k, v in res_dict.items():
        a1 = k[0]
        a2 = k[1]
        final_res.append([(a1, a1), (a2, a2), (v, str(v))])

    return [res[0]] + sorted(final_res), True
