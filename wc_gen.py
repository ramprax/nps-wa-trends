from os import path
import sys
from operator import itemgetter
from wordcloud import *

def mydraw(elements, filedesc, format='PNG', font_path=None, width=400, height=200, scale=1,
    color_func=random_color_func):
    if font_path is None:
        font_path = FONT_PATH
    img = Image.new("RGB", (width * scale, height * scale))
    draw = ImageDraw.Draw(img)
    for (word, count), font_size, position, orientation in elements:
        font = ImageFont.truetype(font_path, font_size * scale)
        transposed_font = ImageFont.TransposedFont(font,
        orientation=orientation)
        draw.setfont(transposed_font)
        color = color_func(word, font_size, position, orientation)
        pos = (position[1] * scale, position[0] * scale)
        draw.text(pos, word, fill=color)
    img.save(filedesc, format=format)

def make_word_cloud_image_from_text(text, output, format='PNG', font_file_name = 'Ubuntu-R.ttf'):

    # Separate into a list of (word, frequency).
    word_freq_list = process_text(text)

    make_word_cloud_image_from_word_freqs(word_freq_list, output, format, font_file_name)


def make_word_cloud_image_from_word_freqs(word_freq_list, output, format='PNG', font_file_name = 'Ubuntu-R.ttf'):
    d = path.dirname(__file__)
    ub_font_path = path.join(d, font_file_name)#'TSCu_Comic.ttf')#'Ubuntu-R.ttf')
    # Compute the position of the words.
    elements = fit_words(word_freq_list, font_path = ub_font_path, width=500, height=500)

    # Draw the positioned words to a PNG file.
    mydraw(elements, output, format=format, font_path = ub_font_path, width=500, height=500, scale=2)

def normalize_and_sort_word_freq_list(word_freq_list):
    item1 = itemgetter(1)
    word_freq_list = sorted(word_freq_list, key=item1, reverse=True)
    maximum = float(max( (wf[1] for wf in word_freq_list)  ))
    for i, (word, count) in enumerate(word_freq_list):
        word_freq_list[i] = word, count/maximum
    return word_freq_list
 

if __name__=='__main__':
    text = open(sys.argv[1]).read()
    outfile = sys.argv[2]
    make_word_cloud_image_from_text(text, outfile)
    
