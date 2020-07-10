import re
import time
import json
import requests
from pathlib import Path

import click
from tqdm import tqdm
import pandas as pd
from splinter import Browser
from bs4 import BeautifulSoup

root = Path.cwd().parent.absolute()
main_url = 'https://www.ispot.tv/browse'
base_url = 'https://www.ispot.tv'

def get_links(url):
    ''' Get all the links from a landing/browse page '''
    soup2 = BeautifulSoup(requests.get(url).content, 'html.parser')
    links = [a['href'] for a in soup2.select("div.thumbnail-title a")]
    return links

def get_adpage_info(ad_url, browser):
    ''' Get the data from a single ad page'''

    def get_meta(fields, browser=browser):
        ''' Get the mood from the page '''
        meta={}
        for row in browser.find_by_css('#meta-data div.row'):
            cells = row.find_by_tag('div')
            field = cells[0].text.strip().lower()
            if field in fields:
                meta[field] = cells[1].text.strip()
        return meta

    def get_video(browser=browser):
        ''' Get the video object'''
        vlist = browser.find_by_css('#my-video video')
        if len(vlist):
            return vlist[0]

    # Coerce url
    if ad_url.startswith('/ad'):
        ad_url = base_url+ad_url

    data = {}
    browser.visit(ad_url)

    # Heading and subheading
    heading = browser.find_by_css('.grid-video h1')[0]
    data['title'] = heading.text

    subheading = browser.find_by_css('.grid-video')[0].find_by_tag('div')[-2].text
    subheading_data = re.search(r"Ad ID: (?P<id>\d+)\s+(?P<runtime>\d+)s \s+ (?P<year>\d{4})", subheading).groupdict()

    data.update(subheading_data)

    meta_fields = ['advertiser', 'mood', 'characters', 'animals', 'products']
    data.update(get_meta(meta_fields))


    video = get_video()
    if not video:
        time.sleep(4)
        video = get_video()
    if not video:
        return None
    data['video_url'] = video._element.get_attribute('src')

    return data


@click.command()
@click.argument('url')
@click.argument('dir_name')
def main(url, dir_name):
    # Initialise browser
    br = Browser('chrome', headless=True)

    # Create output directory
    new_dir = root/'data'/dir_name
    if not new_dir.exists():
        new_dir.mkdir()

    # Get links
    links = get_links(url)

    # Pull info
    for link in tqdm(links, desc="Scraping ad pages..."):
        try:
            data = get_adpage_info(link, br)
            if not data:
                continue
            fname = data['id'] + '.json'

            with open(new_dir/fname, 'w+', encoding="utf-8") as wfile:
                json.dump(data, wfile)
        except:
            pass


if __name__ == '__main__':
    main()
