#!/usr/bin/env python3

from models import YTVideo
from models import WikiTrack 

import scrapewiki as wiki
import ytdl
import match
import tagger as tag

import progressbar

import youtube_dl
import os
from termcolor import cprint
import sys
from multiprocessing.pool import ThreadPool

def main():
    pool = ThreadPool(processes=1)
    if not os.path.exists("/tmp/album-dl"):
        os.makedirs("/tmp/album-dl")

    yt_url = input("Enter youtube url:\n")
    # yt_url = "https://www.youtube.com/watch?v=avgiqNapUx0&list=PLcTz7Wlk_9U3Weklyt9mgcARhEJie4qMP"
    song_downloader = pool.apply_async(ytdl.song_titles, (yt_url, )) 
    print("Downloading youtube playlist metadata...")

    wiki_url = input("Enter wikipedia url:\n")
    # wiki_url = "https://en.wikipedia.org/wiki/Mer_de_Noms"

    try:
        wiki_page = wiki.capture_page(wiki_url)

        metadata = wiki.get_metadata(wiki_page)

        wiki.download_art(wiki_page)

        track_tables = wiki.get_track_tables(wiki_page)

        table_indicies = select_tables(track_tables)
        tracks = wiki.get_tracks(track_tables, table_indicies)

        print_metadata(metadata)
        print_tracks(tracks)

        while not confirm():
            print("What do you want to change?")
            print("[artist|album|year|genre|track ##]")
            k = input(": ").lower()
            if k in metadata:
                newval = input("New value for {}: ".format(k))
                metadata[k] = newval
            elif k.split()[0] == "track":
                num = k.split()[1]
                for track in tracks:
                    if num == track.num:
                        newval = input("New title for track {}: ".format(track.num))
                        track.title = newval
            else:
                print("Not a valid field.")

            print_metadata(metadata)
            print_tracks(tracks)


        print("Downloading youtube playlist metadata...")
        last_msg = ""
        current, total = ytdl.msg_status
        with progressbar.ProgressBar(max_value=total, widgets=[progressbar.Bar()]) as bar:
        # with tqdm(total=ytdl.msg_status[1], postfix="") as pbar:
            bar.update(current)
            while not song_downloader.ready():
                if ytdl.msg_status != last_msg:
                    current, total = ytdl.msg_status
                    bar.update(current)
                    # print("|{:<20}|".format((20*int(current)//int(total))*"*"))

        yt_song_titles = song_downloader.get()  

        mapping = match.mapTitlesToFiles(tracks, yt_song_titles) 

        print_mapping(mapping)
            
        if not confirm():
            exit()

        ytdl.download_songs(yt_url)

        new_names = tag.tag_songs(tracks, metadata, mapping)

        path = "/home/rutrum/music/{}/{}".format(metadata["artist"], metadata["album"])
        os.makedirs(path, exist_ok=True)
        
        for name in new_names:
            old_path = "/tmp/album-dl/{}.mp3".format(name["old"])
            new_path = "{}/{}.mp3".format(path, name["new"])
            os.rename(old_path, new_path)
        
        
    except Exception as ex:
        cprint(ex.args[0], "red", attrs=["bold"], file=sys.stderr)
        raise ex

def confirm():
    response = input("\nIs this correct? [Y/n] ")
    if response not in "Yy":
        return False
    else:
        return True

def select_tables(tables):
    if len(tables) > 1:
        print("Please enter which track tables you would like to use.")
        print("Please use space as delimeter, for example: 1 2")
        print("By default, all tables will be used, in order.")

        for (i, table) in enumerate(tables):
            print("***{:^14}***".format(i))
            for track in table:
                print("{:>3}. ".format(track.num), track.title)

        res = input("Track tables: ")
        selected_tracks = list(map(lambda x: int(x), res.split()))

        if len(selected_tracks) == 0:
            return list(range(len(tables)))

        for selection in selected_tracks:
            if selection > len(tables) or selection < 0:
                cprint("Please select valid tables.", "red")
                return select_tables(tables)
        
        return selected_tracks

    else:
        # Only found 1 table, return this
        return [0]

def print_mapping(mapping):
    print()
    cprint("{:>30}   {}".format("Song Title", "Video Title"), attrs=['bold'])
    for (key, val) in mapping.items():
        # Doesn't lookup when empty (string)
        # TODO
        if val:
            print("{:>30}   {}".format(key.title, val.title))
        else:
            print("{:>30}   {}".format(key.title, val))

def print_metadata(data):
    print()
    for key in data:
        print("{:>10}  ".format(key.capitalize()), data[key])

def print_tracks(tracks):
    print()
    for track in tracks:
        print("{:>3}. ".format(track.num), track.title)

if __name__ == "__main__":
    main()
