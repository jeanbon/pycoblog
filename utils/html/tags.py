#!/usr/bin/python
# -*- coding: utf-8 -*-

class Tag:
    """
    A simple tag
        newline if a new line has to be added after the tag (useless :)
        last_tag if the closing tag has to be written, even if ther is no content
    """
    def __init__(self, tagname="", inner="", newline=False, last_tag=False, **attr):
        #unicode.__init__(self, encoding, errors)
        self.tagname  = encode(tagname)
        self.inner    = encode(inner)
        self.newline  = newline
        self.last_tag = last_tag
        self.attr     = {}
        for k, v in attr.iteritems():
            self.attr[k] = encode(v)

    def __add__(self, val):
        return self.__repr__() + encode(val)
    
    def __radd__(self, val):
        return encode(val) + self.__repr__()

    def __iadd__(self, val):
        return self.__radd__(val)

    def __unicode__(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.__repr__())

    def __cmp__(self, val):
        return cmp(self.__repr__(), val)

    def __hash__(self):
        return hash(self.__repr__())

    def __getslice__(self, i, j):
        return self.__repr__().__getslice__(i, j)

    def __getitem__(self, i):
        return self.__repr__().__getitem__(i)

    #def __new__(cls, tagname="", *args, **kwargs):
    #    encoding = kwargs["encoding"] if "encoding" in kwargs else "utf-8"
    #    errors   = kwargs["errors"]   if "errors"   in kwargs else "replace"
    #    if isinstance(tagname, Tag):
    #        return unicode.__new__(cls, tagname.__repr__())
    #    else:
    #        return unicode.__new__(cls, tagname, encoding, errors)

class XHTMLTag(Tag):
    def __init__(self, tagname, inner="", newline=False, last_tag=False, **attr):
        Tag.__init__(self, tagname, inner, newline,
                last_tag, **attr)

    def __repr__(self):
        if self.inner or self.last_tag:
            return u"<%(name)s%(attr)s>%(val)s</%(name)s>%(newline)s" % {
                    "name":self.tagname,
                    "attr":(" "+" ".join(u"%s=\"%s\"" % (key,
                        self.attr[key].strip('"')) for key in self.attr if
                        self.attr[key]) if self.attr else ""),
                    "val":self.inner,
                    "newline": "\n" if self.newline else ""
                    }
        else:
            return u"<%(name)s%(attr)s />%(newline)s" % {
                    "name":self.tagname,
                    "attr":" "+" ".join(u"%s=\"%s\"" % (key,
                        self.attr[key].strip('"')) for key in self.attr if
                        self.attr[key]) if self.attr else "",
                    "newline": "\n" if self.newline else ""
                    }

    def add_attr(self, attr, value=""):
        self.attr[attr] = encode(value)
    
    def del_attr(self, attr):
        if self.attr.has_key(attr):
            del self.attr[attr]

class XHTMLComment(Tag):
    def __init__(self, content, newline=True):
        self.content = encode(content)
        self.newline = newline

    def __repr__(self):
        return "<!-- %s -->%s" % (self.content, "\n" if self.newline else "")

def encode(var):
    if isinstance(var, (unicode, Tag)):
        return var
    else:
        return unicode(var, "utf-8")

