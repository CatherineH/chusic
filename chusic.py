import os
import zipfile
from collections import Counter, defaultdict
from shutil import rmtree, copytree, copyfile
from fnmatch import fnmatch
import re
from eyed3 import load
try:
    from googleapiclient.discovery import build
except Exception:
    build = None
import urllib
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, Request
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, Request

import time

from os.path import isfile, expanduser
from send2trash import send2trash
from subprocess import call
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

import ast
import wget
import unidecode


separators = ['_', '-']


def load_mappings():
    fh_lines = open('mappings.csv', 'r').readlines()
    mappings = dict()
    for fh_line in fh_lines:
        parts = fh_line.split(",")
        mappings[parts[0]] = parts[1].strip()
    return mappings


def check_mappings(map_key, convert_unicode=True):
    mappings = load_mappings()

    if map_key in mappings.keys():
        return_value = mappings[map_key]
    else:
        return_value = map_key
    if convert_unicode:
        return unicode(return_value, 'utf-8')
    else:
        return return_value


def guess_album(filename, artist='', title=''):
    # first, try with the full filename
    filename = strip_filename(filename)
    print("guess album filename: ", filename, " artist: ", artist, " title: ",
          title)
    album = filename.lower().replace(artist.lower(), '')
    album = album.lower().replace(title.lower(), '')
    album = album.replace('-copy', '')
    for separator in separators:
        album = album.replace(separator, '').strip()
    album = re.sub('[0-9]+$', '', album)
    album = re.sub('cd\s*\d', '', album)
    return album.capitalize()


def strip_filename(filename):
    title = os.path.splitext(os.path.basename(filename))
    # remove the number
    title = re.sub('^[0-9 ]+', '', title[0])
    return title


def guess_title(filename, other_filenames, separator=None, verbose=False):
    """
    guess the title based on the filename and the other filenames
    :param filename: the filename of the MP3
    :type filename: str
    :param filenames: the filenames of the MP3s nearby
    :type filenames: list
    :return: the guessed title
    :rtype: dict
    """
    verbose = True
    title = filename.replace(expanduser("~/Music"), "")
    title = title.replace(".mp3", "")
    # now, let's try to see if there's two sections - one for the title, one for the artist
    candidates = []
    for separator in separators:
        # remove the separator at the beginning of the string
        _temp = re.sub('^'+separator, '', title)
        parts = _temp.split(separator)
        if len(parts) >= 2:
            candidates.append(separator)

    if len(candidates) != 1 and separator is None:
        print("difficulty discerning separators, candidates are: "+str(candidates))
        return
    elif len(candidates) != 1:
        candidates = [separator]

    # now guess the artist
    # going to guess that the most common tag is the artist
    tags = {}
    fragments = []
    for other_filename in other_filenames:
        other_filename = other_filename.replace(expanduser("~/Music"), "")
        other_filename = other_filename.replace("/", candidates[0])
        #other_filename = strip_filename(other_filename)
        parts = other_filename.split(candidates[0])

        for part in parts:
            if len(part) > 0:
                fragments.append(part.strip())
    # add the first fragment again to break ties
    if len(fragments) >= 1:
        fragments.append(fragments[0])

    counts = Counter(fragments)
    most_common = counts.most_common(2)
    if verbose:
        print(most_common)

    artist = most_common[0][0]
    album = most_common[1][0]
    if verbose:
        print("guess artist is: ", artist, " and album is: ", album)
    if len(other_filenames) > 1:
        for key in tags.keys():
            if tags[key] == len(other_filenames) and len(other_filenames) > 1:
                title = title.replace(key, '')
    # remove the alternate names for the artist
    alternate_artists = [key for key in load_mappings().keys() if load_mappings()[key] == artist]
    title = title.lower()
    title = title.replace(artist.lower(), "")
    for checked_artist in alternate_artists:
        title = title.replace(checked_artist.lower(), "")
    title = title.split("/")[-1]


    for separator in separators:
        artist = artist.replace(separator, ' ')
        title = title.replace(separator, ' ')
        album = album.replace(separator, ' ')
    if len(title) > len(album):
        title = re.sub(album.lower(), "", title, 1)
    title = re.sub('^[0-9 ]+', '', title)
    title = re.sub('^\.', '', title)
    title = title.strip().capitalize()
    if verbose:
        print("guess title is: "+title)

    artist = artist.capitalize()
    title = title.capitalize()
    album = album.capitalize()
    return {'title': title, 'artist': artist, 'album': album,
            'separator': candidates[0]}


