#!/usr/bin/python

import argparse
import os
import sys
import fnmatch
from mimetypes import guess_type
import eyed3
from PIL import Image
from resizeimage import resizeimage
eyed3.log.setLevel("ERROR")
from chusic import copy_dir, get_music, get_image
parser = argparse.ArgumentParser(description='Add images to MP3 tracks')
parser.add_argument('--foldername', type=str, help='The foldername to search')
parser.add_argument('--online', dest='online', action='store_true', help='search online for images')
parser.add_argument('--copy', dest='copy', action='store_true',
                    help='make changes to a copy')
parser.add_argument('--ignore', dest='ignore', action='store_true',
                    help='ignore existing art')

parser.set_defaults(web_search=False)
parser.set_defaults(copy=False)
parser.set_defaults(ignore=False)

def main():
    args = parser.parse_args()
    if not hasattr(args, 'online'):
        args.online = False
    if args.copy:
        new_foldername = copy_dir(args.foldername)
    else:
        new_foldername = args.foldername
    file_lists = get_music(new_foldername=new_foldername)
    mp3_lists = file_lists['mp3']
    path_images = file_lists['images']
    seen_covers = {}
    web_search = args.online
    print(web_search)
    for _path in mp3_lists.keys():
        current_track = 1
        for _mp3_file in mp3_lists[_path]:

            # update the metadata for the mp3
            _audiofile = eyed3.load(_mp3_file)
            if len(_audiofile.tag.images) > 0 and not args.ignore:
                continue
            cover_key = _audiofile.tag.artist+"_"+_audiofile.tag.album
            if _audiofile.tag is None:
                print "initializing tag"
                # the track likely has no tags
                _audiofile.tag = eyed3.id3.tag.Tag()

            if _path in path_images.keys():
                _image_path = os.path.join(_path, path_images[_path])
                jpgfile = open(_image_path, "rb")
                _audiofile.tag.images.set(0x03, jpgfile.read(), 'image/jpeg')
                jpgfile.close()
                _audiofile.tag.save(filename=_mp3_file,
                                    version=eyed3.id3.ID3_V2_4)
            else:
                if cover_key not in seen_covers.keys() and web_search:
                    print "cover key not in seen covers, going to search the web"
                    web_image = get_image(_audiofile.tag.album,
                                          _audiofile.tag.artist,
                                                  web_search)
                    if web_image is None:
                        print "search failed for: ("+cover_key+")"
                        continue
                    try:
                        if isinstance(web_image, list):
                            for _item in web_image:
                                if check_image(_item, cover_key):
                                    seen_covers[cover_key] = _item
                                    break
                        if isinstance(web_image, basestring):
                            if check_image(web_image, cover_key):
                                seen_covers[cover_key] = web_image
                    except Exception as e:
                        print "Critical failure on: "+cover_key
                        print(e)
                        seen_covers[cover_key] = 'invalid'
                        continue
                if not cover_key in seen_covers.keys():
                    seen_covers[cover_key] = 'invalid'

                if seen_covers[cover_key] != "invalid":
                    jpgfile = open(seen_covers[cover_key], "rb")
                    img = Image.open(jpgfile)
                    img = img.resize((400, 400))
                    img.save(seen_covers[cover_key])
                    jpgfile.close()

                    jpgfile = open(seen_covers[cover_key], "rb")


                    mime = guess_type(seen_covers[cover_key])[0]
                    _audiofile.tag.images.set(0x03,  jpgfile.read(), mime)
                    jpgfile.close()
                    _audiofile.tag.save(filename=_mp3_file,version=eyed3.id3.ID3_V2_4)
            current_track += 1
            #print "saving track: "+_mp3_file+" image path was: "+_image_path


def check_image(item, cover_key):
    img = Image.open(item)
    img.show()

    response = raw_input("Is album cover acceptable ("+cover_key.encode('utf-8')+")? y/n")
    if response == "y":
        return True
    else:
        return False

if __name__ == "__main__":
    sys.exit(main())