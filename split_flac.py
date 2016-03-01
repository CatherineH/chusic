#!/usr/bin/python

import subprocess
import argparse
import os
import sys
from fnmatch import fnmatch
from chusic import copy_dir, convert_files
from cueparser import CueSheet
from send2trash import send2trash



parser = argparse.ArgumentParser(description='Chop Up all flacs in a folder based on the cue')
parser.add_argument('--foldername', type=str, help='The foldername to search')


def main():
    args = parser.parse_args()
    new_foldername = copy_dir(args.foldername)
    for root, dirs, files in os.walk(new_foldername):
        # keep a list of all cues and flacs
        flac_filenames = []
        cue_filenames = []
        thumbnail_filename = None
        for name in files:
            if fnmatch(name, "*.flac") or fnmatch(name, ".m4a") or fnmatch(
                    name, '.wma'):
                flac_filenames.append(os.path.join(root, name))
            if fnmatch(name, "*.cue"):
                cue_filenames.append(os.path.join(root, name))
            if fnmatch(name, "*.jpg"):
                thumbnail_filename = os.path.join(root, name)
        # we should now have exactly one flac and one cue file
        if len(flac_filenames) == 1 and len(cue_filenames) == 1:

            ps = subprocess.Popen(('cuebreakpoints', cue_filenames[0]),
                                  stdout=subprocess.PIPE)
            subprocess.check_output(('shnsplit', '-o', 'flac', flac_filenames[0], '-a',
                                     flac_filenames[0].replace(root,'').replace('.flac', ''), '-d', root),
                                    stdin=ps.stdout)
            ps.wait()
            # move the old flac file to the trash
            send2trash(flac_filenames[0])

        if len(cue_filenames)>0:
            cuesheet = CueSheet()
            cuesheet.setOutputFormat('%performer% - %title%\n%file%\n%tracks%', '%title%')
            with open(cue_filenames[0], "r") as f:
                cuesheet.setData(f.read())
            cuesheet.parse()
        else:
            cuesheet = None
        print root
        # convert the other flacs to mp3
        convert_files(root, cuesheet=cuesheet, thumbnail_filename=thumbnail_filename)

if __name__ == "__main__":
    sys.exit(main())
