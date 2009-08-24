#!/usr/bin/python
# -*- coding: utf-8 -*-

# I would like to apologize to the people who read this for the poor english
# used in the comments. I really try to write it well, but I'm a french with
# little english skill.

from __future__ import with_statement
import os
from sys import argv, path as sys_path
from time import time, ctime
from datetime import datetime
from re import sub, match
from math import ceil
from copy import copy

from codecs import open as copen
from urllib import quote_plus
from ConfigParser import SafeConfigParser, NoOptionError
from types import ModuleType

from utils.html.structure import XHTMLStructure
import utils.html.xhtmltags as t
from utils.rfc3339 import rfc3339
from utils.captcha import generate_captcha

from cgi import FieldStorage

import gettext
import locale
# TODO use the config file : global var ?
os.environ["LANG"] = "fr_FR.utf-8"
os.environ["LANGUAGE"] = "fr"
gettext.bindtextdomain("blog", "locale")
gettext.textdomain("blog")
#_ = gettext.gettext
def _(text):
    return gettext.gettext(text)

# DEBUGING PART
import cgitb
cgitb.enable()
import logging

def debug(*args):
    with copen("debug.log", "a", "utf-8") as f:
        f.write("::".join(unicode(a) for a in args) + "\n")
#cgitb.enable(display=0, logdir="tmp")

#DEBUG_OPEN = False
#if DEBUG_OPEN:
#    _open = open
#    OPEN_COUNTER = []
#    import inspect
#    def open(file, mode, encoding=None, errors="strict", buffering=1):
#        OPEN_COUNTER.append([", ".join(reversed(zip(*inspect.stack()[1:-1]
#                )[3])), file, mode])
#        return _open(file, mode, encoding, errors, buffering)
# END OF DEBUGING

# TODO
# - Ajouter des mails aux utilisateurs
# - le gros : FILTRES
# - l'autre gros : création de pages statiques 
#   => ajouter un titre correct, du genre "12-ceci-est-un-titre"
#      cela permettrait à la fois des meilleurs liens pour le dynamique,
#      et une création depages statiques
#      modification des pages : à l'édition, la supression, l'ajout de posts
#      à l'ajout de commentaires ?
#   => l'index peut-il être statique ?
# - améliorer les captchas
# * optimisation : moins de lectures dans les fichiers
#   => index : lorsqu'il a été lu une fois, conserver un tuple.
#              et lorsqu'on écris dedans, modifier celui-çi
# * Des logs corrects, avec genre logger


ROOT, OP, HOP, VOICE = range(4)


class Config(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)

    def get(self, section, option, raw=False, vars=None):
        return unicode(SafeConfigParser.get(self, section, option, raw, vars),
                "utf-8")

    def get_blog(self, opt, default=None, t=None):
        """
        get the option in the 'blog' section
        t can be int, float or boolean
        """
        if t:
            fun = getattr(self, "get%s" % t)
        else:
            fun = self.get
        try:
            return fun("blog", opt)
        except NoOptionError:
            return default


class Comment(dict):
    """
    A simple dict with default values :
        id, post, author, title, date, content and moderated are initialized
    """
    def __init__(self, args=None, sep="", **kwargs):
        dict.__init__(self, **kwargs)
        if args and sep:
            self.split(sep, args)
        else:
            getd = (lambda k, d: kwargs.setdefault(k, d))
            self["id"] = int(getd("id", 0))
            self["post"] = int(getd("post", 0))
            self["date"] = float(getd("date", 0))
            self["author"] = getd("author", "")
            self["title"] = getd("title", "")
            self["content"] = getd("content", "")
            self["moderated"] = getd("moderated", False)

    def __setitem__(self, x, y):
        if x in ("id", "post"):
            z = int(y)
        elif x in ("date",):
            z = float(y)
        elif x in ("moderated",) and is_str(y):
            z = True if y[0].lower() == "t" else False
        else:
            z = y
        dict.__setitem__(self, x, z)

    def join(self, sep):
        return sep.join(unicode(i) for i in (self["id"], self["post"],
            self["date"], self["author"], self["title"], self["moderated"]))

    def split(self, sep, line):
        elems = sep.split(line) if is_str(line) else line
        self["id"] = elems[0]
        self["post"] = elems[1]
        self["date"] = elems[2]
        self["author"] = elems[3]
        self["title"] = elems[4]
        self["moderated"] = elems[5]
        self["content"] = ""


