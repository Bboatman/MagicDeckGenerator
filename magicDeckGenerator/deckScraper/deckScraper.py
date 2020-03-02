from .scraper import Scraper
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
    def __init__(self):
        self.start_urls = urls
        self.to_scrape = []
        self.seen = []

    def prime(self):
        pickle.dump( {"to_scrape": []}, open( "./models/pickledLinks.p", "wb" ) )

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
            print("Got: " + url)
            deck = []
            if raw_html:
                html = BeautifulSoup(raw_html, 'html.parser')
                if popped['parent'] == 'http://tappedout.net':
                    deck = self.processTappedOut(html)
                if popped['parent'] == 'https://www.mtgtop8.com/':
                    deck = self.processMtgTop8(html)

            if len(deck) < 100 and len(deck) > 0:
                deck_obj = Deck(url, url)
                for member in deck:
                    deck_obj.add_member_to_deck(member)
                self.saveToDB(deck_obj)
                random.shuffle(self.to_scrape)
            
            return

    def processMtgTop8(self, html):
        members = html.find_all("td", attrs={"class": "G14"})
        deck = []
        if not members:
            return []
        else:
            for item in members:
                count = item.find("div").contents[0].strip()
                name = item.find("span").contents[0]
                card_id = self.get_id_for_card(name)
                deck.append(DeckMember(name, card_id, count))
        print("Added MtgTop8 Cards")
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
        if not members:
            return []
        else :
            for item in members:
                name = item["data-orig"]
                card_id = self.get_id_for_card(name)
                count = item["data-qty"]
                deck.append(DeckMember(name, card_id, count))

        print("Added TappedOut Cards")
        similar_decks = html.select("a.name")
        for link in similar_decks:
            if link['href'].find("/mtg-decks/") >= 0:
                self.add_to_scrape_pool(link['href'], 'http://tappedout.net')
            elif link['href'].find("mtg-decks/") >= 0:
                self.add_to_scrape_pool(link['href'], 'http://tappedout.net/')

        return deck
        

    def saveToDB(self, deck):
        body = deck.build_for_db()
        
        headers = {'Content-type': 'application/json'}
        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('POST', '/api/deck/', json.dumps(body), headers)
        resp = conn.getresponse().read()
        response = json.loads(resp)
        deck_id =response['id']
        deck_size = body["deck_size"]
        for member in deck.deckMembers:
            ret = member.build_for_db(deck_id, deck_size)
            req = http.client.HTTPConnection('localhost:8000')
            req.request('POST', '/api/deck_detail/', json.dumps(ret), headers)
            print(ret)

    def add_to_scrape_pool(self, link, parent_domain):
        new_url = link
        if new_url not in self.seen and new_url not in [ e['url'] for e in self.to_scrape ] :
            self.to_scrape.append(
                {'url': link, 'parent': parent_domain}
            )
            if len(self.to_scrape) % 100 == 0:
                print(len(self.to_scrape), new_url)
                pickle.dump( {"to_scrape": self.to_scrape}, open( "./models/pickledLinks.p", "wb" ) )
    
    def get_id_for_card(self, card_name):
        card_name = card_name.lower()
        poss = Card.where(name=card_name).where(page=1).where(pageSize=1).all()
        if poss:
            if poss[0] is None :
                print(card_name + " not in db")
            return poss[0].id if poss[0].id is not None else 0
        else: 
            return 0

class DeckMember:
    def __init__(self, name, card_id, count = 1):
        self.name = name.lower()
        self.two_face_card_normalizer()
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


    def build_for_db(self, deck_id, deck_size):
        signficance = float(self.count) / float(deck_size)
        return {"deck": deck_id, "card": self.name, "count": self.count, "significance": signficance}

    def two_face_card_normalizer(self):
        self.name.replace(" / ", " // ")
        cardnames = {
            "brazen borrower": "brazen borrower // petty theft", \
            "fae of wishes": "fae of wishes // granted", \
            "murderous rider": "murderous rider // swift end", \
            "foulmire knight": "foulmire knight // profane insight", \
            "merfolk secretkeeper" : "merfolk secretkeeper // venture deeper"
        }
        if self.name in cardnames:
            self.name = cardnames[self.name]

class Deck:
    def __init__(self, name, url):
        self.name = name.lower()
        self.url = url
        self.deckMembers = []

    def __str__(self):
        return self.url

    def add_member_to_deck(self, member):
        self.deckMembers.append(member)

    def build_for_db(self):
        deck_size = 0
        unique_count = len(self.deckMembers)
        for member in self.deckMembers:
            deck_size += int(member.count)
        return {"deck_size": deck_size, "unique_count": unique_count, "name": self.name, "url": self.url}

if __name__ == "__main__":
    dS = DeckScraper([])
    dS.prime()
    dS.build()