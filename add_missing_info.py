#!/usr/bin/python

import argparse
import os
import sys
import eyed3
from chusic import copy_dir, get_music, guess_title, guess_album, \
    load_mappings, check_mappings

parser = argparse.ArgumentParser(description='Guess at the missing information on MP3 tracks')
parser.add_argument('--foldername', type=str, help='The foldername to search')
parser.add_argument('-i', '--ignore', action="store_true", dest="ignore",
                    default=False,
                    help="If the tag is present, any existing MP3 tags "
                             "will be ignored.")

separators = ['_', '-']



def main():
    args = parser.parse_args()
    new_foldername = copy_dir(args.foldername)
    file_lists = get_music(new_foldername=new_foldername)
    mp3_lists = file_lists['mp3']
    prev_separator = None
    for _path in mp3_lists.keys():
        for _mp3_file in mp3_lists[_path]:
            # update the metadata for the mp3
            _audiofile = eyed3.load(_mp3_file)
            # check that the title exists
            guess = guess_title(_mp3_file, mp3_lists[_path], prev_separator)
            if _audiofile.tag is None:
                _audiofile.initTag()
            prev_separator = guess['separator']
            if _audiofile.tag.title is None or args.ignore:
                print("file: "+_mp3_file+" is missing the title, guess is: "+
                      guess['title'])
                _audiofile.tag.title = check_mappings(guess['title'])
            else:
                guess['title'] = _audiofile.tag.title
            if _audiofile.tag.album is None or args.ignore:
                album = guess_album(_path, guess['artist'])
                print("file: "+_mp3_file+" is missing the album, guess is: "+
                      album)
                _audiofile.tag.album = check_mappings(album)
            if _audiofile.tag.artist is None or args.ignore:
                print("file: "+_mp3_file+" is missing the artist, guess is: "
                      +guess['artist'])
                _audiofile.tag.artist = check_mappings(guess['artist'])
            else:
                _audiofile.tag.artist = check_mappings(_audiofile.tag.artist)
            _audiofile.tag.save()


if __name__ == "__main__":
    sys.exit(main())