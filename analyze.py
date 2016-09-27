#!/usr/bin/python
# get music by age and count
from argparse import ArgumentParser
from operator import itemgetter
from os.path import expanduser

import sys
from eyed3 import load
from os import stat

from chusic import get_music

parser = ArgumentParser(description='Get ranking of bands by count number and '
                                    'age.')
parser.add_argument('--foldername', type=str, help='The foldername to search')

band_alternates = {'emerson, lake & palmer': 'emerson, lake & palmer',
                   'emerson lake & palmer': 'emerson, lake & palmer',
                   'f.o.e.s': 'f.o.e.s', 'foes': 'f.o.e.s',
                   'ghost b.c.': 'ghost'}

def main():
    args = parser.parse_args()
    args.foldername = expanduser(args.foldername)
    new_foldername = args.foldername
    # keep a list of all cues and flacs
    file_lists = get_music(new_foldername=new_foldername)
    band_ages = {}
    band_count = {}
    for files in file_lists['mp3'].keys():
        for file in file_lists['mp3'][files]:
            _created_time = stat(file).st_mtime
            _audiofile = load(file)
            _artist = _audiofile.tag.artist.strip().lower()
            # that one funky st vincent tag
            if _artist.find('st. vincent') == 0:
                _artist = 'st. vincent'
            if _artist in band_alternates.keys():
                _artist = band_alternates[_artist]
            if _artist not in band_ages.keys():
                band_ages[_artist] = _created_time
            elif _created_time < band_ages[_artist]:
                band_ages[_artist] = _created_time
            if _artist not in band_count.keys():
                band_count[_artist] = 1
            else:
                band_count[_artist] += 1

    ages_ranking_list = sorted(band_ages.items(), key=itemgetter(1))#.reverse()
    ages_ranking = {}
    ofh = open("rankings.csv", "w+")
    ofh.write("\nAges Ranking\n")
    ofh.write("Rank\tBand\n")
    rank = 1
    prev_val = ages_ranking_list[0][1]
    for i in range(len(ages_ranking_list)):
        print(abs(ages_ranking_list[i][1] - prev_val))
        if abs(ages_ranking_list[i][1] - prev_val) > 86400:
            rank += 1
            prev_val = ages_ranking_list[0][1]
        ofh.write(str(rank)+" "+ages_ranking_list[i][0].encode('utf8', 'replace').title()+"\n")
        ages_ranking[ages_ranking_list[i][0]] = rank

    count_ranking_list = sorted(band_count.items(), key=itemgetter(1))
    count_ranking_list.reverse()
    count_ranking = {}
    ofh.write("\nCount Ranking\n")
    ofh.write("Rank\tBand\tCount\n")
    rank = 1
    prev_val = count_ranking_list[0][1]
    for i in range(len(count_ranking_list)):
        if count_ranking_list[i][1] != prev_val:
            rank += 1
            prev_val = count_ranking_list[0][1]
        ofh.write(str(rank)+"\t"+count_ranking_list[i][0].encode('utf8', 'replace').title()+"\t"+str(count_ranking_list[i][1])+"\n")
        count_ranking[count_ranking_list[i][0]] = rank

    combined_rank = {}
    for key in band_ages.keys():
        combined_rank[key] = 0.5*ages_ranking[key] + count_ranking[key]

    print(combined_rank)
    combined_ranking_list = sorted(combined_rank.items(), key=itemgetter(1))
    print(combined_ranking_list)
    ofh.write("\nCombined Ranking\n")
    ofh.write("Rank\tBand\tCombined Rank\n")
    for i in range(len(combined_ranking_list)):
        ofh.write(str(i)+" "+combined_ranking_list[i][0].encode('utf8', 'replace').title()+"\t"+str(combined_ranking_list[i][1])+"\n")

    ofh.close()


if __name__ == "__main__":
    sys.exit(main())