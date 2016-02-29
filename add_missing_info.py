#!/usr/bin/python

import argparse
import os
import sys
import eyed3
from chusic import copy_dir, get_music, guess_title, guess_album

parser = argparse.ArgumentParser(description='Guess at the missing information on MP3 tracks')
parser.add_argument('--foldername', type=str, help='The foldername to search')

separators = ['_', '-']


def main():
    args = parser.parse_args()
    new_foldername = copy_dir(args.foldername)
    file_lists = get_music(new_foldername=new_foldername)
    mp3_lists = file_lists['mp3']

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



if __name__ == "__main__":
    sys.exit(main())