class Post(dict):
    """
    A simple dict with default values :
        id, author, title, date, tags and content are initialized
    """
    def __init__(self, args=None, sep="", **kwargs):
        dict.__init__(self, **kwargs)
        if args and sep:
            self.split(sep, args)
        else:
            getd = (lambda k, d: kwargs.setdefault(k, d))
            self["id"] = int(getd("id", 0))
            self["author"] = getd("author", "")
            self["title"] = getd("title", "")
            self["date"] = float(getd("date", 0))
            self["tags"] = getd("tags", list())
            self["content"] = getd("content", "")

    def __setitem__(self, x, y):
        if x in ("id",):
            z = int(y)
        elif x in ("date",):
            z = float(y)
        elif x in ("tags",) and is_str(y):
            z = [i.rstrip(" ").lstrip(" ") for i in y.split(",")]
        else:
            z = y
        dict.__setitem__(self, x, z)

    def join(self, sep):
        return sep.join([unicode(i) for i in (self["id"], self["date"],
            self["author"], self["title"], ",".join(self["tags"]))])

    def split(self, sep, line):
        elems = sep.split(line) if is_str(line) else line
        self["id"] = elems[0]
        self["date"] = elems[1]
        self["author"] = elems[2]
        self["title"] = elems[3]
        self["tags"] = elems[4]
        self["content"] = ""

    def ascii(self):
        new_dict = {}
        for k, v in self.iteritems():
            if isinstance(v, unicode):
                new_dict[k] = v.decode("ascii", "replace")
            else:
                new_dict[k] = v
        return new_dict



