#!/usr/bin/python

import argparse
import os
import sys
import fnmatch
import eyed3
import Image
import shutil
parser = argparse.ArgumentParser(description='Add images to MP3 tracks')
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
    # if an image is found, save it as the thumbnail for that folder
    mp3_lists = {}
    path_images = {}
    for root, dirs, files in os.walk(new_foldername):
        for name in files:
            _dir = root
            if fnmatch.fnmatch(name.lower(), "*.mp3"):
                if _dir in mp3_lists.keys():
                    mp3_lists[_dir].append(os.path.join(root, name))
                else:
                    mp3_lists[_dir] = [os.path.join(root, name)]
            #else:
            #    print "file: "+name+" did not match"
            if fnmatch.fnmatch(name.lower(), "*.jpg"):
                os.rename(os.path.join(root, name), os.path.join(root, 'thumb.jpg'))
                path_images[_dir] = os.path.join(root, 'thumb.jpg')

    for _path in mp3_lists.keys():
        # check to make sure that we also have a cover image for this path
        if _path in path_images.keys():
            current_track = 1
            print _path
            for _mp3_file in mp3_lists[_path]:
                # update the metadata for the mp3
                _image_path = os.path.join(_path, path_images[_path])
                _audiofile = eyed3.load(_mp3_file)
                jpgfile = open(_image_path, "rb")

                _audiofile.tag.images.set(0x03, jpgfile.read(), 'image/jpeg')
                jpgfile.close()
                _audiofile.tag.save(version=eyed3.id3.ID3_V2_4)
                current_track += 1
                #print "saving track: "+_mp3_file+" image path was: "+_image_path
            # test the image information on the tracks
            for _mp3_file in mp3_lists[_path]:
                _audiofile = eyed3.load(_mp3_file)
                saved_image = _audiofile.tag.images
        else:
            print "No cover image found for path: "+_path

if __name__ == "__main__":
    sys.exit(main())