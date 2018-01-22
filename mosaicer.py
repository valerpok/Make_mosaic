"""
Application for creating image, that consists of small images (thumbnails) of porn actors.
You must set path to target image, also you can choose gender of actors, chunks size and thumbnails size.

Word 'chunk' means part of original image, that is replacing by thumbnail.
The best size ratio of chunk and thumbnail is 1:10, e.g. 6x8:60x80
"""

import os
import sys
import glob
import random as rn
from PIL import Image
from urllib.request import urlopen
from urllib.request import urlretrieve
from urllib.error import URLError
from bs4 import BeautifulSoup

path_to_image = '/home/someuser/some_image.jpg'  # Path to your image for transformation

gender = 'female'  # you can set 'male' or 'female'
pages = 10  # save 56 photos for every porhnub page. More is better, but slower

# Set False, if you run that script not for the first time and all photos are downloaded
# It will save your time from redownloading photos and creating thumbnails
download_photos = True

# Recommended 6 and 8
chunk_width = 6
chunk_height = 8

# Size of thumbnails, 60x80 is the best
thumb_width = 60
thumb_height = 80

# Set path
path = os.getcwd()
path_photos = path+'/just_for_science/'
path_thumbs = path_photos + 'thumbs/'

# For possible error 'connection reset by peer'
current_page = 0  

# --------------------------- FUNCTIONS ---------------------------


# Progress bar function, I borrowed it from StuckOverflow
def progress(count, total, status=''):

    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('\r')
    sys.stdout.write('[%s] %s%s ...%s' % (bar, percents, '%', status))
    sys.stdout.flush()


# Open pornhub and gather photos, save them to the folder 'just_for_science'
def save_photos(end_page):

    global current_page
    
    for j in range(current_page, end_page):

        for b in range(1):
            a = urlopen('https://www.pornhub.com/pornstars?gender='+gender+'&page='+str(j))
            soup = BeautifulSoup(a.read(), 'lxml')

            links = []
            for link in soup.findAll('img'):
                links.append(link)

            stars = []
            for i in links:
                if 'src' in i.attrs.keys():
                    src = i.attrs['src']
                    if 'pornstars' in src:  # Link to pornstar with image. Exactly, what we need
                        stars.append(src)

            for i in range(len(stars)):
                progress(i, len(stars), status='saving from page {}'.format(j))
                urlretrieve(stars[i], path_photos+str(j) + '_{}.jpg'.format(i))

        current_page += 1
        
    print('\nPhotos downloading complete!')


# Create thumbnail for saved pictures with some size, save them in 'just_for_science/thumbs'
def create_thumbs(width, height):

    size = [width, height]

    glb = glob.glob(path_photos+"*.jpg")
    a = iter(range(len(glb)))

    counter = 0

    for infile in glb:

        progress(counter, len(glb), status='creating thumbs')
        counter += 1

        im = Image.open(infile)
        im.thumbnail(size)
        im = im.resize(size)
        im.save(path_thumbs + str(next(a)) + ".thumbnail", "JPEG")

    print('\nThumbnails created!')


# Find the average color of given pixel array
def find_mean_RGB(pixels):

    reds = []
    greens = []
    blues = []

    for (r, g, b) in pixels:
        reds.append(r)
        greens.append(g)
        blues.append(b)

    r, g, b = map(lambda x: sum(x)//len(x), (reds, greens, blues))

    return r, g, b


# Create matrix of pixels
def get_matrix(im, xr, yr):
    pixels = []
    for x in range(xr, xr+chunk_width):
        for y in range(yr, yr+chunk_height):
            pixels.append(im.getpixel((x, y)))
    return pixels


# Paint chunk of image in one — average — color
def set_color(color, xstart, ystart):
    for x in range(xstart, xstart+chunk_width):
        for y in range(ystart, ystart+chunk_height):
            im.putpixel((x, y), color)


# Create dictionary with average colors as keys and photos as values
def create_palette():
    palette = {}
    glb = glob.glob(path_thumbs + "*.thumbnail")

    counter = 0

    for infile in glb:

        progress(counter, len(glb), status='creating palette')
        counter += 1

        im = Image.open(infile)
        color = []

        for x in range(thumb_width):
            for y in range(thumb_height):
                color.append(im.getpixel((x, y)))

        avr_color = find_mean_RGB(color)
        palette[avr_color] = infile

    print('\nPalette created. ')

    return palette


# Find four closest pictures by average RGB
def closest_pic(aver, color):

    pal = aver.keys()

    # Sort by mean difference between chunk color and color of palette's items
    close = sorted(pal, key=lambda x: (abs(color[0]-x[0]) +
                                       abs(color[1]-x[1] +
                                       abs(color[2]-x[2])))/3)

    return close[:4]  # Four images to decrease level of repeats


# Return new image, consisting of photos' thumbnails
def pure_art(data, aver):

    # Create new image
    nim = Image.new('RGB', (len(data[0])*thumb_width, len(data)*thumb_height), 'white')

    counter = 0  # for progress bar

    for row in range(len(data)):  # go through rows of chunks

        progress(counter, len(data), status='creating image')
        counter += 1

        tail = [0, 0, 0, 0]  # four last pasted images

        for i in range(len(data[row])):  # go through lines of chunks

            pics = closest_pic(aver, data[row][i])  # find four closest to chunk color thumbnails
            pic = Image.open(aver[pics[0]])  # open the most close thumbnail

            nim.paste(pic, (i * thumb_width, row * thumb_height))  # paste image
            tail.insert(0, pic)  # add image to tail
            tail.pop()  # remove 5th tail's picture

            # Check for identical pictures
            # If all four pictures is identical, randomly change one in random position
            if tail.count(tail[0]) == 4:
                pic = Image.open(aver[rn.choice(pics[1:])])  # change for another picture
                position = rn.choice(range(4))  # choose position for changing
                nim.paste(pic, (i * thumb_width - thumb_width * position, row * thumb_height))
                tail[3 - position] = pic

    return nim


# ----------------------------- MAIN SCRIPT -----------------------------

# Create folders
os.makedirs(path_thumbs, exist_ok=True)

# Save all necessary files and create thumbnails
if download_photos:

    while current_page < pages:
        try:
            save_photos(pages)
        except URLError:
            print("\n I've caught error and try to reconnect. ")

    create_thumbs(thumb_width, thumb_height)

im = Image.open(path_to_image)  # Open image for transformation
size_w, size_h = im.size

palette = create_palette()

# Chunking original image and creating data-list
chunks = []
for y in range(0, size_h-(size_h % chunk_height), chunk_height):

    progress(y, size_h, status='Chunking image')
    row = []

    for x in range(0, size_w-(size_w % chunk_width), chunk_width):
        pixels = get_matrix(im, x, y)
        set_color((find_mean_RGB(pixels)), x, y)
        row.append(find_mean_RGB(pixels))

    chunks.append(row)

print('\nChunked! ')
im.show()

# Creating new image
nim = pure_art(chunks, palette)
nim.show()
nim.save(path+'result_art.jpg', 'jpeg')