class Blog(object):
    """ 
    Class for creating a simple, minimalist blog, with articles, comments,
    and simple headers and footers.
    example :
        >>> blog = Blog(config_file="blog.cfg")
        >>> print blog.print_page(page=2)
         or 
        >>> print blog.print_page(search="foo")
         or
        >>> print blog.print_page(post=3)

    configuration file :
    TODO => man file/documentation online
    sections are : blog, header, footer, post, comments, url_rewriting, filters
    format look like : {l:[item1][item2]} {c:[item3]} {r:[item4] [item5]}
    """
    def __init__(self, config_file="config", init_file="init"):
        self.config = Config()
        self.config.read(config_file)
        logging.basicConfig(filename=self.config.get_blog("log_file",
                            "debug.log"), level=logging.DEBUG)
        self.logger = logging.getLogger()
        main_dir = self.config.get_blog("directory", "blog")
        self.posts_directory = self.config.get_blog("posts_directory",
                os.path.join(main_dir, "articles"))
        self.posts_index = os.path.join(self.posts_directory, "index")
        self.comments_directory = self.config.get_blog("comments_directory",
                os.path.join(main_dir, "comments"))
        self.comments_index = os.path.join(self.comments_directory, "index")
        self.captchas_directory = self.config.get_blog("captchas_directory",
                os.path.join(main_dir, "captchas"))
        self.captchas_index = os.path.join(self.captchas_directory, "index")
        self.users_index = os.path.join(main_dir, "users")
        # Initialize filters
        self.modules = [] # A SortedDict would be better...
        self.filters_outputs = {
                "add_post": str,
                "print_post": basestring,
                "add_comment": str,
                "print_comment": str,
                "trusted_comment":bool,
                "format_date": str # breaks the combo :/
                }
        sys_path.append(self.config.get("filters", "path",
            vars={"directory":main_dir}))
        for f in self.config.get("filters", "modules").split(" "):
            try:
                # Create a virtual module and import the file with its dict
                mod = ModuleType(str(f))
                execfile(os.path.join(self.config.get("filters", "path",
                         vars={"directory":dir}), "%s.py" % f), {},
                         mod.__dict__)
            except Exception, err:
                self.logger.error("Import : %s %s => %s" % (dir(err), f, err))
            else:
                self.modules.append( (f, mod) )
                self.logger.info("Import : %s success" % f)
        self.fields_separator = ";;"
        self.init_file = init_file
        if os.path.exists(init_file):
            self.init()
        self.clean_captchas()

        
    def _add_to_file(self, filename, line, join=False):
        varname = make_varname(filename)
        if hasattr(self, varname):
            setattr(self, varname, getattr(self, varname) +
            [self.fields_separator.join(line),])
        with copen(filename, "a", "utf-8") as f:
            f.write((self.fields_separator.join(line) if join else line) + "\n")

    def _filter(self, name, *args):
        datas = args
        self.logger.debug("== %s - %s" % (self._get_filters(name), name))
        for m, f in self._get_filters(name):
            try:
                old_datas = copy(datas)
                datas = f(self, *datas)
                self.logger.debug("\ndatas : #%s#\n old : #%s#" % (datas[:20],
                    old_datas[:20]))
                got_type = [type(d) for d in datas] if isinstance(datas, (list,
                    set, tuple)) else type(datas)
                if not type_match(datas, self.filters_outputs[name]):
                    self.logger.error("Modules : %s from %s does not match the "
                                "prototype (needed %s, got %s)" % (f.__name__, m,
                                    self.filters_outputs[name], got_type))
                    datas = copy(old_datas)
            except Exception, err:
                self.logger.error("Modules : error in %s from module %s : %s" % 
                        (f.__name__, m, err))
            else:
                self.logger.debug("Modules : %s => %s" % (m, f.__name__))
        return datas

    def _get_all_comments(self, get_content=False):
        """ Returns a tuple with all comments mixed, without by-post sorting """
        return [self._make_comment(p, None if get_content else "") for p in
                self._read_file(self.comments_index, True, True)]

    def _get_all_posts(self, get_content=False):
        """ Returns a tuple with every post from the post index """
        return [self._make_post(p, (None if get_content else "")) for p in
                self._read_file(self.posts_index, True, save=True)]

    def _get_post_content(self, post_id):
        try:
            with copen(self._path_to_post(post_id), "r", "utf-8") as f:
                post = f.read()
            return post
        except IOError:
            return None

    def _get_comment_content(self, comm_id):
        try:
            with copen(self._path_to_comment(comm_id), "r", "utf-8") as f:
                comm = f.read()
            return comm
        except IOError:
            return None

    def _get_filters(self, function):
        """
        Returns a tuple with the function found in the modules
        """
        return [(m.__name__, getattr(m, function)) for n, m in
                self.modules if function in dir(m)]

    def _total_pages(self):
        lines = self._read_file(self.posts_index, save=True)
        # divisionbyzero is for douches
        return int(ceil(len(lines) / self.config.get_blog("posts_per_page", 10.,
            "float")))

    def _total_tags(self):
        tags = [Post(p, self.fields_separator)["tags"] for p in
                self._read_file(self.posts_index, save=True)]
        set_t = []
        [set_t.extend(t) for t in tags]
        return sorted(list(set(set_t)))

    def _total_users(self):
        """ Returns a tuple with all users : (name, pass_hash, power) """
        return self._read_file(self.users_index, True, save=True)

    def _make_post(self, line, content=None):
        """
        If line is a iterable, convert it into a Post, else get only the
        content.
        """
        post = Post(line, self.fields_separator) if isinstance(line,
                (tuple, list, set)) else line
        post["content"] = (content if content is not None else
            self._get_post_content(post["id"]))
        return post

    def _make_comment(self, line, content=None):
        commz = Comment(line, self.fields_separator) if isinstance(line,
                (tuple, list, set)) else line
        commz["content"] = (content if content is not None else
            self._get_comment_content(commz["id"]))
        return commz

    def _path_to_post(self, id):
        return os.path.join(self.posts_directory, str(id))

    def _path_to_comment(self, id):
        return os.path.join(self.comments_directory, str(id))

    def _read_file(self, filename, split=True, save=False):
        """
        If save is set, read content from an existing list, or read content
        from the file and write it in a list.
        """
        varname = make_varname(filename) if save else ""
        # If save, create a new variable with a dict of lines
        if varname and hasattr(self, varname):
            lines = getattr(self, varname)
        else:
            with copen(filename, "r", "utf-8") as f:
                lines = [l.rstrip("\n") for l in f.readlines()]
            if varname:
                setattr(self, varname, lines)
        return ([l.split(self.fields_separator) for l in lines] if split
                else lines)

    def _write_file(self, filename, lines, join=False):
        varname = make_varname(filename)
        lines = lines.split("\n") if is_str(lines) else lines
        joined = [self.fields_separator.join(l) for l in lines if isinstance(l,
                (list, tuple, set))]
        if hasattr(self, varname):
            setattr(self, varname, joined)
        with copen(filename, "w", "utf-8") as f:
            f.writelines("%s\n" % l for l in (joined if join else lines))

    def add_comment(self, comment):
        """
        Add the `comment' instance to the comments
        """
        prev_commz = self._get_all_comments()
        new_id = (prev_commz[-1]["id"] + 1 if prev_commz else
                  self.config.get_blog("posts_counter_start", 0, "int"))
        comment["id"] = new_id
        self._add_to_file(self.comments_index,
                comment.join(self.fields_separator), join=False)
        self._write_file(self._path_to_comment(comment["id"]),
                comment["content"])
        return new_id

    def add_post(self, post):
        """
        Add a new post. 'post' is a Post instance
        """
        previous_posts = self._read_file(self.posts_index, save=True)
        id = (int(previous_posts[-1][0]) + 1 if previous_posts else
                self.config.get_blog("posts_counter_start", 0, "int"))
        post["id"] = id
        self._add_to_file(self.posts_index, post.join(self.fields_separator),
                join=False)
        self._write_file(self._path_to_post(post["id"]), post["content"])
        self.update_feed()
        return id

    def add_user(self, user, password, power=VOICE):
        """
        Add a new user. 'password' is the plain password
        returns the user name
        """
        if user in zip(*self._total_users())[0]:
            return None
        t = (user, hash_user(user, password), str(power))
        self._add_to_file(self.users_index, t, True)
        return t[1]

    def clean_captchas(self, path=None):
        """
        if path exists, remove this captcha too
        """
        if not os.path.exists(self.captchas_index):
            self.init()
        lines = self._read_file(self.captchas_index, split=True, save=True)
        new_lines = []
        for l in lines:
            if float(l[0]) > time() and l[2] != path:
                new_lines.append(l)
            else:
                try:
                    os.remove(l[2])
                except OSError:
                    self.logger.error("Unable to remove %s." % l[2])
        self._write_file(self.captchas_index, new_lines, join=True)

    def create_captcha(self):
        expire = time() + 2 * 3600
        path, code = generate_captcha(directory=self.captchas_directory,
                lines=10, mode="mixed")
        os.chmod(path, 0644)
        self._add_to_file(self.captchas_index, (unicode(expire), code, path),
                join=True)
        return path, code

    def del_comment(self, comment_id=None, post_id=None):
        """
        if comment_id is specified, delete this one, else delete the comments
        from the post_id
        """
        commz = self._get_all_comments()
        new_commz = []
        for c in commz:
            if (comment_id is not None and comment_id == c["id"]) or (post_id is
                    not None and post_id == c["post_id"]):
                path = self._path_to_comment(c["id"])
                try:
                    os.remove(path)
                except OSError:
                    self.logger.error("Unable to delete %s" % path)
            else:
                new_commz.append(c.join(self.fields_separator))
        self._write_file(new_commz, join=False)

    def del_post(self, post_id):
        """
        Delete the post #post_id.
        """
        posts = self._get_all_posts()
        post_id = int(post_id)
        posts = [p.join(self.fields_separator) for p in posts if
                 p["id"] != post_id]
        self._write_file(self.posts_index, posts)
        self.del_comment(post_id=post_id)
        path = self._path_to_post(post_id)
        try:
            os.remove(path)
            self.update_feed()
            return 0
        except OSError:
            self.logger.error("Unable to remove %s." % path)
            return 1

    def del_user(self, user):
        """
        Delete a user
        """
        self._write_file(self.users_index, [u for u in self._total_users() if
            u[0] != user], True)

    def edit_post(self, post):
        """
        Replace the content of the post #post_id with the content of the 'post',
        which is a Post instance.
        """
        self._write_file(self.posts_index, [p.join(self.fields_separator) if
            p["id"] != post["id"] else post.join(self.fields_separator) for p in
            self._get_all_posts()])
        self._write_file(self._path_to_post(post["id"]), post["content"])
        self.update_feed()

    def format_comment(self, comment):
        """
        Reads the configutation and returns html code
        """
        comm_id = str(comment["id"])
        comm_infos = expand(self.config.get("comment", "infos_format"),
                ((r"\[id\]", t.A(self.rewrite(post=str(comment["post"]),
                    comment=comm_id), comm_id, name="comment_%s" %
                    comm_id)),
                 (r"\[title\]", comment["title"]),
                 (r"\[author\]", comment["author"]),
                 (r"\[date\]", frogify(float(comment["date"]), True))
                 ))
        infos = t.Div(**{"id":"", "class": "comment_infos",
            "content": comm_infos})
        content = t.Div(**{"id":"", "class": "comment_content",
            "content": comment["content"]})
        return unicode(t.Div(**{"id":"", "class": "comment", "content": infos +
            content}))

    def format_div(self, option, div_id, page=None, tags=None):
        """
        Returns a div with expanded options.
        """
        
        numbers = "".join(unicode(t.A(self.rewrite(page=n), str(n),
            **{"class": "link_page" if n != page else "link_page_selected"}))
            for n in range(self._total_pages()))
        tags = ", ".join(unicode(t.A(self.rewrite(tag=t), t)) for t in
                self._total_tags())
        home = self.config.get_blog("home", "")
        name = self.config.get_blog("name", "")
        feeds = self.get_all_feeds()
        content = expand(option,
           ((r"\[title\]", t.H(1, unicode(t.A(home, name)))),
            (r"\[home\]", home),
            (r"\[numbers\]", numbers),
            (r"\[tags\]", tags),
            (r"\[search\]", unicode(t.Form(self.config.get_blog(
                "home", "")+argv[0], t.Label("search", _("Search : ")) +
                                     t.Input("text", name="search")))),
            (r"\[feed\]", " ".join(unicode(t.A(l, v)) for v,
                l in feeds))
           ))
        return unicode(t.Div(div_id, content))

    def format_post(self, post, short=True):
        """
        Reads the configuratin and returns html code.
        """
        comments = self.get_comments_by_post_id(post["id"], False)
        n_comments = len(comments)
        if n_comments:
            first_comment = self.rewrite(post=post["id"],
                    comment=comments[0]["id"])
        self_link = self.rewrite(post=str(post["id"]))
        # Replace the elements in the configurationn with expand
        post_infos = expand(self.config.get("post", "infos_format"),
            ((r"\[id\]", unicode(t.A(self_link, str(post["id"])))),
             (r"\[title\]", unicode(t.A(self_link, post["title"]))),
             (r"\[author\]", unicode(t.A(self.rewrite(author=post["author"]),
                 post["author"]))),
             # TODO A filter for the date
             (r"\[date\]", frogify(float(post["date"]), True)),
             (r"\[comments\]",  _("No comments") if not n_comments else
                 unicode(t.A(first_comment, _("Only one comment") if
                 n_comments == 1 else _("%d comments") % n_comments))),
             (r"\[tags\]", ", ".join(unicode(t.A(self.rewrite(tag=t), t))
                 for t in post["tags"])),
             ))
        post_content = post["content"]
        self._filter("print_post", post_content)
        short, post_content = (shortify(post_content) if short else (False,
                post_content))
        if short:
            post_content = post_content + t.A(self_link, _("Read more..."))
        infos = t.Div(**{"id": "", "class": "post_infos",
            "content": post_infos})
        content = unicode(t.Div(**{"id": "", "class": "post_content",
            "content": post_content}))
        fpost = expand(self.config.get("post", "format"), ((r"\[infos\]",
            unicode(infos)), (r"\[content\]", content)))
        return unicode(t.Div(**{"id":"", "class":"post", "content": fpost}))

    def get_all_feeds(self):
        """
        Returns a tuple with tuples containing the name of the feed and its path
        """
        return [(f, self.config.get("feed", "%s_path" % f)) for f in ("atom",
            "rss") if self.config.getboolean("feed", f)]

    def get_captcha_code(self, path, delete=True):
        """
        Returns the code of the captcha
        If delete is True, also clean the requested captcha
        """
        lines = self._read_file(self.captchas_index, save=True)
        lines = [l for l in lines if l[2] == path]
        if delete:
            self.clean_captchas(path)
        return lines[0][1] if lines else None

    def get_comments_by_post_id(self, post_id, get_content=True):
        """ Returns  the comments which belong to the post `post_id' """
        return [self._make_comment(c, None if get_content else "") for c in
                self._get_all_comments() if self._make_comment(c,
                "")["post"] == post_id]

    def get_comment_by_id(self, comm_id):
        """
        Returns the comment which has the id `comm_id'
        if it doesn't exist, return None
        """
        c = [self._make_comment(c) for c in self._get_all_comments() if
                self._make_comment(c, "")["id"] == comm_id]
        return c[0] if c else None

    def get_posts(self, post_id=None, prange=None, tag=None, author=None):
        """
        If argument is range, tag or author, returns a list with posts instance
        Else, if argument is post_id, return an unique post
         post_id is an int
         prange is a tuple (start, end) e.g. (-10, None)
         tag and author are strings
        if no argument is specified, returns all posts, but it may never be
        used
        """
        posts = self._get_all_posts()
        if post_id is not None:
            posts = [self._make_post(p) for p in posts if p["id"] == post_id]
            return posts[0] if posts else None
        elif prange is not None:
            start, end = prange
            return [self._make_post(p) for p in (posts[start:end][::-1 if
                start > end else 1])]
        elif tag is not None:
            return [self._make_post(p) for p in posts if tag in p["tags"]]
        elif author is not None:
            return [self._make_post(p) for p in posts if p["author"] == author]
        else:
            return [self._make_post(p) for p in posts]

    def has_power(self, user, power):
        """
        Returns true if userhas more or equal power than 'power'.
        As instance, has_power("foo", OP) returns true if 'foo' is OP or 
        ROOT.
        """
        lines = self._read_file(self.users_index, save=True)
        users = [l for l in lines if l[0] == user]
        return True if users and int(users[0][2]) <= power else False

    def init(self):
        """
        Internal, make the dirs and touch the files
        """
        pexists = os.path.exists
        pjoin = os.path.join
        #if not pexists(".htaccess"):
        #    with copen(".htaccess", "w") as f:
        #        f.write("DirectoryIndex %s" % argv[0])
        for dir in [d for o, d in self.config.items("blog") if
                o.endswith("directory")]:
            if not pexists(dir):
                os.makedirs(dir, mode=(0770 if not "captcha" in dir else 0771))
                with copen(pjoin(dir, ".htaccess"), "w") as f:
                    f.write("Order Deny, Allow\nDeny from All")

        for index in [getattr(self, a) for a in self.__dict__ if
                a.endswith("_index")]:
            if not pexists(index):
                with copen(index, "w"): pass
                os.chmod(index, 0640)
        if pexists(self.init_file):
            with copen(self.init_file) as f:
                lines = f.readlines()
            try:
                result = [self.add_user(*l.strip("\n").split(":")) for l in
                          lines]
            except TypeError:
                pass
            if result:
                with copen("%s.log" % self.init_file, "w") as f:
                    f.writelines(result)
                os.remove(self.init_file)

    def is_user(self, user="", password="", hash=""):
        """
        Returns a tuple with the user name and the power if the user and the
        password or the hash match the users database.
        Else, return (None, None).
        """
        lines = self._read_file(self.users_index, save=True)
        new_hash = hash_user(user, password)
        user = [l for l in lines if l[1] == hash or l[1] == new_hash]
        return (user[0][0], user[0][1]) if user else (None, None)

    def print_page(self, page=None, post=None, author=None, tag=None,
            search=None):
        """
        Prints the page number 'num', with the header and the footer.
        """
        # I'll just leave this here
        # http://fukung.net/v/13898/08a83f807114369410af2259d729f49e.jpg
        content = []
        append = content.append
        header = self.format_div(self.config.get("header", "format"), "header",
                page=page)
        
        if page is not None:
            ppp = self.config.get_blog("posts_per_page", 10, "int")
            start_page = self.config.get_blog("pages_counter_start", 0, "int")
            start = -ppp * (page - start_page + 1)
            end = start + ppp if start < -ppp else None
            # posts[-20:-10] for instance, or posts[-10:]
            posts = self.get_posts(prange=(start, end))
            append(unicode(t.BR()).join(self.format_post(post) for post
                in posts))
        elif post is not None:
            p = self.get_posts(post_id=post)
            append(self.format_post(p, False))
            append(t.Div("comments",
                unicode(t.BR()).join(self.format_comment(c)
                for c in self.get_comments_by_post_id(post))))
            path, code = self.create_captcha()
            form_content = (
                    _("Leave a comment : ") + t.BR(),
                    t.Label("author", _("Author : ")),
                    t.Input("text", name="author") + t.BR(),
                    t.Label("title", _("Title : ")),
                    t.Input("text", name="title") + t.BR(),
                    t.Label("content", _("Content : ")) + t.BR(),
                    t.Textarea(5, 80, content="", name="content") + t.BR(),
                    t.Label("captcha_content", _("Please copy this captcha : ")),
                    t.BR() + t.Img(path, "It's a captcha") + t.BR(), 
                    t.Input("text", name="captcha_content") + t.BR(),
                    t.Input("submit", value=_("Send")),
                    t.Input("hidden", name="post", value=str(post)),
                    t.Input("hidden", name="mode", value="add"),
                    t.Input("hidden", name="captcha_path", value=path)
            )
            append(t.Form(self.config.get_blog("home", "") +
                "comments.py", u"\n".join(unicode(l) for l in form_content),
                method="POST", id="leave_message"))

        elif author is not None:
            append(unicode(t.BR()).join(self.format_post(post) for post in
                    self.get_posts(author=author)[::-1]))

        elif search is not None:
            results = self.search(search)
            if results:
                append(unicode(t.BR()).join(self.format_post(post) for post in
                        results[::-1]))
            else:
                append(t.P("Nothing found."))
        elif tag is not None:
            append(unicode(t.BR()).join(self.format_post(post) for post in
                    self.get_posts(tag=tag)[::-1]))
        else:
            append(t.H(2, "ERROR, FAIL, PWND."))

        footer = self.format_div(self.config.get("footer", "format"), "footer",
                page=page)
        
        return unicode(t.Div("container", header + t.Div("content",
            "\n".join(unicode(l) for l in content) + footer)))

    def print_feed(self, format="atom"):
        """
        Prints the rss feed in atom or rss 2.0
        """
        # TODO an AtomFeed/RSSFeed class
        def format_date(date):
            return (rfc3339(date) if format == "atom" else
                    date.strftime("%a, %d %b %Y %H:%M:%S -0200"))
        def format_post(post):
            author = post["author"]
            title = post["title"]
            link = self.rewrite(post=post["id"])
            post_id = post["id"]
            date = format_date(datetime.fromtimestamp(post["date"]))
            content = post["content"]
            return (u"\n".join(("<entry>",
                u"    <author>",
                u"        <name>%(author)s</name>",
                u"    </author>",
                u"    <title>%(title)s</title>",
                u"    <link href=\"%(link)s\" />",
                u"    <id>%(link)s</id>",
                u"    <updated>%(date)s</updated>",
                u"    <content type=\"xhtml\">",
                u"    <div xmlns=\"http://www.w3.org/1999/xhtml\">",
                u"        %(content)s",
                u"    </div></content>",
                u"</entry>") if format == "atom" else ("<item>",
                u"    <title>%(title)s</title>",
                u"    <link>%(link)s</link>",
                u"    <guid>%(link)s</guid>",
                u"    <pubDate>%(date)s</pubDate>",
                u"    <!--<description>%(content)s</description>-->",
                u"</item>"))) % locals()
        title = self.config.get_blog("name", "")
        subtitle = self.config.get("feed", "subtitle")
        self_link = "%s/%s" % (self.config.get_blog("home"),
                self.config.get("feed", "atom_path" if format == "atom" else
                                "rss_path"))
        link = "%s/%s" % (self.config.get_blog("home"),
                argv[0])
        feed_id = self.config.get_blog("home", "none")
        date = format_date(datetime.today())
        author = self.config.get_blog("author")
        email = self.config.get_blog("email")
        posts = [format_post(post) for post in
                self.get_posts(prange=(-self.config.getint("feed",
                "feed_number"), None))]
        entries = "\n".join(posts)

        feed = u"\n".join((u"<?xml version=\"1.0\" encoding=\"utf-8\"?>",
            u"<feed xmlns=\"http://www.w3.org/2005/Atom\">",
            u"    <title>%(title)s</title>",
            u"    <subtitle>%(subtitle)s</subtitle>",
            u"    <link href=\"%(self_link)s\" rel=\"self\" />",
            u"    <link href=\"%(link)s\" />",
            u"    <id>%(feed_id)s</id>",
            u"    <updated>%(date)s</updated>",
            u"    <author>",
            u"        <name>%(author)s</name>",
            u"        <email>%(email)s</email>",
            u"    </author>",
            u"    %(entries)s",
            u"</feed>") if format == "atom" else 
           (u"<?xml version=\"1.0\" encoding=\"utf-8\"?>",
            u"<rss version=\"2.0\">",
            u"    <channel>",
            u"        <title>%(title)s</title>",
            u"        <description>%(subtitle)s</description>",
            u"        <lastBuildDate>%(date)s</lastBuildDate>",
            u"        <link>%(link)s</link>",
            u"        %(entries)s",
            u"    </channel>",
            u"</rss>")) % locals()
        return feed

    def rewrite(self, page=None, tag=None, post=None, author=None,
            comment=None):
        """
        Check if url_rewriting is enabled and write the good link
        """
        urlrew = self.config.getboolean("url_rewriting", "enabled")
        get = lambda i, p, r: self.config.get("url_rewriting", i).replace(p, r)
        link = ""
        exists = lambda v: v is not None
        suffix = ("#comment_%s" % comment) if exists(comment) else ""
        name = self.config.get_blog("home")
        if exists(page):
            link = (get("page", "[num]", str(page)) if urlrew else "%s?page=%d"
                    % (name, page))
        elif exists(tag):
            tag = quote_plus(tag)
            link = (get("tag", "[tag]", tag) if urlrew else "%s?tag=%s"
                    % (name, tag))
        elif exists(post):
            link = (get("post", "[num]", str(post)) + suffix if urlrew else
                    "%s?post=%d%s" % (name, post, suffix))
        elif exists(author):
            author = quote_plus(author)
            link = (get("author", "[author]", author) if urlrew
                    else "%s?author=%d" % (name, author))
        return self.config.get_blog("home", "") + link

    def search(self, pattern):
        """
        Search the pattern 'pattern' in the content of the posts.
        """
        # XXX Totally safe ?
        cmd = "grep --exclude=index -r \"%s\" %s" % \
               (pattern.replace("\\", "").replace('"', r'\"'),
                self.posts_directory)
        self.logger.debug(cmd)
        stdout = os.popen(cmd, "r")
        result = stdout.read()
        debug(result)
        posts = []
        for line in result.split("\n"):
            if line:
                id = int(os.path.basename(line.split(":")[0]))
                posts.append(id)
        return [self.get_posts(post_id=p) for p in sorted(set(posts))]

    def set_user(self, user, password=None, power=None):
        """
        Set the password and/or the permissions for a user
        """
        self._write_file(self.users_index, [(user, (hash_user(user, password)
            if password else h), (power if power is not None else p)) if
            user == u else (u, h, p) for (u, h, p) in self._total_users()],
            True)

    def update_feed(self):
        for f, p in self.get_all_feeds():
            self.logger.info("Updating %s" % f)
            self._write_file(p, self.print_feed(f))

