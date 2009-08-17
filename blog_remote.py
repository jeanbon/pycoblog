#!/usr/bin/python
# -*- coding: utf-8 -*-

# Structure : 
# 
# - Create a temporary file, with the title, the tags, and the content,
# - open the editor to edit this
# - send the datas

from __future__ import with_statement
import os
from sys import stderr, argv, exit
from shutil import move
from shutil import Error as ShutilError
from tempfile import mkstemp
from codecs import open
from getopt import gnu_getopt, GetoptError
import urllib

EDITOR = ""
COMMENTS = u"%%%%"
BASE_STRUCTURE = u"""
%%%% vim: set spell spelllang=fr filetype=html expandtab shiftwidth=4 softtabstop=4 textwidth=79:
"""

# (user, password, hashed password ?)
USER = (u"foo", u"bar", False)

POST_ADDRESS = u"http://pycoblog.alwaysdata.net/dev/posts.py"
USERS_ADDRESS = u"http://pycoblog.alwaysdata.net/dev/users.py"

USAGE = u"""Usage: %(self)s post_action [-h] [ident] [-f file] [post]
   or: %(self)s user_action [-h] [ident] user [-t password] [-l power]
   post_actions are : add|edit|del
        edit and del actions need a post number
   user_actions are : useradd|useredit|userdel
        useredit and useradd need the power argument which is the permission
  -h or --help :              display this help
  -f or --file :              use a file with a predefined content
  -t or --target-password :   the new password of the user to create or edit
  -l or --level :             the level ef the new user to create or edit
  ident : -u or --user : set your user name
          -p or --pasword: set your password
          -a or --hash   : set the hash of your password
When you edit a post, the first line contains the title, the seconds contains
the tags separated by commas, and the others the text.
Everything after a "%(sep)s" is ignored.
""" % {"self": os.path.basename(argv[0]), "sep": COMMENTS}

def clean(file, ask=True):
    try:
        c = (raw_input(u"Remove file `%s' ? [y]es/[n]o  " % file) if ask
                else "y")
        if c and c[0].lower() in ("y", "o"):
            os.remove(file)
        return 0
    except OSError:
        return 1

def edit(file, verb=True):
    env_editor = os.getenv("EDITOR")
    editor = EDITOR if EDITOR else (env_editor if env_editor else "nano")
    if verb:
        raw_input(u"Editing the post with %s... (press enter)" % editor)
    os.system("%s '%s'" % (editor, file))
    with open(file, "r", "utf-8") as file:
        lines = [l.split(COMMENTS)[0].rstrip("\n") for l in file.readlines()]
    return lines

def is_error(text):
    return True if text.startswith("ERROR") else False

def save(file):
    c = raw_input(u"Save the file ? [y]es/[n]o : ")
    if c and c[0].lower() not in ("o", "y"):
        clean(file)
        return
    print u"Where ?"
    path = ""
    while not path or (os.path.dirname(path) and not
            os.path.exists(os.path.dirname(path))):
        path = raw_input("> ")
    try:
        move(file, path)
    except ShutilError, e:
        print >>stderr, u"Unable to move file %s to %s" % (file, path)

def retrieve(post_id):
    content = send(**{"post": post_id, "mode": "retrieve"})
    return (content.replace("OK\n", "", 1) if content.startswith("OK")
            else content)

def send(link=POST_ADDRESS, **post):
    for k, v in post.iteritems():
        if isinstance(v, unicode):
            post[k] = v.encode("utf-8", "replace")
    req = urllib.urlencode(post)
    page = urllib.urlopen(link, req)
    return page.read()

def main():
    file_name = ""
    content = ""
    mode = "edit"
    target = {"power": None, "target_password": None}
    post_datas = {
                  "user":   USER[0],
                  "password": USER[1] if not USER[2] else "",
                  "hash":     USER[2] if USER[2] else "",
                  "mode":     u"add"
                 }
    try:
        opts, args = gnu_getopt(argv[1:], "hf:u:p:a:t:l:", ("help", "file=",
            "user=", "password=", "hash=", "target-password=", "level="))
    except GetoptError, e:
        print >>stderr, u"Parsing error : %s" % e
        return 1
    for o, a in opts:
        if o in ("-h", "--help"):
            print USAGE
            return 0
        elif (o in ("-f", "--file") and (os.path.exists(os.path.dirname(a))
                or not os.path.dirname(a))):
            file_name = a
        elif o in ("-d", "--delete") and a.isdigit():
            mode = "delete"
        elif o in ("-u", "--user"):
            post_datas["user"] = a
        elif o in ("-p", "--password"):
            post_datas["password"] = a
            post_datas["hash"] = ""
        elif o in ("-a", "--hash"):
            post_datas["hash"] = a
            post_datas["password"] = ""
        elif o in ("-t", "--target-password"):
            target["target_password"] = a
        elif o in ("-l", "--level"):
            target["power"] = a
        else:
            print USAGE
            return 1
    if args:
        mode, args = args[0], args[1:]
    else:
        print "There is no action, then add a post."
        mode = "add"
    if mode in ("useradd", "userdel", "useredit", "del", "edit") and not args:
        print >>stderr, "\"%s\" needs more arguments" % mode
        return 1
    if mode in ("useradd", "userdel", "useredit"):
        if len(args) == 1:
            user, power = args[0], ""
        else:
            user, power = args[:2]
        post_datas.update({"mode": mode[4:], "target": user})
        for k, v in target.iteritems():
            if v is not None:
                post_datas[k] = v
        print send(link=USERS_ADDRESS, **post_datas)

    elif mode in ("edit", "add"):
        if mode == "edit":
            if args:
                post_datas.update({"mode": "edit", "post": args[0]})
                content = retrieve(args[0])
            else:
                print >> stderr, u"Edit mode needs more arguments"
                return 1
        if not file_name:
            fd, file_name = mkstemp(prefix="blog.", dir="tmp/")
            file = os.fdopen(fd, "w")
            file.write(content if content else BASE_STRUCTURE)
            file.close()
        ok = False
        structure = (u"\n   Write the title on the first line and only on this "
                      "line.\n   Write the tags separated by commas, only on "
                      "the second line\n   And bellow, the post content\n")
        print structure
        while not ok:
            lines = edit(file_name)
            if len(lines) < 3:
                print >>stderr, (u"This structure is not correct.")
                print structure
                c = raw_input(u"Edit again ? [y]es/[n]o  ")[0]
                if c and c[0].lower() == "n":
                    save(file_name)
                    return 0
            else:
                title = lines[0]
                tags = lines[1]
                content = "\n".join(lines[2:])
                print u"\nTitle :", title
                print u"Tags :", tags
                print u"Content :\n", content
                c = raw_input(u"Is this ok ? [y]es/[n]o/[q]uit  ")
                ok = not c or c[0].lower() not in ("n", "q")
                if c and c[0].lower() == "q":
                    save(file_name)
                    return 0
        c = raw_input(u"Send this post ? [y]es/[n]o  ")
        if not c or c[0].lower() is not "n":
            post_datas.update({"title": title, "tags": tags, "content": content})
            print send(**post_datas)
            clean(file_name)
        else:
            save(file_name)

    elif mode == "del":
        post_datas.update({"mode": "del", "post": args[0]})
        content = retrieve(args[0])
        print content
        if is_error(content):
            return 1
        c = raw_input(u"Remove this post ? [y]es/[n]o  ")
        if c and c[0].lower() in ("y", "o"):
            print send(**post_datas)

    elif mode == "delcomment":
        pass

    else:
        print "%s is not a correct action." % mode

if __name__ == "__main__":
    exit(main())
