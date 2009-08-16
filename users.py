#!/usr/bin/python
# -*- coding: utf-8 -*-

from cgi import FieldStorage
from blog import Blog, get_value, ROOT, OP, VOICE
from blog import _
from time import time
import protocol

import cgitb
cgitb.enable()

def main():
    header = u"Content-Type: text/html\n"
    content = []
    blog = Blog()
    post_datas = FieldStorage()
    mode = get_value(post_datas, "mode", "add")
    user = get_value(post_datas, "user")
    password = get_value(post_datas, "password")
    hash = get_value(post_datas, "hash")
    user, power = blog.is_user(user, password, hash)
    post_id = get_value(post_datas, "post")
    target = get_value(post_datas, "target")
    target_password = get_value(post_datas, "target_password")
    power = get_value(post_datas, "power")
    power_exists = (power and power.isdigit() and int(power) < VOICE)
    if not user:
        content.append(protocol.error(_(u"Wrong username/password")))
    elif not (blog.has_power(user, OP if mode == "add" else ROOT) or
            user == post[0]["author"]):
        content.append(protocol.error(_(u"You don't have the permission to do"
                                         " that.")))
    elif not (target and (power_exists and password and mode == "add") or 
             ((power_exists or password) and mode == "edit") or mode == "del"):
        content.append(protocol.error(_(u"Post datas are not set")))
    # It's ok.
    elif mode == "add":
        if not (target_password and power):
            content.append(protocol.error(_(u"Please set a password and"
                                             " permissions.")))
        else:
            ret = blog.add_user(target, target_password, power)
            content.append(protocol.success(ret) if ret else
                    protocol.error(_(u"User exists")))
    elif mode == "edit":
        blog.set_user(target, target_password if target_password else None,
                power if power else None)
        content.append(protocol.success())
    elif mode == "del":
        blog.del_user(target)
        content.append(protocol.success())
    else:
        content.append(protocol.error(_(u"Wrong mode.")))
    print header
    print u"\n".join(content).encode("utf-8", "replace")

if __name__ == "__main__":
    main()