def is_str(elem):
    return True if isinstance(elem, (str, unicode)) else False

def expand(string, replacements):
    r"""
    This function applies the replace rules given in 'replacements' to 'string'
    replacements is a 2d tuple : ((r"foo", "bar"), (r"(.+)bar", r"\1baz")).
    """
    def expand_pos(m):
        """
        function to pass as argument in a sub function, to handle teh
        position syntax : $c:foo$.
        """
        p = m.group(1)
        pos = "center" if p == "c" else ("right" if p == "r" else "left")
        return m.expand(r"<div class='item position_%s'>\2</div>" % pos)
    string = sub(r"{([clr]):(.+?)}", expand_pos, string)
    for p, r in replacements:
        string = sub(p, r, string)
    return string

def get_value(field_storage, value, default=""):
    return unicode(field_storage.getfirst(value, default), "utf-8")

def hash_user(user, password):
    """
    Hash the user and the password using the sha224 algoritm.
    """
    from hashlib import sha224
    return sha224(user + password).hexdigest()

def frogify(date, print_hour=False):
    """
    Returns a string with the french date format of the float `date'
    """
    jours = (u"Lundi", u"Mardi", u"Mercredi", u"Jeudi", u"Vendredi", u"Samedi",
             u"Dimanche")
    mois = (u"Janvier", u"Février", u"Mars", u"Avril", u"Mai", u"Juin",
            u"Juillet", u"Août", u"Septembre", u"Octobre", u"Novembre",
            u"Décembre")
    date_t = datetime.fromtimestamp(date)
    hour = u" à %(h)dh%(m)02d" % {"h": date_t.hour, "m": date_t.minute,
            "s":date_t.second}
    return u"%(weekday)s %(day)s %(month)s %(year)s%(hour)s" % {
            "weekday": jours[date_t.weekday()],
            "day":     (lambda d: ("%s<sup>er</sup>" if d == 1 else "%s") %
                    d)(date_t.day),
            "month":   mois[date_t.month - 1],
            "year":    date_t.year,
            "hour":    hour if print_hour else ""
            }

