"""
Application for creating image, that consists of small images (thumbnails) of porn actors.
You must set path to target image, also you can choose gender of actors, chunks size and thumbnails size.
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

path_to_image = '/home/immo/Pictures/roj.jpg'  # Path to your image for transformation

gender = 'female'  # you can set 'male' or 'female'
pages = 5  # save 56 photos for every porhnub page. More is better, but slower

# Set False, if you run that script not for the first time and all photos are downloaded
# It will save your time from redownloading photos and creating thumbnails
download_stuff = True

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


# Opens pornhub and gathers photos, saves them in the folder 'just_for_science'
def save_photos(till_page):

    global current_page

    for j in range(current_page, till_page):

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
                    if 'pornstars' in src:
                        stars.append(src)

            for i in range(len(stars)):
                progress(i, len(stars), status='saving from page {}'.format(j))
                urlretrieve(stars[i], path_photos+str(j) + '_{}.jpg'.format(i))

        current_page += 1
        
    print('\nPhotos downloading complete!')


# Creates thumbnails for saved pictures with some size, saves them in 'just_for_science/thumbs'
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


# Finds the average color of given pixel array
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


# Creates matrix of pixels
def get_matrix(im, xr, yr):
    pixels = []
    for x in range(xr, xr+chunk_width):
        for y in range(yr, yr+chunk_height):
            pixels.append(im.getpixel((x, y)))
    return pixels


# Paints chunk of image in one, average, color
def set_color(color, xstart, ystart):
    for x in range(xstart, xstart+chunk_width):
        for y in range(ystart, ystart+chunk_height):
            im.putpixel((x, y), color)


# Returns four closest pictures by average RGB
def closest_pic(aver, color):

    pal = aver.keys()
    close = sorted(pal, key=lambda x: (abs(color[0]-x[0]) +
                                       abs(color[1]-x[1] +
                                       abs(color[2]-x[2])))/3)
    return close[:4]


# Creates dir with average colors as keys and photos as values
def create_palette():

    palette = {}
    glb = glob.glob(path_thumbs+"*.thumbnail")

    counter = 0

    for infile in glb:

        progress(counter, len(glb), status='creating palette')
        counter +=1 
        
        im = Image.open(infile)
        color = []

        for x in range(thumb_width):
            for y in range(thumb_height):
                color.append(im.getpixel((x, y)))

        avr_color = find_mean_RGB(color)
        palette[avr_color] = infile

    print('\nPalette created.')

    return palette


# Returns new image, consisting of photos thumbnails
def pure_art(data, aver):
    
    nim = Image.new('RGB', (len(data[0])*thumb_width, len(data)*thumb_height), 'white')

    counter = 0

    for row in range(len(data)):

        progress(counter, len(data), status='creating image')
        counter += 1

        tail = [0, 0, 0, 0]

        for i in range(len(data[row])):

            pics = closest_pic(aver, data[row][i])
            pic = Image.open(aver[pics[0]])
                                             
            nim.paste(pic, (i*thumb_width, row*thumb_height))
            tail.insert(0, pic)
            tail.pop()

            # Check for identical pictures
            if tail.count(tail[0]) == 4:
                pic = Image.open(aver[rn.choice(pics[1:])])
                position = rn.choice((0, 1, 2, 3))
                nim.paste(pic, (i*thumb_width-thumb_width*position, row*thumb_height))
                tail[3-position] = pic


    return nim


# ----------------------------- MAIN SCRIPT -----------------------------

# Create folders
os.makedirs(path_thumbs, exist_ok=True)

current_page = 0  # For possible error 'connection reset by peer'

# Save all necessary files and create thumbnails
if download_stuff:

    while current_page < pages:
        try:
            save_photos(pages)
        except URLError:
            print("\n I've caught error and try to reconnect")

    create_thumbs(thumb_width, thumb_height)

im = Image.open(path_to_image)  # Open image for transformation
size_x, size_y = im.size

palette = create_palette()

# Chunking original image and creating data-list
chunks = []
for y in range(0, size_y-(size_y % chunk_height), chunk_height):

    progress(y, size_y, status='Chunking image')
    row = []

    for x in range(0, size_x-(size_x % chunk_width), chunk_width):
        pixels = get_matrix(im, x, y)
        set_color((find_mean_RGB(pixels)), x, y)
        row.append(find_mean_RGB(pixels))

    chunks.append(row)

print('\nchunked!')
im.show()

# Creating new image
nim = pure_art(chunks, palette)
nim.show()
nim.save(path+'result_art.jpg', 'jpeg')
