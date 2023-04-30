
import json
import re
import random
import urllib.parse
import pickle
import requests
from time import sleep
from multiprocessing.connection import wait
from .scraper import Scraper
from .log import Log
from .DeckMember import DeckMember
from .Deck import Deck
from .queries import get_unseen, save_deck, deck_exists
from bs4 import BeautifulSoup
import random
import psycopg2
import time

log = Log("DECK SCRAPER", 0).log
searchUnseen = True
maxTop8 = 200

# TODO: Make this variable dependant
urls = [
    #{"parent": 'https://www.mtgtop8.com/', "url": "format_limited"},
    #{"parent": 'https://www.mtgtop8.com/', "url": "format?f=PAU"},
    #{"parent": 'https://www.mtgtop8.com/', "url": "format?f=PEA"},
    #{"parent": 'https://www.mtgtop8.com/', "url": "format?f=MO"},
    #{"parent": 'https://www.mtgtop8.com/', "url": "format?f=PI"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=ST"}
]


class DeckScraper:
    def __init__(self):
        self.db = psycopg2.connect("host=localhost dbname=magic user=magic password=magic")
        self.start_urls = urls
        self.to_scrape = []
        self.seen = []
        #self.service = DeckService()
        self.spider_search = False

    def prime(self):
        pickle.dump({"to_scrape": []}, open("./models/pickledLinks.p", "wb"))

    def build(self):
        self.spider_search = True
        print("Is spider searching")
        for u in self.start_urls:
            time.sleep(10)
            url = u['parent'] + u['url']
            try:
                raw_html = Scraper(url).simple_get()
                html = BeautifulSoup(raw_html, 'html.parser')
                if u['parent'].find('mtgtop8') >= 0:
                    for link in html.find_all('a',  href=True):
                        if 'archetype' in link['href']:
                            time.sleep(3)
                            self.getMtgTop8Links(link)
            except Exception as e:
                log(2, f"Unavailable url: {url}")
                raise(e)

        random.shuffle(self.to_scrape)
        log(0, "Done building")

    def primeFromDB(self):
        names = []
        try:
            if searchUnseen:
                names = get_unseen(self.db)
                random.shuffle(names)
            #else:
                #resp = self.service.get_cards()
                #names = [x["name"] for x in resp["body"]]
                #random.shuffle(names)
            #log(0, "Names: " + str(names))
        except:
            log(0, "Issue connecting to the database")

        for name in names:
            self.getMtgTop8Prime(name)

        random.shuffle(self.to_scrape)
        return self.to_scrape

    def getMtgTop8Prime(self, searchStr):
        body = {
            "compet_check[P]": 1,
            "compet_check[M]": 1,
            "compet_check[C]": 1,
            "compet_check[R]": 1,
            "MD_check": 1,
            "SB_check": 1,
            "cards": searchStr
        }

        raw_html = requests.post("https://www.mtgtop8.com/search", json=body)
        html = BeautifulSoup(raw_html.text, 'html.parser')
        count = 0
        for nlink in html.select('a'):
            if 'href' in nlink and nlink['href'].find('event?e') >= 0:
                added = self.add_to_scrape_pool(
                    nlink['href'], 'https://www.mtgtop8.com/')
                if added:
                    count += 1

        log(0, f"Found {count} links for {searchStr} in mtgTop8")

    def getMtgTop8Links(self, link):
        if len(self.to_scrape) < maxTop8:
            url = 'https://www.mtgtop8.com/' + link['href']
            raw_html = Scraper(url).simple_get()
            html = BeautifulSoup(raw_html, 'html.parser')

            for nlink in html.find_all('a',  href=True):
                urlVal = nlink['href']
                if nlink['href'].find('event?e') >= 0:
                    self.add_to_scrape_pool(
                        urlVal, 'https://www.mtgtop8.com/')

    def generate_card_pool(self, lock=None):
        popped = self.to_scrape.pop()
        url = popped["parent"] + popped['url']
        deck = []
        ret = False
        if deck_exists(self.db, url) != None:
            self.seen.append(url)
            return ret

        raw_html = Scraper(url).simple_get()
        log(0, f"Got: {url}")
        if raw_html:
            html = BeautifulSoup(raw_html, 'html.parser')
            if popped['parent'] == 'https://www.mtgtop8.com/':
                deck = self.processMtgTop8(html)
                if url in self.seen:
                    log(0, f"Seen: {url}")
                    return ret
                if len(deck) == 0 or url in self.seen:
                    return ret

        if (lock != None):
            lock.acquire()
            self.seen.append(url)
            lock.release()
        else:
            self.seen.append(url)

        deck_obj = Deck(url, url)
        for member in deck:
            deck_obj.add_member_to_deck(member)
        deck_size = deck_obj.get_deck_size()[1]

        if deck_size >= 40 and deck_size < 160:
            ret = self.saveToDB(deck_obj)
            random.shuffle(self.to_scrape)
        sleep(.5)
        return ret

    def processMtgTop8(self, html):
        members = html.find_all("div", attrs={"class": "deck_line"})
        deck = []
        try:
            for item in members:
                count = item.contents[0].strip()
                name = item.find("span", attrs={"class": "L14"}).contents[0]
                card_id = item.get('id')[2:]
                is_sideboard = item.get('id')[:2] == "sb"
                deck_member = DeckMember(is_sideboard, name, card_id, count)
                deck.append(deck_member)
        except Exception as e:
            log(0, "Failure to parse cards")
            log(0, e)
            return

        if not self.spider_search:
            return deck

        added = []
        for nlink in html.find_all('a',  href=True):
            boolval = '?e=' in nlink['href']
            urlVal = nlink['href']

            parsedVal = 'https://www.mtgtop8.com/event' + urlVal
            if boolval and parsedVal not in self.seen and parsedVal not in added:
                added.append(parsedVal)
                self.add_to_scrape_pool(
                    "event" + urlVal, 'https://www.mtgtop8.com/')

        return deck

    def saveToDB(self, deck):
        try:
            save_deck(self.db, deck)
            return True
        except:
            return False

    def add_to_scrape_pool(self, link, parent_domain):
        new_url = link
        if new_url not in self.seen and new_url not in [e['url'] for e in self.to_scrape]:
            self.to_scrape.append(
                {'url': link, 'parent': parent_domain}
            )
            if len(self.to_scrape) % 100 == 0:
                log(0, f"To Scrape: {len(self.to_scrape)}, adding {new_url}")
                pickle.dump({"to_scrape": self.to_scrape},
                            open("./models/pickledLinks.p", "wb"))
            return True
        return False


if __name__ == "__main__":
    dS = DeckScraper()
    dS.prime()
    dS.build()
    while len(dS.to_scrape):
        dS.generate_card_pool()
        time.sleep(3)