def make_varname(text):
    return "genvar_" + str(hash(text)).replace("-", "_")

def shortify(text):
    """
    Returns (True, text) if text has been shortified, else (False, text)
    """
    pattern = r"\s*\<p([^>]*)\>(.*?)\<\/p\>"
    m = match(pattern, text.replace("\n", " "))
    if m:
        return (True, m.expand(r"<p\1>\2</p>"))
    else:
        return (False, text)

def type_match(var, required_type):
    match = True
    if isinstance(required_type, (list, set, dict)):
        for t, v in zip(required_type, var):
            if not isinstance(v, t):
                match = False
    else:
        match = isinstance(var, required_type)
    return match

#def _(text):
#    return text

def main():
    #import pycallgraph
    #pycallgraph.start_trace()
    start = time()
    blog = Blog()
    if "init" in argv:
        blog.init()
    elif "update" in argv:
        blog.update_feed()
        return
    home = blog.config.get("blog", "home")
    field_storage = FieldStorage()
    POST = {
        "post": get_value(field_storage, "post", ""),
        "page": get_value(field_storage, "page", ""),
        "tag": get_value(field_storage, "tag", ""),
        "author": get_value(field_storage, "author", ""),
        "search": get_value(field_storage, "search", ""),
        "mode": get_value(field_storage, "mode", "")
        }
    headers = ["Content-type: text/html",]

    args = {"http-equiv": "Content-Type", "content": "text/html;charset=utf-8"}
    struct = XHTMLStructure("PycoBlog")
    struct.head.add_meta(**args)
    for f, l in blog.get_all_feeds():
        struct.head.add_feed(l, "application/%s+xml" % f,"%s Feed" % f.upper())
    struct.head.add_style(link=home+"/style.css")
    struct.head.add_style(link=home+"/hilight.css")

    print "\n".join(headers) + "\n"
    #print field_storage, post
    args = {}
    if POST["page"] and POST["page"].isdigit():
        args["page"] = int(POST["page"])
    elif POST["post"] and POST["post"].isdigit():
        args["post"] = int(POST["post"])
    elif POST["search"]:
        args["search"] = POST["search"]
    elif POST["author"]:
        args["author"] = POST["author"]
    elif POST["tag"]:
        args["tag"] = POST["tag"]
    elif POST["mode"] == "edit":
        edit = POST["post"]
    else:
        args["page"] = blog.config.get_blog("pages_counter_start", 0, "int")
    if POST["mode"] == "edit":
        struct.content = t.Form(home + "/" + argv[0])
    elif POST["mode"] == "test_atom":
        struct = blog.print_feed("atom")
    else:
        struct.content = blog.print_page(**args)
    #if DEBUG_OPEN:
    #    print "<br/>".join("%s : %s => %s" % (n, f, m) for n, f, m in
    #            OPEN_COUNTER) + "<br/>==>" + str(len(OPEN_COUNTER))
    print struct #.encode("utf-8", "replace")
    #blog.logger.debug("Rendering time : %s" % (time() - start))
    #pycallgraph.make_dot_graph("graphs/%d.png" % long(time()))

if __name__ == "__main__":
    main()
