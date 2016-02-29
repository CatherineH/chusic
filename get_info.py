#!/usr/bin/python

import argparse
import os
import os.path
import sys
import fnmatch
import eyed3
from chusic import get_music
from pandas import DataFrame
from tinytag import TinyTag

parser = argparse.ArgumentParser(description='Get the title, artist, album, and date modified information on MP3 and '
                                             'flac files.')
parser.add_argument('--foldername', type=str, help='The foldername to search')


def main():
    args = parser.parse_args()
    args.foldername = os.path.expanduser(args.foldername)
    new_foldername = args.foldername
    # keep a list of all cues and flacs
    file_lists = get_music(new_foldername=new_foldername)
    music_filenames = file_lists['mp3']
    # now, for each file, get the mp3 tags and get the date created
    music_dataframe = []
    for music_file in music_filenames:
        try:
            tag = TinyTag.get(music_file)
        except Exception as e:
            print e
            next
        if tag.artist is not None:
            artist = tag.artist.encode('ascii', 'ignore')
        if tag.album is not None:
            album = tag.album.encode('ascii', 'ignore')
        if tag.title is not None:
            title = tag.title.encode('ascii', 'ignore')
        date_changed = os.path.getmtime(music_file)
        music_dataframe.append({'artist':artist,'album':album,'title':title,'date':date_changed})


    music_dataframe = DataFrame(music_dataframe)
    music_dataframe.to_csv("mp3_tags.csv")

if __name__ == "__main__":
    sys.exit(main())
