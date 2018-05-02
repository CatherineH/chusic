from chusic import copy_dir, get_music, guess_title, guess_album
from argparse import ArgumentParser
import os
import os.path
import eyed3
eyed3.log.setLevel("ERROR")

parser = ArgumentParser(description='Identify missing information in a file '
                                    '(i.e., image, title, artist, album)')
parser.add_argument('--foldername', type=str, help='The foldername to search')


def decode_unicode(instr):
    try:
        return unicode(instr)
    except UnicodeDecodeError:
        return instr.decode('utf-8')


def main():
    args = parser.parse_args()
    new_foldername = args.foldername
    file_lists = get_music(new_foldername=new_foldername)
    mp3_lists = file_lists['mp3']
    path_images = file_lists['images']
    total_tracks = 0
    prev_separator = None
    for _path in mp3_lists.keys():
        for _mp3_file in mp3_lists[_path]:
            save_track = False
            total_tracks += 1
            print(_mp3_file)

            # update the metadata for the mp3
            guess = guess_title(_mp3_file, mp3_lists[_path],
                        prev_separator, verbose=True)
            # remove whitespace and
            for key in guess.keys():
                guess[key] = guess[key].strip().title()
            prev_separator = guess['separator']
            _audiofile = eyed3.load(_mp3_file)
            if _audiofile.tag is None:
                _audiofile.initTag()
            if _audiofile.tag.title is None:
                response = raw_input("Accept new title? (y/n)")
                if response == 'y':
                    _audiofile.tag.title = decode_unicode(guess['title'])
                    save_track = True
            if _audiofile.tag.album is None:
                album = guess['album']
                response = raw_input("Accept new album? (y/n)")
                if response == 'y':
                    _audiofile.tag.album = decode_unicode(album)
                    save_track = True
            if _audiofile.tag.artist is None:
                response = raw_input("Accept new artist? (y/n)")
                if response == 'y':
                    _audiofile.tag.artist = decode_unicode(guess['artist'])
                    save_track = True
            if len(_audiofile.tag.images) == 0:
                if _path in path_images:
                    response = raw_input("Use image: "+str(path_images[_path])+" ("
                                                                  "y/n)?")
                    if response == 'y':
                        _image_path = os.path.join(_path, path_images[_path])
                        jpgfile = open(_image_path, "rb")
                        _audiofile.tag.images.set(0x03, jpgfile.read(), 'image/jpeg')
                        jpgfile.close()
                        save_track = True
            if save_track:
                _audiofile.tag.save(filename=_mp3_file,version=eyed3.id3.ID3_V2_4)
    print "total tracks: "+str(total_tracks)

if __name__ == "__main__":
    main()
