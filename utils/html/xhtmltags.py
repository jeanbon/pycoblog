#!/usr/bin/python
# -*- coding: utf-8 -*-

from tags import XHTMLTag
TAG = XHTMLTag

class A(TAG):
    def __init__(self, href="", content="", **attr):
        TAG.__init__(self, "a", inner=content, href=href, **attr)
        if href:
            self.add_attr("href", href)


class B(TAG):
    def __init__(self, content="", **attr):
        TAG.__init__(self, "b", inner=content, **attr)


class BR(TAG):
    def __init__(self):
        TAG.__init__(self, "br", newline=True)


class Div(TAG):
    def __init__(self, id="", content="", **attr):
        TAG.__init__(self, "div", inner="\n%s\n" % content, newline=True, id=id, **attr)


class Form(TAG):
    def __init__(self, action, content, method="GET", **attr):
        TAG.__init__(self, "form", inner="\n" + content, newline=True,
                action=action, method=method, **attr)


class H(TAG):
    def __init__(self, hierarchy, content="", **attr):
        """ 'hierarchy' must be an int between 1 and 6 """
        if not 1 <= hierarchy <= 6:
            raise IndexError("h1-h6 only")
        TAG.__init__(self, "h%d" % hierarchy, inner=content, newline=True,
                **attr)


class I(TAG):
    def __init__(self, content="", **attr):
        TAG.__init__(self, "i", inner=content, **attr)


class Input(TAG):
    def __init__(self, type, content="", value="", **attr):
        TAG.__init__(self, "input", inner=content, newline=True,
                type=type, value=value, **attr)

        
class Img(TAG):
    def __init__(self, src, alt="", **attr):
        TAG.__init__(self, "img", src=src, alt=alt, **attr)

        
class Label(TAG):
    def __init__(self, _for, content, **attr):
        attr["for"] = _for
        TAG.__init__(self, "label", inner=content, **attr)


class MetaTag(TAG):
    def __init__(self, **attr):
        TAG.__init__(self, "meta", **attr)


class Option(TAG):
    def __init__(self, content, **attr):
        TAG.__init__(self, "option", inner=content, **attr)


class P(TAG):
    def __init__(self, content="", **attr):
        TAG.__init__(self, "p", inner=content, newline=True, **attr)


class Pre(TAG):
    def __init__(self, content="", **attr):
        TAG.__init__(self, "pre", inner=content, newline=True, **attr)


class Select(TAG):
    def __init__(self, name, options, **attr):
        """ options is a list with Option instances"""
        TAG.__init__(self, "select", name=name,
                inner="\n" + "\n".join("    %s" % opt.tostr() for
                    opt in options) + "\n", newline=True, **attr)


class Span(TAG):
    def __init__(self, content="", **attr):
        TAG.__init__(self, "span", inner=content, **attr)


class Table(TAG):
    def __init__(self, lines, **attr):
        """ lines is a list of TR """
        TAG.__init__(self, "table", inner="\n".join("    %s" %
            tr.tostr() for tr in lines)+"\n", newline=True, **attr)


class TD(TAG):
    def __init__(self, content, **attr):
        TAG.__init__(self, "td", inner=content, newline=True, **attr)


class Textarea(TAG):
    def __init__(self, rows, cols, content, **attr):
        """ rows and cols are ints """
        TAG.__init__(self, "textarea", inner=content,
                newline=True, last_tag=True, rows=str(rows), cols=str(cols),
                **attr)


class TR(TAG):
    def __init__(self, cols, **attr):
        """ cols is a list of TD """
        TAG.__init__(self, "tr", inner="\n".join("        %s" %
            td.tostr() for td in cols)+"\n", newline=True, **attr)


class U(TAG):
    def __init__(self, content="", **attr):
        TAG.__init__(self, "u", inner=content, **attr)


