#!/usr/bin/env python

import optparse
import urllib
import urllib2
import json
import os
import re

def parse_commandline_arguments():
    parser = optparse.OptionParser(usage="%prog [options] show_name")
    parser.add_option('-s', '--default-season', dest='default_season', help = 'default season number (for files without a season number in name)', default = 1)
    parser.add_option('-y', '--year', dest='year', help = 'year the show was produced, helps with show name conflicts')
    parser.add_option('-d', '--dry-run', action="store_true", dest='dry_run', help = 'application will only print out the renames', default = True)
    parser.add_option('-r', '--rename', action="store_false", dest='dry_run', help = 'application will rename the files')
    options, arguments = parser.parse_args()
    if not arguments:
        parser.error("You must supply the show name")
    return (options, arguments)

def download_episode_list(show_name, year):
    url = "http://imdbapi.poromenos.org/js/?name="+urllib.quote(show_name)
    if year: url = url + "&year=" + year
    response = urllib2.urlopen(url, None, 30)
    return response.read()

def parse_episode_list(episodes_txt):
    return json.loads(episodes_txt)

def normalize_episode_list(show_name, episodes_hash):
    normalized_episodes = {}    
    episodes = []
    
    if episodes_hash.has_key('shows'):
        print "Could not find 'episodes' in hash. Try specifying a year (-y)"
        for show in episodes_hash['shows']:
            print "%s - %d" % (show['name'], show['year'])
    elif episodes_hash.values()[0].has_key('episodes'):
        episodes = episodes_hash.values()[0]['episodes']        
    else:
        print episodes
        print "Unknown response format"        
    
    for episode_description in episodes:
        season = int(episode_description['season'])
        number = int(episode_description['number'])
        name = episode_description['name']
        episode_number = "%02dx%02d" % (season, number)
        normalized_episodes[episode_number] = name
    
    return normalized_episodes

def get_episode_list(show_name, year):
    episodes_txt = download_episode_list(show_name, year)
    episode_list_hash = parse_episode_list(episodes_txt)
    if not episode_list_hash: return None
    return normalize_episode_list(show_name, episode_list_hash)

def get_files_in_current_directory():
    files = os.listdir('.')
    return [file for file in files if os.path.isfile(file)]

def get_episode_number(file_name, default_season):
    match = re.search("[sS]?(\d+)[eExX](\d+)", file_name)
    if match: return "%02dx%02d" % (int(match.group(1)), int(match.group(2)))
    match = re.search("(\d\d?)(\d\d)", file_name)
    if match: return "%02dx%02d" % (int(match.group(1)), int(match.group(2)))
    match = re.search("(\d\d).*(\d\d)", file_name)
    if match: return "%02dx%02d" % (int(match.group(1)), int(match.group(2)))    
    match = re.search("\d+", file_name)
    if match: return "%02dx%02d" % (default_season, int(match.group(0)))
    return None

def get_extension(file_name):
    return os.path.splitext(file_name)[-1]

def new_file_name(show_name, episode_number, title, extension):
    return remove_illegal_characters("%s - %s - %s%s" % (show_name, episode_number, title, extension))

def remove_illegal_characters(string):
    illegal_chars = '*/:<>?\|;"'
    for char in illegal_chars:
        string = string.replace(char, '')
    return string

def get_new_name(file_name, episode_list, default_season, show_name):
    episode_number = get_episode_number(file_name, default_season)
    if not episode_number: return None
    extension = get_extension(file_name)        
    return new_file_name(show_name, episode_number, episode_list[episode_number], extension) 

def rename_episode(file, new_name):
    if not new_name: return
    if file == new_name: return
    if os.path.exists(new_name):
        print "CONFLICT! File: '%s' exists" % (new_name)
    else:
        os.rename(file, new_name)

def renameable_files_in_current_directory(all_episodes, default_season, show_name):
    files = get_files_in_current_directory()
    for file in files:
        new_name = get_new_name(file, all_episodes, default_season, show_name)
        if new_name:
            yield (file, new_name)

def main():
    options, args = parse_commandline_arguments()
    show_name = args[0]
    default_season = int(options.default_season)
    year = options.year
    all_episodes = get_episode_list(show_name, year)
    dry_run = options.dry_run
    if not all_episodes:
        print "Could not find show: '%s' on IMDB" % (show_name)
        return
    if dry_run:
        print "Dry run: will not perform renames\n\n"
    nothing_to_rename = True
    for file, new_name in renameable_files_in_current_directory(all_episodes, default_season, show_name):
        nothing_to_rename = False
        print "'%s' => '%s'" % (file, new_name)        
        if not dry_run:        
            rename_episode(file, new_name)
    if nothing_to_rename:
        print "Could not find any episode to rename"

if __name__ == '__main__':
    main()