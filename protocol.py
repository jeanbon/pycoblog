#!/usr/bin/python
# -*- coding: utf-8 -*-

def error(text=""):
    return "ERROR\n%s" % text

def success(text=""):
    return "OK\n%s" % text

def format_comment(comment):
    return u"\n".join( (comment["author"], comment["title"],
        comment["content"]) )
    
def format_post(post):
    return u"\n".join( (post["title"], ", ".join(post["tags"]),
        post["content"]) )
