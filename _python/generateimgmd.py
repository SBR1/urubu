#!/usr/bin/env python3


import hashlib
import json
import os.path
import shutil
import urllib.parse

import photobucket


markdown_header = """---
title: %s
layout: page
pager: true
---

"""


def read_config(filename = None):
    if filename == None:
        filename = "../_data/photobucket.json"
    with open(filename) as json_file:
        return json.load(json_file)


def create_thumb_filename(directurl, thumburl):
    return hashlib.sha1(directurl.encode("utf-8")).hexdigest() + '.' + thumburl.rsplit(".",1)[-1].split("~")[0]
    
    
def process(url, markdown_file, title, thumbpath = None, rel = None):
    if rel == None:
        rel = ".."
    if thumbpath == None:
        thumbpath = "img/thumbs"
    localpath = os.path.realpath(os.path.join(rel, thumbpath))
    os.makedirs(localpath, exist_ok=True)
    if not markdown_file.startswith("/"):
        markdown_file = os.path.realpath(os.path.join(rel, markdown_file))
    os.makedirs(os.path.dirname(markdown_file), exist_ok=True)
    # First getting the info from Photobucket (only those with a title).
    images = photobucket.filter_images(photobucket.process_album(base_url))
    image_link = """[![%s](/""" + thumbpath + """/%s)](%s){:target="_blank"}\n""" # % (title, thumb_filename, url)
    with open(markdown_file, 'w') as mdfh:
        mdfh.write(markdown_header % (title))
        for image in images:
            thumb_filename = create_thumb_filename(image["direct"], image["thumbnail"])
            thumb_fullpath_filename = os.path.join(localpath, thumb_filename)
            if not os.path.isfile(thumb_fullpath_filename):
                # Download it.
                print("Downloading %s as %s..." % (image["thumbnail"], thumb_fullpath_filename))
                # Download the file from `url` and save it locally under `file_name`:
                with urllib.request.urlopen(image["thumbnail"]) as response, open(thumb_fullpath_filename, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
            mdfh.write(image_link % (image["title"], thumb_filename, image["direct"]))


if __name__ == "__main__":
    config = read_config()
    for location in config:
        base_url = "http://%s.photobucket.com/user/%s/library/%s" % (
            location["node"], 
            location["username"], 
            urllib.parse.quote(location["album"])
        )
        if "status" in location:
            if location["status"] == "generate":
                process(base_url, location["path"] + ".md", location["title"])
    # TODO: generate the index.md also inside those directories.

