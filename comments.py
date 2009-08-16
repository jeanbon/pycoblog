#!/usr/bin/python
# -*- coding: utf-8 -*-

from cgi import FieldStorage
from blog import Blog, Comment, get_value
from blog import _
from time import time
import protocol
import sys
sys.path.append("~/python")
import XHTML.tags

import cgitb
cgitb.enable()

def main():
    header = u"Content-Type: text/html\n"
    content = []
    blog = Blog()
    field_storage = FieldStorage()
    post_datas = {}
    for k in ("author", "password", "hash", "title", "content", "post"):
        post_datas[k] = get_value(field_storage, k)
    mode = get_value(field_storage, "mode", "add")
    captcha_code = get_value(field_storage, "captcha_content")
    captcha_path = get_value(field_storage, "captcha_path")
    post_id = get_value(field_storage, "post")
    user, power = blog.is_user(post_datas["author"], post_datas["password"],
            post_datas["hash"])
    if (blog.get_captcha_code(captcha_path) != captcha_code.strip(" ") and
            not user):
        content.append(protocol.error(_(u"Invalid captcha")))
    elif mode in ("edit", "del", "retrieve") and not (post_id and
            raw_post_id.isdigit()):
        content.append(protocol.error(_(u"Need an id")))
    elif mode == "add":
        if not (post_datas["author"] and post_datas["content"]):
            content.append(protocol.error(_(u"You have to write as least your"
                                            " name and a comment.")))
        elif not post_datas["post"]:
            content.append(protocol.error(_(u"Internal : no post ??")))
        else:
            post_datas["date"] = time()
            post_datas["moderated"] = True if blog.config.getboolean("comment",
                    "auto_moderated") else False
            new_id = blog.add_comment(Comment(**post_datas))
            content.append(protocol.success(_(u"Comment added")))
            blog.clean_captchas(captcha_path)
    elif mode == "del":
        if user:
            blog.del_comment(int(post_id))
            content.append(protocol.succes(_(u"Comment deleted")))
        else:
            content.append(protocol.error(_(u"You don't have the permission for"
                                             " doing this.")))
    elif mode == "edit":
        content.append(error(_("Not implemented")))
    elif mode == "retrieve":
        comment = blog.get_comment_by_id(int(post_id))
        if comment:
            content.append(protocol.succes(protocol.format_comment(comment)))
        else:
            content.append(protocol.error(_(u"No id %s") % post_id))
    else:
        content.append(protocol.error(_(u"You're doing it wrong.")))
        
    if post_datas["post"]:
        content.append(XHTML.tags.A(blog.rewrite(post=post_datas["post"]),
                _("Back to the post")).tostr())
    print header
    print u"\n".join(content).encode("utf-8", "replace")

if __name__ == "__main__":
    main()