def copy_dir(foldername=None):
    # remove the last /, if it exists
    if foldername[-1] == '/':
        foldername = foldername[:-1]
    foldername = os.path.expanduser(foldername)
    new_foldername = foldername+"-copy"
    # copy the folder so that we can work on it without worry
    # this will delete the existing copy
    if os.path.isdir(new_foldername):
        rmtree(new_foldername)
    copytree(foldername, new_foldername)
    return new_foldername


def get_music(new_foldername):
    # recursively walk through the directory structure
    # if an mp3 is found, add it to the list of tracks for that folder
    # if an image is found, save it as the thumbnail for that folder
    mp3_lists = defaultdict(list)

    path_images = {}

    def add_file(name, root):
        if fnmatch(name.lower(), "*.mp3") or fnmatch(name.lower(), ".m4a"):
            mp3_lists[_dir].append(os.path.join(root, name))
        if fnmatch(name.lower(), "*.jpg") or fnmatch(name.lower(),
                                                     "*.jpeg"):
            thumbnail_file = os.path.join(root, 'thumb.jpg')
            os.rename(os.path.join(root, name), thumbnail_file)
            path_images[_dir] = thumbnail_file

    for root, dirs, files in os.walk(new_foldername):
        for name in files:
            _dir = root
            # ignore hidden files
            if name[0] == '.':
                continue
            add_file(name, root)
            if fnmatch(name.lower(), "*.zip"):
                # unzip the directory
                z = zipfile.ZipFile(os.path.join(root, name))
                for f in z.namelist():
                    z.extract(f, root)
                    add_file(f, root)

    return {'mp3': mp3_lists, 'images': path_images}


def reorganize_music(root, mp3_lists):
    """
    reorganize the music collection based on the format artist/album/track.mp3
    :param root: the new foldername
    :param _mp3_list: the list of mp3 paths
    :return:
    """
    for _path in mp3_lists.keys():
        for _mp3_file in mp3_lists[_path]:
            # update the metadata for the mp3
            _audiofile = load(_mp3_file)
            if _audiofile.tag.album is None or _audiofile.tag.artist is None:
                print("warning: not able to place file: "+_mp3_file)
                continue
            artist = _audiofile.tag.artist
            album = _audiofile.tag.album
            directory = os.path.join(root, artist, album)
            if not os.path.exists(directory):
                os.makedirs(directory)

            # there's some funky behavior with this line regarding files with unicode characters
            new_filename = os.path.join(directory, os.path.basename(_mp3_file.decode('utf-8')))
            copyfile(_mp3_file, new_filename)


def make_cover_folder(album, artist):
    # first, check to see whether the file already exists in the covers
    cover_location = os.path.expanduser("~/covers")
    if not os.path.exists(cover_location):
        os.makedirs(cover_location)
    cover_filename = os.path.join(cover_location, album+"_"+artist+".jpg")
    return cover_filename


def get_image(album="", artist="", search=True):
    print("getting image from web")
    cover_filename = make_cover_folder(album, artist)
    if (not os.path.exists(cover_filename)) and search:
        # first, search xbox live
        cover_filename = None
        try:
            cover_filename = xboxlive_image_search(album, artist)
        except Exception as e:
            print("xbox failed for reason: "+str(e))

        if cover_filename is None:
            cover_filename = google_image_search(album, artist)
        return cover_filename
        
    elif not os.path.exists(cover_filename):
        fhandle = open(cover_filename, 'a')
        fhandle.close()
        return cover_filename
    else:
        return cover_filename


