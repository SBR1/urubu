#!/usr/bin/env python3


"""Function for getting data out of photobucket for use in a website."""

import json
import logging
import re
import urllib.request
from html.parser import HTMLParser


# Defines the sort=_ value for different types of sort.
sort_types = {"oldest first": 2, "newest first": 3, "title": 4, "filename": 9}


class PhotobucketPageParser(HTMLParser):
    """Parses a photobucket page to extract token, album info and image info.
    
    It will return a chronological (by upload) list of dictionaries with the
    following keys:
        thumbnail: URL where the tumbnail can be downloaded.
        direct: URL to the full size image.
        title: title in photobucket, "
        description: description in photobucket.
    """

    def __init__(self):
        super().__init__()
        self.isscript = False
        self.token = None
        self.album = None
        self.images = []
        
    def handle_starttag(self, tag, attrs):
        """Looks if it the token or a script tag."""
        if tag.lower() == "input":
            # <input type="hidden" name="token" id="token" value="17eb8f26d242585220675e11f631d656" />
            istoken = False
            tokenvalue = None
            for (key, value) in attrs:
                if key == "id":
                    istoken = True
                if key == "value":
                    tokenvalue = value
            if istoken:
                self.token = tokenvalue
        if tag.lower() == "script":
            self.isscript = True
            for (key, value) in attrs:
                if key.lower() == "src":
                    # Ignoring external javascript loaded instead of inlined.
                    self.isscript = False

    def handle_data(self, data):
        """If we're in a script tag it looks for the json for album and image info."""
        album_marker = "var albumJson = " # ";"
        image_marker = "Pb.Data.add('libraryAlbumsPageCollectionData',"
        image_data_marker = "collectionData:"
        isimagescript = False
        for line in data.split("\n"):
            if isimagescript:
                try:
                    start = line.index(image_data_marker) + len(image_data_marker)
                    end = line.rindex(",")
                    length = end-start
                    logging.debug("Found image json:  %s-%s (%s)" % (start, end, length))
                    json_data = line[start:end]
                    x = json.loads(json_data)
                    self.images.append(x)
                except ValueError:
                    # Not found what we are looking for
                    pass
            elif image_marker in line:
                isimagescript = True
            else:
                try:
                    start = line.index(album_marker) + len(album_marker)
                    end = line.rindex(";")
                    length = end-start
                    logging.debug("Found album json:  %s-%s (%s)" % (start, end, length))
                    json_data = line[start:end]
                    self.album = json.loads(json_data)
                    logging.debug(self.album)
                except ValueError:
                    # Not found what we are looking for
                    pass

    def handle_enttag(self, tag):
        self.isscript = False


def download_page(url):
    """Downloads the page into memory."""
    logging.info("Getting %s..." % (url))
    return urllib.request.urlretrieve(url)
    
    
def process_album(base_url, sort = None, page = None, images = None):
    """Processes a (sub)album page (and the next if necessary)."""
    if images == None:
        images = [] # Need the order, so a list.
    previous_count = len(images)
    if sort == None:
        sort = sort_types["newest first"]
    else:
        sort = int(sort)
    if page == None:
        page = 1
    else:
        page = int(page)
    url = "%s?sort=%s&page=%s" % (base_url, sort, page)
    try:
        (content_filename, httpmessage) = download_page(url)
        logging.debug("Download result: %s" % (httpmessage))
        ppp = None
        try:
            ppp = PhotobucketPageParser()
            for line in open(content_filename, 'r', encoding="utf-8"):
                ppp.feed(line)
            video_count = 0
            image_count = 0
            item_count = 0
            subalbums = {}
            for key in ppp.album:
                if key ==  "ablumStats":
                    for var in ppp.album[key]:
                        if var == "subalbums":
                            # TODO
                            # Example of when there are no sub-albums
                            #   'subalbums': {'display': '0 sub-albums', 'count': 0}
                            pass
                        elif var == "images":
                            image_count = ppp.album[key][var]["count"]
                            logging.info("Image count: %s" % (image_count))
                        elif var == "videos":
                            video_count = ppp.album[key][var]["count"]
                            logging.info("Video count: %s" % (video_count))
            for image in ppp.images:
                for key in image:
                    logging.debug("%s: %s" % (key, type(image[key])))
                    if key == "items":
                        for item in image[key]:
                            logging.debug("\t%s: %s" % (item, type(image[key][item])))
                            if item == "total":
                                item_count = image[key][item]
                            elif item == "objects":
                                for iobject in image[key][item]:
                                    thumburl = None
                                    origurl = None
                                    description = None
                                    title = None
                                    logging.debug("\t\t%s" % (type(iobject)))
                                    for okey in iobject:
                                        logging.debug("\t\t%s: %s" % (okey, type(iobject[okey])))
                                        if okey == "thumbUrl":
                                            thumburl = iobject[okey]
                                        elif okey == "orig":
                                            origurl = iobject[okey]
                                        elif okey == "description":
                                            description = iobject[okey]
                                        elif okey == "title":
                                            title = iobject[okey]
                                        elif okey == "linkcodes":
                                            if "direct" in iobject[okey]:
                                                directurl = iobject[okey]["direct"]
                                    images.append({"thumbnail": thumburl,
                                                   "direct" : directurl, 
                                                   "original": origurl, 
                                                   "title": title, 
                                                   "description": description})
        finally:
            try:
                ppp.close()
            except:
                pass
        if len(images) == previous_count:
            # Something went wrong, this run didn't result in any extra images!
            # Perhaps I should raise here instead of going silent.
            logging.error("Premature end of process_album(): I couldn't get all images.")
            return images
        if len(images) < item_count:
            # All the images found isn't enough, so move onto the next page.
            process_album(base_url, sort, page+1, images)
    except urllib.error.HTTPError as he:
        logging.error("HTTP Error: %s" % he)
    except OSError as oe:
        logging.error("OS Error: %s" % oe)
    finally:
        logging.debug("Item count: %s reported, %s found." % (item_count, len(images)))
        return images


def filter_images(images, criteria = "title"):
    """Filters the images based on if a property is set."""
    # There might be a oneliner that replaces this function but
    # I'm lazy so I just say: "Explicit is better then implicit."
    result = []
    for image in images:
        try:
            if len(image[criteria]) > 0:
                result.append(image)
        finally:
            pass
    return result


if __name__ == "__main__":
    # Stuff for testing purposes and shows you how to use it.
    logging.basicConfig(level = logging.INFO)
    node = "s205"
    username = "schilduil"
    album = urllib.parse.quote("Exhibition Budgerigars/Season 2016 bred")
    base_url = "http://%s.photobucket.com/user/%s/library/%s" % (node, username, album)
    
    images = process_album(base_url)
    
    print()
    title_images = filter_images(images)
    print("Images (%s/%s):" % (len(title_images),len(images)))
    for image in title_images:
        print("\t%s" % (image["title"]))

