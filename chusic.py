import os
from shutil import rmtree, copytree, copyfile
from fnmatch import fnmatch
import re
from eyed3 import load
from googleapiclient.discovery import build
from PIL import Image
import urllib
import time

separators = ['_', '-']


def guess_album(filename, artist='', title=''):
    # first, try with the full filename
    filename = strip_filename(filename)
    print "guess album filename: "+filename+" artist: "+artist+" title: " \
                                                               ""+title
    album = filename.lower().replace(artist.lower(), '')
    album = album.lower().replace(title.lower(), '')
    album = album.replace('-copy', '')
    for separator in separators:
        album = album.replace(separator, '').strip()
    album = re.sub('[0-9]+$', '', album)
    album = re.sub('cd\s*\d', '', album)
    return album.capitalize()

def strip_filename(filename):
    title = os.path.splitext(os.path.basename(filename))
    # remove the number
    title = re.sub('^[0-9 ]+', '', title[0])
    return title


def guess_title(filename, other_filenames, separator=None, verbose=False):
    """
    guess the title based on the filename and the other filenames
    :param filename: the filename of the MP3
    :type filename: str
    :param filenames: the filenames of the MP3s nearby
    :type filenames: list
    :return: the guessed title
    :rtype: str
    """
    title = strip_filename(filename)
    # now, let's try to see if there's two sections - one for the title, one for the artist
    candidates = []
    for separator in separators:
        # remove the separator at the beginning of the string
        _temp = re.sub('^'+separator, '', title)
        parts = _temp.split(separator)
        if len(parts) >= 2:
            candidates.append(separator)
    if len(candidates) != 1 and separator is None:
        print "difficulty discerning separators, candidates are: "+str(candidates)
        return
    elif len(candidates) != 1:
        candidates = [separator]

    # now guess the artist
    # going to guess that the most common tag is the artist
    tags = {}
    #print candidates[0]
    for other_filename in other_filenames:
        other_filename = strip_filename(other_filename)
        parts = other_filename.split(candidates[0])
        for part in parts:
            if len(part) > 0:
                if part not in tags.keys():
                    tags[part] = 1
                else:
                    tags[part] += 1

    if verbose:
        print tags

    max_key = max(tags)


    artist = max_key
    if verbose:
        print "guess artist is: "+artist
    if len(other_filenames) > 1:
        for key in tags.keys():
            if tags[key] == len(other_filenames) and len(other_filenames) > 1:
                title = title.replace(key, '')
    else:
        title = title.replace(artist, "")
    # title = title.replace(candidates[0], '')
    title = re.sub('^[0-9 ]+', '', title)
    if verbose:
        print "guess title is: "+title


    for separator in separators:
        artist = artist.replace(separator, ' ')
        title = title.replace(separator, ' ')

    artist = artist.capitalize()
    title = title.capitalize()

    return {'title': title, 'artist': artist, 'separator': candidates[0]}


def copy_dir(foldername=None):
    # remove the last /, if it exists
    if foldername[-1] == '/':
        foldername = foldername[:-1]
    foldername = os.path.expanduser(foldername)
    new_foldername = foldername+"-copy"
    # copy the folder so that we can work on it without worry
    # this will delete the existing copy
    if os.path.isdir(new_foldername):
        rmtree(new_foldername)
    copytree(foldername, new_foldername)
    return new_foldername


def get_music(new_foldername):
    # recursively walk through the directory structure
    # if an mp3 is found, add it to the list of tracks for that folder
    # if an image is found, save it as the thumbnail for that folder
    mp3_lists = {}
    path_images = {}
    for root, dirs, files in os.walk(new_foldername):
        for name in files:
            _dir = root
            # ignore hidden files
            if name[0] == '.':
                continue
            if fnmatch(name.lower(), "*.mp3") or fnmatch(name.lower(), ".m4a"):
                if _dir in mp3_lists.keys():
                    mp3_lists[_dir].append(os.path.join(root, name))
                else:
                    mp3_lists[_dir] = [os.path.join(root, name)]
            #else:
            #    print "file: "+name+" did not match"
            if fnmatch(name.lower(), "*.jpg"):
                os.rename(os.path.join(root, name), os.path.join(root, 'thumb.jpg'))
                path_images[_dir] = os.path.join(root, 'thumb.jpg')
    return {'mp3': mp3_lists, 'images': path_images}

def reorganize_music(root, mp3_lists):
    """
    reorganize the music collection based on the format artist/album/track.mp3
    :param root: the new foldername
    :param _mp3_list: the list of mp3 paths
    :return:
    """
    for _path in mp3_lists.keys():
        for _mp3_file in mp3_lists[_path]:
            print _mp3_file
            # update the metadata for the mp3
            _audiofile = load(_mp3_file)
            if _audiofile.tag.album is None or _audiofile.tag.artist is None:
                print "warning: not able to place file: "+_mp3_file
                continue
            artist = _audiofile.tag.artist
            album = _audiofile.tag.album
            directory = os.path.join(root, artist, album)
            if not os.path.exists(directory):
                os.makedirs(directory)
            _mp3_file = _mp3_file.decode('utf-8')
            new_filename = os.path.join(directory, os.path.basename(_mp3_file))
            copyfile(_mp3_file, new_filename)


def get_image(album="", artist="", search=True):
    # first, check to see whether the file already exists in the covers
    cover_location = os.path.expanduser("~/covers")
    if not os.path.exists(cover_location):
        os.makedirs(cover_location)
    cover_filename = os.path.join(cover_location, album+"_"+artist+".jpg")
    if not os.path.exists(cover_filename) and search:

        key = os.environ.get('GOOGLE_API_KEY')
        service = build("customsearch", "v1", developerKey=key)
        query = album+"+"+artist+"+album+art"
        try:
            res = service.cse().list(
                q=query, cx="015111312832054302537:ijkg6sdfkiy", searchType='image',
                num=1, ).execute()
            time.sleep(1.5)

            item = res['items'][0]
            mime = item['mime']
            _image = urllib.urlretrieve(item['link'], cover_filename)
            return [_image[0], mime]
        except:
            return [None, None]
    elif not os.path.exists(cover_filename):
        fhandle = open(cover_filename, 'a')
        fhandle.close()
        return [cover_filename, 'image/jpeg']
    else:
        return [cover_filename, 'image/jpeg']

    # Be nice to Google and they'll be nice back :)


