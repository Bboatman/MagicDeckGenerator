from scraper import Scraper
from bs4 import BeautifulSoup
from importlib import import_module
import http.client
import json
import re
from mtgsdk import Card
import random
import time
import pickle

urls = [{"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/standard/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/pauper/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/modern/"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=LE"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=MO"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=ST"}]

class DeckScraper:
    def __init__(self, vectorizor):
        self.start_urls = urls
        self.to_scrape = []
        self.seen = []
        self.vectorizor = vectorizor

    def prime(self):
        pickle.dump( {"seen" : [], "to_scrape": []}, open( "./models/pickledLinks.p", "wb" ) )

    def build(self):
        for u in self.start_urls:
            url = u['parent'] + u['url']
            raw_html = Scraper(url).simple_get()
            html = BeautifulSoup(raw_html, 'html.parser')
            if u['parent'].find('tappedout') >= 0:
                for link in html.select('a'):
                    if link['href'].find("/mtg-decks/") >= 0:
                        self.add_to_scrape_pool(link['href'], 'http://tappedout.net')
                    elif link['href'].find("mtg-decks/") >= 0:
                        self.add_to_scrape_pool(link['href'], 'http://tappedout.net/')
            elif u['parent'].find('mtgtop8') >= 0:
                for link in html.select('a'):
                    if link['href'].find('archetype') >= 0:
                        self.getMtgTop8Links(link)
        random.shuffle(self.to_scrape)
        print("Done building")

    def getMtgTop8Links(self, link):
            url = 'https://www.mtgtop8.com/' + link['href']
            raw_html = Scraper(url).simple_get()
            html = BeautifulSoup(raw_html, 'html.parser')

            for nlink in html.select('a'):
                if nlink['href'].find('event?e') >= 0:
                    self.add_to_scrape_pool(nlink['href'], 'https://www.mtgtop8.com/')
                

    def generate_card_pool(self):
        popped = self.to_scrape.pop()
        url = popped["parent"] + popped['url']

        if url in self.seen:
            return
        else:
            self.seen.append(url)
            raw_html = Scraper(url).simple_get()
            deck = []
            if raw_html:
                html = BeautifulSoup(raw_html, 'html.parser')
                if popped['parent'] == 'http://tappedout.net':
                    deck = self.processTappedOut(html)
                if popped['parent'] == 'https://www.mtgtop8.com/':
                    deck = self.processMtgTop8(html)

            #print(len(deck))
            #if len(deck) < 50 and len(deck) > 0:
                #self.saveToDB(url, deck)
            if len(self.to_scrape) > 0:
                return

    def processMtgTop8(self, html):
        c = html.find_all("td", attrs={"class": "G14"})
        deck = []
        if not c and len(self.to_scrape) > 0:
            return []
        else:
            for entry in c:
                count = entry.find("div").contents[0].strip()
                name = entry.find("span").contents[0]
                card_id = self.get_id_for_card(name)
                deck.append(DeckMember(name, card_id, count))

        similar_decks = html.select("div.S14 a")
        for nlink in similar_decks:
            if nlink['href'].find('event?e=') >= 0:
                self.add_to_scrape_pool(nlink['href'], 'https://www.mtgtop8.com/')
            elif nlink['href'].find('?e=') >= 0:
                self.add_to_scrape_pool( 'event' + nlink['href'], 'https://www.mtgtop8.com/')
        
        return deck


    def processTappedOut(self, html):
        members = html.select('li.member a.qty.board')
        deck = []
        if not members and len(self.to_scrape) > 0:
            return []
        else :
            for item in members:
                name = item["data-orig"]
                card_id = self.get_id_for_card(name)
                count = item["data-qty"]
                deck.append(DeckMember(name, card_id, count))

        similar_decks = html.select("a.name")
        for link in similar_decks:
            if link['href'].find("/mtg-decks/") >= 0:
                self.add_to_scrape_pool(link['href'], 'http://tappedout.net')
            elif link['href'].find("mtg-decks/") >= 0:
                self.add_to_scrape_pool(link['href'], 'http://tappedout.net/')

        return deck
        

    def saveToDB(self, name, deck):
        headers = {'Content-type': 'application/json'}
        name = re.sub(r"[']", "", name)
        body = {"name" : name, "deckArray" : list(map(lambda x: x.asDict(), deck))}

        conn = http.client.HTTPConnection('magic-deck-generator.herokuapp.com')
        #conn.request('POST', '/deck', json.dumps(body), headers)
        #response = conn.getresponse()
        print(name)
        #print(response.read().decode())

    def add_to_scrape_pool(self, link, parent_domain):
        new_url = link
        if new_url not in self.seen and new_url not in [ e['url'] for e in self.to_scrape ] :
            self.to_scrape.append(
                {'url': link, 'parent': parent_domain}
            )
            if len(self.to_scrape) % 100 == 0:
                print(len(self.to_scrape), new_url)
    
    def get_id_for_card(self, card_name):
        poss = Card.where(name=card_name).where(page=1).where(pageSize=1).all()
        if poss:
            if poss[0] is None :
                print(card_name + " has null id")
            #if poss[0].text:
            #    self.vectorizor.tokenize_text(poss[0].text)
            return poss[0].multiverse_id if poss[0].multiverse_id is not None else 0
        else: 
            return 0

class DeckMember:
    def __init__(self, name, card_id, count = 1):
        self.name = name
        self.multiverse_id = card_id
        self.count = count

    def __repr__(self):
        return '{{"name": "{0}", "multiverse_id": {1}, "count": {2}}}'.format(self.name, self.multiverse_id, self.count)
    
    def __str__(self):
        return '{{"name": "{0}", "multiverse_id": {1}, "count": {2}}}'.format(self.name, self.multiverse_id, self.count)
    
    def asDict(self):
        self.name = re.sub(r"[']", "", self.name)
        return {"name" : self.name, "multiverse_id" : self.multiverse_id, "count" : self.count}
    
    def increase(self, number = 1):
        self.count += number

    def decrease(self, number = 1):
        self.count -= number

ds = DeckScraper([])
ds.prime()
ds.build()