#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from PIL.Image import new as new_image, BILINEAR, BICUBIC

from PIL.ImageDraw import Draw
import PIL.ImageFont
from random import choice, randrange
from string import ascii_letters, digits, ascii_uppercase
import os.path

def generate_letter(char, font_size, font_name):
    img_dim = (font_size + font_size / 2,) * 2
    img = new_image("RGB", img_dim, (0, 0, 0))
    img_draw = Draw(img)
    #font = PIL.ImageFont.ImageFont()
    #font.font = PIL.ImageFont.truetype(font_name, font_size)
    #font.color = tuple( [randrange(126, 256) for i in range(3)] )
    font = PIL.ImageFont.truetype(font_name, font_size)
    color = tuple( [randrange(126, 256) for i in range(3)] )
    img_draw.text((0, 0), char, color, font)
    #img = img_draw.flush()
    img = img.rotate(randrange(-30, 30), BICUBIC)
    mask = new_image("L", img.size, 0)
    mask.paste(img, (0, 0))
    return img, mask

def generate_captcha(directory="tmp", letters=ascii_uppercase+digits,
        length=3, font_size=30, lines=5, mode="ellipse", font="FreeSerif.ttf"):
    """ Returns a tuple : (path, code) """
    dimensions = ((length + 1) * font_size, int(font_size * 2))
    path = "%s%s" % (os.path.join(directory, "".join(choice(ascii_letters) for
        i in xrange(7))), ".png")
    code = "".join(choice(letters) for i in range(length))
    background_color = tuple( [randrange(190, 230) for i in xrange(3)] )
    master = new_image("RGB", dimensions, background_color)

    # On colle les lettres
    for i, l in enumerate(code):
        img, mask = generate_letter(l, font_size, font)
        for _ in xrange(3):
            # On colle plusieurs fois pour plus de netteté
            master.paste(img, (font_size / 2 + font_size * i , font_size / 3),
                    mask)

    # Et on dessine quelques jolies lignes
    draw = Draw(master)
    for i in xrange(lines):
        color = tuple( [randrange(128, 190) for i in xrange(3)] )
        #pen = Pen("black", opacity=64)
        #pen.color = color
        w = dimensions[0]
        h = dimensions[1]
        geom = (randrange(0, int(w * 3. / 4)), randrange(0, h),
                randrange(int(w * 1. / 4), w), randrange(0, h))
        if mode == "mixed":
            mode_ = choice( ("ellipse", "line") )
        else:
            mode_ = mode
        if mode_ == "ellipse":
            draw.ellipse(geom, None, color)
        else:
            draw.line(geom, color, 1)
    with open(path, "w") as f:
        master.save(f)
    return (path, code)

def main():
    #path, code = generate_captcha(length=10000, font_size=60, lines=200, mode="mixed")
    path, code = generate_captcha(length=3, lines=10, mode="mixed")
    print path, code

if __name__ == "__main__":
    main()

