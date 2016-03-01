#!/usr/bin/python

import argparse
import os
import sys
import fnmatch
import eyed3
import Image
eyed3.log.setLevel("ERROR")
from chusic import copy_dir, get_music, get_image
parser = argparse.ArgumentParser(description='Add images to MP3 tracks')
parser.add_argument('--foldername', type=str, help='The foldername to search')
parser.add_argument('--online', dest='web_search', action='store_true', help='search online for images')
parser.set_defaults(web_search=False)

def main():
    args = parser.parse_args()
    new_foldername = args.foldername #copy_dir(args.foldername)
    file_lists = get_music(new_foldername=new_foldername)
    mp3_lists = file_lists['mp3']
    path_images = file_lists['images']
    seen_covers = {}
    web_search = args.web_search
    for _path in mp3_lists.keys():
        current_track = 1
        for _mp3_file in mp3_lists[_path]:

            # update the metadata for the mp3
            _audiofile = eyed3.load(_mp3_file)
            if len(_audiofile.tag.images) > 0:
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
                if cover_key not in seen_covers.keys():
                    print "cover key not in seen covers, going to search the web"
                    [web_image, mime] = get_image(_audiofile.tag.album,
                                          _audiofile.tag.artist,
                                                  web_search)
                    if web_image is None:
                        print "search failed for: ("+cover_key+")"
                        continue
                    img = Image.open(web_image)
                    img.show()

                    response = raw_input("Is album cover acceptable ("
                                         ""+_audiofile.tag.artist+") ("
                                         ""+_audiofile.tag.album+")? y/n")

                    if response == "y":
                        seen_covers[cover_key] = web_image
                        jpgfile = open(web_image, "rb")
                        _audiofile.tag.images.set(0x03,  jpgfile.read(), mime)
                        jpgfile.close()
                        _audiofile.tag.save(filename=_mp3_file,version=eyed3.id3.ID3_V2_4)
                    else:
                        seen_covers[cover_key] = "invalid"
                else:
                    if seen_covers[cover_key] != "invalid":
                        jpgfile = open(seen_covers[cover_key], "rb")
                        _audiofile.tag.images.set(0x03,  jpgfile.read(), mime)
                        jpgfile.close()
                        _audiofile.tag.save(filename=_mp3_file,version=eyed3.id3.ID3_V2_4)
            current_track += 1
            #print "saving track: "+_mp3_file+" image path was: "+_image_path

if __name__ == "__main__":
    sys.exit(main())