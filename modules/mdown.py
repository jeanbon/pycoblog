#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement

def print_post(blog, text):
    #debug = blog.logger.debug
    def unescape(text):
        chars = {"&quot;": "\""}
        for c, r in chars.iteritems():
            text = text.replace(c, r)
        return text
    from BeautifulSoup import BeautifulSoup as bf
    from re import findall
    from os import popen3
    if findall(r"% [^\n]*mdown", text):
        # Le texte devra contenir une ligne avec une instruction au format mdown
        # contenant ce nom.
        # On utilise un format spécial pour préciser le langage de code qui suivra.
        # ceci signifie que chaque code devra être précédé de cette description,
        # sinon, ça mettrait le chaos dans les balises. Et on ne veut pas ça.
        code_infos = findall(r"% \[code\] lang *[:=] *(\w+) *", text)
        f_in, f_out, f_err = popen3("mdown -f xhtml -B tdql -b xml")
        f_in.write(text.encode("utf-8", "ignore"))
        f_in.close()
        out, err = f_out.read(), f_err.read()
        f_out.close()
        f_err.close()
        if err:
            blog.logger.warning(u"Mdown : %s" % err)
        soup = bf(unescape(out))
        for elem, lang in zip(soup.findAll("code"), code_infos):
            elem.parent.replaceWith(elem)
            elem["lang"] = lang
        return unicode(soup.prettify(), "utf-8")
    else:
        return text

