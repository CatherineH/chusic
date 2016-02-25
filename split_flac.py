#!/usr/bin/python

import subprocess
import argparse
import os
import sys
import fnmatch
from chusic import copy_dir
from cueparser import CueSheet
from send2trash import send2trash
import eyed3


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
            if fnmatch.fnmatch(name, "*.flac"):
                flac_filenames.append(os.path.join(root, name))
            if fnmatch.fnmatch(name, "*.cue"):
                cue_filenames.append(os.path.join(root, name))
            if fnmatch.fnmatch(name, "*.jpg"):
                thumbnail_filename = os.path.join(root, name)
        # we should now have exactly one flac and one cue file
        if len(flac_filenames) == 1 and len(cue_filenames) == 1:

            ps = subprocess.Popen(('cuebreakpoints',cue_filenames[0]), stdout=subprocess.PIPE)
            subprocess.check_output(('shnsplit', '-o', 'flac', flac_filenames[0], '-a',
                                     flac_filenames[0].replace(root,'').replace('.flac', ''), '-d', root),
                                    stdin=ps.stdout)
            ps.wait()
            # move the old flac file to the trash
            send2trash(flac_filenames[0])
        elif len(cue_filenames)<1:
            continue

        cuesheet = CueSheet()
        cuesheet.setOutputFormat('%performer% - %title%\n%file%\n%tracks%', '%title%')
        with open(cue_filenames[0], "r") as f:
            cuesheet.setData(f.read())
        cuesheet.parse()

        # convert the other flacs to mp3
        curr_dir_files = sorted(os.listdir(root))
        current_track = 0
        for _file in curr_dir_files:
            if fnmatch.fnmatch(_file, '*.flac'):
                in_flac = os.path.join(root,_file)
                out_mp3 = in_flac.replace('flac', 'mp3')
                subprocess.call(('avconv','-i', in_flac, '-qscale:a', '0',
                                 out_mp3))
                # move the flac to the trash
                send2trash(os.path.join(root, _file))
                # update the metadata for the mp3
                _audiofile = eyed3.load(out_mp3)
                if thumbnail_filename is not None:
                    _audiofile.tag.images.set(0x03, thumbnail_filename, 'jpg')
                _audiofile.tag.artist = unicode(cuesheet.performer)
                _audiofile.tag.album = unicode(cuesheet.title)
                _audiofile.tag.title = unicode(cuesheet.tracks[current_track])
                _audiofile.tag.track_num = current_track+1
                _audiofile.tag.save()
                current_track += 1

if __name__ == "__main__":
    sys.exit(main())
