#!/usr/bin/python
# get music by age and count
from argparse import ArgumentParser
from operator import itemgetter
from os.path import expanduser
from re import split
import sys
from eyed3 import load
from os import stat

from chusic import get_music

# does not currently work for python3 due to eye3d tags arg!!!
parser = ArgumentParser(description="Get ranking of bands by count number and "
                                    "age, or compare two generated rankings.")
parser.add_argument('--foldername', type=str, help="The foldername to search")
parser.add_argument('--alternate', type=str, help="An alternate foldername, "
                                                   "for completeness of history")
parser.add_argument('--compare', type=str, metavar="OLD_RANKING,NEW_RANKING",
                    help="Compare two generated ranking files.")

band_alternates = {'emerson, lake & palmer': 'emerson, lake & palmer',
                   'emerson lake & palmer': 'emerson, lake & palmer',
                   'f.o.e.s': 'f.o.e.s', 'foes': 'f.o.e.s',
                   'ghost b.c.': 'ghost', u'mg\u0142a': 'mgla'}


def map_age_count(file_lists):
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
    return [band_ages, band_count]


def rank(args):
    args.foldername = expanduser(args.foldername)
    alt_foldername = args.alternate
    new_foldername = args.foldername
    # keep a list of all cues and flacs
    [band_ages, band_count] = map_age_count(get_music(new_foldername=new_foldername))
    if alt_foldername is not None:
        [alt_ages, _] = map_age_count(get_music(new_foldername=alt_foldername))
    else:
        alt_ages = {}
    for band in band_ages.keys():
        if band in alt_ages.keys():
            band_ages[band] = alt_ages[band]

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
    combined_ranking_list = sorted(combined_rank.items(), key=itemgetter(1))
    ofh.write("\nCombined Ranking\n")
    ofh.write("Rank\tBand\tCombined Rank\n")
    for i in range(len(combined_ranking_list)):
        ofh.write(str(i)+" "+combined_ranking_list[i][0].encode('utf8', 'replace').title()+"\t"+str(combined_ranking_list[i][1])+"\n")

    ofh.close()


def read_ranking(lines):
    combined_ranking = lines.split("Combined Rank\n")[1].split('\n')
    rankings = dict()
    for line in combined_ranking:
        parts = split("\s", line)
        print(parts)
        if len(parts) > 2:
            band = " ".join(parts[1:-1])
            rankings[band] = float(parts[0])
    print(rankings)
    return rankings


def main():
    args = parser.parse_args()
    if args.foldername is not None:
        rank(args)
    if args.compare is not None:
        first_filename = args.compare.split(",")[0]
        second_filename = args.compare.split(",")[1]
        first_lines = open(first_filename, "r").read(-1)
        second_lines = open(second_filename, "r").read(-1)
        old_rankings = read_ranking(first_lines)
        new_rankings = read_ranking(second_lines)
        all_bands = set(old_rankings.keys() + new_rankings.keys())
        print(all_bands)
        changes = dict()
        new_bands = dict()

        for band in all_bands:
            if band not in old_rankings.keys():
                new_bands[band] = new_rankings[band]
                changes[band] = len(new_rankings.keys()) - new_rankings[band]
            elif band not in new_rankings.keys():
                changes[band] = old_rankings[band] - len(old_rankings.keys())
            else:
                changes[band] = old_rankings[band] - new_rankings[band]

        fh = open("ranking_changes.csv", "w")
        fh.write("New Bands\n")
        sorted_new = sorted(new_bands.items(), key=itemgetter(1))
        for new_band in sorted_new:
            fh.write(str(new_band)+"\n")
        fh.write("\nChanged Ranks\n")

        sorted_changes = sorted(changes.items(), key=itemgetter(1))
        for band in sorted_changes:
            fh.write(str(band)+"\n")
        fh.close()

if __name__ == "__main__":
    sys.exit(main())