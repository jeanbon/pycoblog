#!/usr/bin/python
# -*- coding: utf-8 -*-

def print_post(blog, text):
    hax = {"a":"4", "b":"8", "e":"3", "g":"9", "l":"1", "o":"0", "r":"2", "s":"5"}
    for l, r in hax.iteritems():
        text = text.replace(l, r)
    return text

