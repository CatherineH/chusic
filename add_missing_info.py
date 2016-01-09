#!/usr/bin/python

import argparse
import os
import sys
import fnmatch
import eyed3
import Image
import shutil
import re
parser = argparse.ArgumentParser(description='Guess at the missing information on MP3 tracks')
parser.add_argument('--foldername', type=str, help='The foldername to search')

def main():
    args = parser.parse_args()
    # remove the last /, if it exists
    if args.foldername[-1] == '/':
        args.foldername = args.foldername[:-1]
    args.foldername = os.path.expanduser(args.foldername)
    new_foldername = args.foldername+"-copy"
    # copy the folder so that we can work on it without worry
    # this will delete the existing copy
    if os.path.isdir(new_foldername):
        shutil.rmtree(new_foldername)
    shutil.copytree(args.foldername, new_foldername)

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

    for _path in mp3_lists.keys():
        for _mp3_file in mp3_lists[_path]:
            # update the metadata for the mp3
            _audiofile = eyed3.load(_mp3_file)
            # check that the title exists
            if _audiofile.tag.title is None:
                print "file: "+_mp3_file+" is missing the title, guess is: "+guess_title(_mp3_file)
                _audiofile.tag.title = unicode(guess_title(_mp3_file))
            if _audiofile.tag.album is None:
                print "file: "+_mp3_file+" is missing the album"
            if _audiofile.tag.artist is None:
                print "file: "+_mp3_file+" is missing the artist"
            _audiofile.tag.save()


def guess_title(filename):
    """
    guess the title based on the filename
    :param filename: the filename of the MP3
    :type filename: str
    :return: the guessed title
    :rtype: str
    """
    title = os.path.splitext(os.path.basename(filename))
    title = re.sub('^[0-9 ]+', '', title[0])
    # remove the number
    return title

if __name__ == "__main__":
    sys.exit(main())