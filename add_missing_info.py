#!/usr/bin/python

import argparse
import os
import sys
import fnmatch
import eyed3
from chusic import copy_dir
import re
parser = argparse.ArgumentParser(description='Guess at the missing information on MP3 tracks')
parser.add_argument('--foldername', type=str, help='The foldername to search')

separators = ['_', '-']


def main():
    args = parser.parse_args()
    new_foldername = copy_dir(args.foldername)

    # recursively walk through the directory structure
    # if an mp3 is found, add it to the list of tracks for that folder
    mp3_lists = {}
    for root, dirs, files in os.walk(new_foldername):
        for name in files:
            _dir = root
            if fnmatch.fnmatch(name, "*.mp3"):
                if _dir in mp3_lists.keys():
                    mp3_lists[_dir].append(os.path.join(root, name))
                else:
                    mp3_lists[_dir] = [os.path.join(root, name)]
    prev_separator = None
    for _path in mp3_lists.keys():
        for _mp3_file in mp3_lists[_path]:
            print _mp3_file
            # update the metadata for the mp3
            _audiofile = eyed3.load(_mp3_file)
            # check that the title exists
            guess = guess_title(_mp3_file, mp3_lists[_path], prev_separator)
            prev_separator = guess['separator']
            if _audiofile.tag.title is None:
                print "file: "+_mp3_file+" is missing the title, guess is: "+guess['title']
                _audiofile.tag.title = unicode(guess['title'])
            else:
                guess['title'] = _audiofile.tag.title
            if _audiofile.tag.album is None:
                album = guess_album(_path, guess['artist'])
                print "file: "+_mp3_file+" is missing the album, guess is: "+album
                _audiofile.tag.album = unicode(album)
            if _audiofile.tag.artist is None:
                print "file: "+_mp3_file+" is missing the artist, guess is: "+guess['artist']
                _audiofile.tag.artist = unicode(guess['artist'])
            _audiofile.tag.save()


def guess_album(filename, artist):

    filename = strip_filename(filename)
    album = filename.lower().replace(artist.lower(), '')
    album = album.replace('-copy', '')
    for separator in separators:
        album = album.replace(separator, '').strip()

    return album.capitalize()

def strip_filename(filename):
    title = os.path.splitext(os.path.basename(filename))
    # remove the number
    title = re.sub('^[0-9 ]+', '', title[0])
    return title


def guess_title(filename, other_filenames, separator=None):
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
        if len(parts) == 2:
            candidates.append(separator)
    if len(candidates) != 1 and separator is None:
        print "difficulty discerning separators, candidates are: "+str(candidates)
        return
    elif len(candidates) != 1:
        candidates = [separator]

    # now guess the artist
    # going to guess that the most common tag is the artist
    tags = {}
    print candidates[0]
    for other_filename in other_filenames:
        other_filename = strip_filename(other_filename)
        parts = other_filename.split(candidates[0])
        for part in parts:
            if len(part)>0:
                if part not in tags.keys():
                    tags[part] = 1
                else:
                    tags[part] += 1

    #print tags
    max_key = ''
    counter = 0

    for key in tags.keys():
        if tags[key] > counter:
            counter = tags[key]
            max_key = key
    artist = max_key

    parts = title.split(candidates[0])
    for part in parts:
        if len(part) == 0:
            parts.remove(part)

    if parts[0].find(artist) >= 0:
        title = parts[1]
    else:
        title = parts[0]

    for separator in separators:
        artist = artist.replace(separator, ' ')
        title = title.replace(separator, ' ')

    artist = artist.capitalize()
    title = title.capitalize()

    return {'title': title, 'artist': artist, 'separator': candidates[0]}

if __name__ == "__main__":
    sys.exit(main())