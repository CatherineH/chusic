#!/usr/bin/python

import argparse
import os
import sys
import eyed3
eyed3.log.setLevel("ERROR")
from chusic import copy_dir, get_music, reorganize_music

parser = argparse.ArgumentParser(description='Reorganize the music based on '
                                             'artist/album structure')
parser.add_argument('--foldername', type=str, help='The foldername to '
                                                   'organize')
parser.add_argument('--destination', type=str, help='The location to copy '
                                                    'files to')

separators = ['_', '-']


def main():
    args = parser.parse_args()
    if args.destination is not None:
        file_lists = get_music(new_foldername=args.foldername)
        mp3_lists = file_lists['mp3']
        reorganize_music(args.destination, mp3_lists)
    else:
        print("Please specify a destination folder")


if __name__ == "__main__":
    sys.exit(main())