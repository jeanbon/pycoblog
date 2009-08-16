#!/usr/bin/python
# -*- coding: utf-8 -*-

from cgi import FieldStorage
from blog import Blog, Post, get_value, HOP, VOICE, debug
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
    mode = get_value(post_datas, "mode", "retrieve")
    user = get_value(post_datas, "user")
    password = get_value(post_datas, "password")
    hash = get_value(post_datas, "hash")
    user, power = blog.is_user(user, password, hash)
    post_id = get_value(post_datas, "post", "")
    if mode in ("retrieve", "edit", "del") and not (post_id and
            post_id.isdigit()):
        content.append(protocol.error(_(u"Variable 'post' is not set.")))

    elif mode == "retrieve":
        post = blog.get_posts(post_id=int(post_id))
        if post:
            content.append(protocol.success(protocol.format_post(post)))
        else:
            content.append(protocol.error(_(u"No id %s." % post_id)))

    elif mode == "add":
        if user and blog.has_power(user, VOICE):
            datas = {"author": user, "date": time()}
            for k, d in (("title", u"No title"), ("tags", u""),
                    ("content", u"")):
                datas[k] = get_value(post_datas, k, d)
            new_id = blog.add_post(Post(**datas))
            content.append(protocol.success(unicode(new_id)))
        else:
            content.append(protocol.error(_(u"Wrong username/password.")))

    elif mode == "edit":
        post_id = get_value(post_datas, "post", "")
        datas = {"author": user, "date": time(), "id": int(post_id)}
        for k, d in (("title", u"No title"), ("tags", u""),
                ("content", u"")):
            datas[k] = get_value(post_datas, k, d)
        post = blog.get_posts(post_id=int(post_id))
        if post:
            if user == post["author"] or blog.has_power(user, HOP):
                blog.edit_post(Post(**datas))
                content.append(protocol.success(unicode(datas["id"])))
            else:
                content.append(protocol.error(_(u"You don't have the permission"
                                                 " to do that.")))
        else:
            content.append(protocol.error(_(u"No id %s.")) % post_id)

    elif mode == "del":
        post_id = get_value(post_datas, "post", "")
        post = blog.get_posts(post_id=int(post_id))
        if user == post["author"] or blog.has_power(user, HOP):
            if blog.del_post(post_id):
                content.append(protocol.error(_(u"(internal)")))
            else:
                content.append(protocol.success())
        else:
            content.append(protocol.error(_(u"You don't have the permission to"
                                             " do that.")))

    else:
        content.append(protocol.error(_(u"Wrong mode.")))

    print header
    print u"\n".join(content).encode("utf-8", "replace")

if __name__ == "__main__":
    main()