def convert_files(root, cuesheet=None, thumbnail_filename=None):
    # convert the other flacs to mp3
    curr_dir_files = sorted(os.listdir(root))
    current_track = 0
    for _file in curr_dir_files:
        if fnmatch(_file, '*.flac'):
            in_flac = os.path.join(root,_file)
            out_mp3 = in_flac.replace('flac', 'mp3')
            avconv = ('avconv', '-i', "\""+in_flac+"\"", '-qscale:a', '0',
                      "\"" +out_mp3+"\"")
            call(" ".join(avconv), shell=True)

            _flac_audio = FLAC(in_flac)

            # update the metadata for the mp3
            _audiofile = load(out_mp3)
            if thumbnail_filename is not None:
                _audiofile.tag.images.set(0x03, thumbnail_filename, 'jpg')
            elif len(_flac_audio.pictures) >0:
                _audiofile.tag.images.set(0x03, _flac_audio.pictures[0], 'jpg')

            if cuesheet is not None:
                _audiofile.tag.artist = unicode(cuesheet.performer)
                _audiofile.tag.album = unicode(cuesheet.title)
                _audiofile.tag.title = unicode(cuesheet.tracks[current_track])
            else:
                _audiofile.tag.artist = _flac_audio.tags['Artist'][0]
                _audiofile.tag.album = _flac_audio.tags['Album'][0]
                _audiofile.tag.title = _flac_audio.tags['Title'][0]
            _audiofile.tag.track_num = current_track+1
            _audiofile.tag.save()
            current_track += 1
            # move the flac to the trash
            send2trash(os.path.join(root, _file))
        if fnmatch(_file, '*.m4a'):
            in_flac = os.path.join(root, _file)
            out_mp3 = in_flac.replace('m4a', 'mp3')
            parts = ('avconv','-i', in_flac, '-qscale:a', '0',
                             out_mp3)
            print(' '.join(parts))
            call(parts)
            _mp4_audio = MP4(in_flac)
            # update the metadata for the mp3
            _audiofile = load(out_mp3)
            if thumbnail_filename is not None:
                _audiofile.tag.images.set(0x03, thumbnail_filename, 'jpg')
            if cuesheet is not None:
                _audiofile.tag.artist = unicode(cuesheet.performer)
                _audiofile.tag.album = unicode(cuesheet.title)
                _audiofile.tag.title = unicode(cuesheet.tracks[current_track])

            else:
                _audiofile.tag.artist = _mp4_audio['\xa9ART'][0]
                _audiofile.tag.album = _mp4_audio['\xa9alb'][0]
                _audiofile.tag.title = _mp4_audio['\xa9nam'][0]
            _audiofile.tag.track_num = current_track+1
            _audiofile.tag.save()
            current_track += 1
            # move the flac to the trash
            send2trash(os.path.join(root, _file))
        if fnmatch(_file, '*.wma'):
            in_flac = os.path.join(root, _file)
            out_mp3 = in_flac.replace('wma', 'mp3')
            parts = ('avconv','-i', in_flac, '-qscale:a', '0',
                             out_mp3)
            call(parts)
            # update the metadata for the mp3
            _audiofile = load(out_mp3)
            if thumbnail_filename is not None:
                _audiofile.tag.images.set(0x03, thumbnail_filename, 'jpg')
            if cuesheet is not None:
                _audiofile.tag.artist = unicode(cuesheet.performer)
                _audiofile.tag.album = unicode(cuesheet.title)
                _audiofile.tag.title = unicode(cuesheet.tracks[current_track])

            _audiofile.tag.track_num = current_track+1
            _audiofile.tag.save()
            current_track += 1
            # move the flac to the trash
            send2trash(os.path.join(root, _file))


def google_image_search(album, artist):
    if not build:
        print("googleapi not available")
        return None
    cover_filename = make_cover_folder(album, artist)
    key = os.environ.get('GOOGLE_API_KEY')
    service = build("customsearch", "v1", developerKey=key)
    query = album+"+"+artist
    print("searching web for: "+query)
    try:
        res = service.cse().list(
            q=query, cx="015111312832054302537:ijkg6sdfkiy", searchType='image',
            num=10, ).execute()
    except Exception as e:
        print("Google search failed for reason: "+str(e))
    time.sleep(1.5)
    images = []
    print(res.items())
    for i in range(0, min(10, len(res.items()))):
        item = res['items'][i]
        _image = urllib.urlretrieve(item['link'])
        print(_image)
        images.append(_image[0])
    return images


def xboxlive_image_search(album, artist):
    cover_filename = make_cover_folder(album, artist)
    service = "https://datamarket.accesscontrol.windows.net/v2/OAuth2-13"

    # you will need to generate your own client id and key in Azure
    clientId = "chusic"
    clientSecret = os.environ.get('BING_API_KEY')
    print(clientSecret)
    post_data = {"client_id": clientId, "client_secret": clientSecret,
                "scope": "http://music.xboxlive.com",
                "grant_type": "client_credentials"}

    data = urllib.urlencode(post_data)
    req = Request(service, data)
    print(req)
    response = urlopen(req)
    response_string = response.read()

    response_string = ast.literal_eval(response_string)
    token = urllib.quote_plus(response_string['access_token'])
    query = urllib.quote_plus(artist)
    music_url = "https://music.xboxlive.com/1/content/music/search?q" \
                "="+query+"&accessToken=Bearer+" + token
    print(music_url)
    try:
        request = Request(music_url)
        response = urlopen(request)
    except Exception as e:
        raise Exception("xboxlive music request failed for reason: "+str(e)+"\n on url: "+music_url)
    literal_data = response.read()
    literal_data = literal_data.replace(":false", ":False")
    literal_data = literal_data.replace(":true", ":True")

    data = ast.literal_eval(literal_data)
    for _album in data['Albums']['Items']:
        if album.find(_album['Name']) >=0:
            for _artist in _album['Artists']:
                if artist.find(_artist['Artist']['Name'])>=0:
                    temp_filename = wget.download(_album['ImageUrl'], out=cover_filename)
                    return temp_filename

