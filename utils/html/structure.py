#!/usr/bin/python
# -*- coding: utf-8 -*-

from tags import XHTMLTag
from xhtmltags import MetaTag, P

class XHTMLHead:
    def __init__(self, title=""):
        self.doctype = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
        self.title = XHTMLTag("title", title)
        self.meta_tags = []
        self.tags = []

    def __repr__(self):
        return XHTMLTag("head", inner="\n"+"\n".join((
              "    %s" % self.title,
              "\n".join("    %s" % tag for tag in self.meta_tags),
              "\n".join("    %s" % tag for tag in self.tags)
              ))+"\n").__repr__()

    def __str__(self):
        return self.__repr__()

    def __unicode(self):
        return self.__repr__()

    def add_meta(self, **attr):
        self.meta_tags.append(MetaTag(**attr))
    
    def add_tag(self, tag_name, tag_value="", **tag_attr):
        self.tags.append(XHTMLTag(tag_name, tag_value, **tag_attr))

    def add_feed(self, href, type, description=""):
        """
        'type' can be "application/rss+xml" or "application/atom+xml"
        """
        self.tags.append(XHTMLTag("link", "", rel="alternate", href=href,
            type=type, title=description))

    def add_style(self, link="", style=""):
        """
        Use "link" to include a css file, or "style" to include css directly
        """
        if link:
            self.tags.append(XHTMLTag("link", "", rel="stylesheet",
                type="text/css", href=link))
        else:
            self.tags.append(XHTMLTag("style", style, type="text/css"))


class XHTMLBody(XHTMLTag):
    def __init__(self, content, **args):
        XHTMLTag.__init__(self, "body", "\n"+content, newline=True, **args)

class XHTMLStructure:
    def __init__(self, title="", content=""):
        self.doctype = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
        self.html_args = {
            "xmlns":    "http://www.w3.org/1999/xhtml",
            "xml:lang": "en",
            "lang":     "en"
            }
        self.body_args = {}
        self.head = XHTMLHead(title)
        self.content = content

    def __repr__(self):
        #u"%s" % str(self.head)
        content = u"%s\n%s" % (self.doctype, XHTMLTag("html", u"%s\n%s" %
                (self.head, XHTMLBody(self.content, **self.body_args)),
                 **self.html_args))
        return content.encode("utf-8")

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.__repr__()

def test():
    structure = XHTMLStructure("foo", P("Hello world"))
    args = {"http-equiv": "Content-Type", "content": "text/html;charset=utf-8"}
    structure.head.add_meta(**args)
    structure.head.add_tag("style", """
        body{
            text-align:center;
            padding-top:20%;
            color:#ABC;
            background-color:#123;
        }
        a{
            text-decoration:none;
            color:#EDC;
        }
        a:before, a:after{
            content:" ⋅ ";
        }
    """,
    type="text/css")
    print structure

if __name__ == "__main__":
    test()
