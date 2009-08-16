#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement

def print_post(blog, text):
    from pygments import highlight
    from pygments.lexers import guess_lexer, get_lexer_by_name
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    from BeautifulSoup import BeautifulSoup as bf
    def debug(text):
        import codecs
        with codecs.open("debug.log", "a", "utf-8") as f:
            f.write(str(text)+"\n")
    def unescape(text):
        return text.replace("&amp;", "&")
                    #replace("&lt;", "<").    \
                    #replace("&gt;", ">").    \
                    #replace("&quot;", "\""). \
                    #replace("'", "&#39;")

    debug = blog.logger.debug
    soup = bf(text)
    for elem in soup.findAll("code"):
        try:
            lang = elem["lang"]
        except KeyError:
            lang = "text"
        new_elem = elem.findChild("pre") if elem.findChild("pre") else elem
        level = 0
        #while not (isinstance(new_elem, unicode) or level > 3):
        #    level += 1
        #    new_elem = new_elem.next
        content = unicode(new_elem.renderContents(), "utf-8")
        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            try:
                lexer = guess_lexer(content.lstrip())
            except ClassNotFound:
                lexer = get_lexer_by_name("text")
        formatter = HtmlFormatter(linenos="inline")
        elem.next.extract()
        new_content = highlight(content, lexer, formatter)
        elem.replaceWith(unescape(new_content))
    return unicode(soup.prettify(), "utf-8")

