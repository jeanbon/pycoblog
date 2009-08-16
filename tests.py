#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Utils for testing the blog, and developping modules easily """
import blog
import os
from time import time

SAMPLE_POST = """<p>Hello world !
This is my first post on this blog</p>
<p>I will talk about coding stuff and my wonderful life</p>
<code lang="python"><pre>#!/usr/bin/python
# -*- coding: utf-8 -*-

import blog
blog.add_post(blog.Post(title="Hello !", content="foo"))
</pre></code>
And that's it. :)
"""

SAMPLE_COMMENT = """Hi,
I totally love this post. You're my master. Thanks a lot.
"""

SAMPLE_DATE = 1249920708.91

class BlogTester(object):
    def __init__(self, tests_sample_dir="tests/", config_file="config"):
        self.blog = blog.Blog(config_file)
        if not os.path.exists(tests_sample_dir):
            os.makedirs(tests_sample_dir)
        join = lambda p: os.path.join(tests_sample_dir, p)
        self.samples = (
                ("post", join("article"), SAMPLE_POST),
                ("comment", join("comment"), SAMPLE_COMMENT),
                ("date", join("date"), SAMPLE_DATE))
    
    def get_file_content(self, name):
        path, sample = [p, s for n, p, s in self.samples if n == name][0]
        if os.path.exists(path):
            with open(path, "r") as fd:
                content = fd.read()
            return content
        else:
            return sample
            
    def test_print_post():
        """ returns a short post and a long """
        args = {}
        args["date"] = time()
        args["tags"] = u"tag 1, tag2, tâg3, tag-4"
        args["title"] = u"Sample post"
        args["author"] = u"writer"
        args["content"] = self.get_file_content("post")
        post = blog.Post(**args)
        return [self.blog.format_post(post, a) for a in (True, False)]

    def test_print_page():
        """
        returns a tuple with a page containing a header, a footer and a
        post
        """
        pass

    def test_date():
        """
        Returns a formatted date
        """
        return self.blog.filter_date(self.get_file_content("date"))
