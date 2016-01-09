#!/usr/bin/python

import argparse
import os
import os.path
import sys
import fnmatch
import eyed3
from pandas import DataFrame
from tinytag import TinyTag

parser = argparse.ArgumentParser(description='Get the title, artist, album, and date modified information on MP3 and '
                                             'flac files.')
parser.add_argument('--foldername', type=str, help='The foldername to search')


def main():
    args = parser.parse_args()
    args.foldername = os.path.expanduser(args.foldername)
    # keep a list of all cues and flacs
    music_filenames = []

    for root, dirs, files in os.walk(args.foldername):
        #print dirs
        for name in files:
            if fnmatch.fnmatch(name, "*.flac") or fnmatch.fnmatch(name, "*.mp3"):
                # check to see if that file already exists in the list
                for music_filename in music_filenames:
                    if music_filename.split("/")[-1] == name:
                        print 'found possible duplicate file, old one is: '+music_filename
                        print 'new one is: '+os.path.join(root, name)
                music_filenames.append(os.path.join(root, name))
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
