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
from ..log import Log

log = Log("DECK SCRAPER", 0).log

urls = [{"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/standard/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/pauper/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/modern/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/tops/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/arena/"}, \
        {"parent": 'http://tappedout.net/', "url": "mtg-deck-builder/pioneer/"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format_limited"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PAU"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PEA"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=BL"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=MO"}, \
        {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PI"}, \
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
            try:
                raw_html = Scraper(url).simple_get()
                html = BeautifulSoup(raw_html, 'html.parser')
                if u['parent'].find('tappedout') >= 0:
                    for link in html.select('a'):
                        if link['href'].find("/mtg-decks/") >= 0 and url not in self.seen:
                            self.add_to_scrape_pool(link['href'], 'http://tappedout.net')
                        elif link['href'].find("mtg-decks/") >= 0 and url not in self.seen:
                            self.add_to_scrape_pool(link['href'], 'http://tappedout.net/')
                elif u['parent'].find('mtgtop8') >= 0:
                    for link in html.select('a'):
                        if link['href'].find('archetype') >= 0:
                            self.getMtgTop8Links(link)
            except:
                log(2, "Unavailable url: " + url)
        random.shuffle(self.to_scrape)
        log(0, "Done building")

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
            log(0, "seen: " + url)
            return
        else:
            self.seen.append(url)
            raw_html = Scraper(url).simple_get()
            log(0, "Got: " + url)
            deck = []
            if raw_html:
                html = BeautifulSoup(raw_html, 'html.parser')
                if popped['parent'] == 'https://www.mtgtop8.com/':
                    deck = self.processMtgTop8(html)
                else:
                    deck = self.processTappedOut(html)

            if len(deck) > 0:
                log(0, "saving: " + url)
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
        log(0, "Added MtgTop8 Cards")
        similar_decks = html.select("div.S14 a")
        for nlink in similar_decks:
            if nlink['href'].find('event?e=') >= 0 and nlink['href'] not in self.seen:
                self.add_to_scrape_pool(nlink['href'], 'https://www.mtgtop8.com/')
            elif nlink['href'].find('?e=') >= 0 and nlink['href'] not in self.seen:
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

        log(0, "Added TappedOut Cards")
        similar_decks = html.select("a.name")
        for link in similar_decks:
            if link['href'].find("/mtg-decks/") >= 0 and link['href'] not in self.seen:
                self.add_to_scrape_pool(link['href'], 'http://tappedout.net')
            elif link['href'].find("mtg-decks/") >= 0 and link['href'] not in self.seen:
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
            log(0, ret)

    def add_to_scrape_pool(self, link, parent_domain):
        new_url = link
        if new_url not in self.seen and new_url not in [ e['url'] for e in self.to_scrape ] :
            self.to_scrape.append(
                {'url': link, 'parent': parent_domain}
            )
            if len(self.to_scrape) % 100 == 0:
                log(0, "To Scrape: %d, adding %s", len(self.to_scrape), new_url)
                pickle.dump( {"to_scrape": self.to_scrape}, open( "./models/pickledLinks.p", "wb" ) )
    
    def get_id_for_card(self, card_name):
        card_name = card_name.lower()
        poss = Card.where(name=card_name).where(page=1).where(pageSize=1).all()
        if poss:
            if poss[0] is None :
                log(0, card_name + " not in db")
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
        self.name = self.name.replace(" / ", " // ")
        if ("knight of the kitchen sink" in self.name):
            self.name = "knight of the kitchen sink"
        
        #Last verified: kytheon, hero of akros
        cardnames = {
            "brazen borrower": "brazen borrower // petty theft", \
            "fae of wishes": "fae of wishes // granted", \
            "murderous rider": "murderous rider // swift end", \
            "foulmire knight": "foulmire knight // profane insight", \
            "merfolk secretkeeper" : "merfolk secretkeeper // venture deeper", \
            "bonecrusher giant": "bonecrusher giant // stomp", \
            "lovestruck beast": "lovestruck beast // heart's desire", \
            "rimrock knight": "rimrock knight // boulder rush", \
            "embereth shieldbreaker": "embereth shieldbreaker // battle display", \
            "delver of secrets": "delver of secrets // insectile aberration", \
            "giant killer": "giant killer // chop down", \
            "realm-cloaked giant": "realm-cloaked giant // cast off", \
            "search for azcanta": "search for azcanta // azcanta, the sunken ruin", \
            "nissa, vastwood seer": "nissa, vastwood seer // nissa, sage animist", \
            "westvale abbey": "westvale abbey // ormendahl, profane prince", \
            "arguel's blood fast": "arguel's blood fast // temple of aclazotz", \
            "legion's landing": "legion's landing // adanto, the first fort", \
            "chalice of life": "chalice of life // chalice of death", \
            "thaumatic compass": "thaumatic compass // spires of orazca", \
            "elbrus, the binding blade": "elbrus, the binding blade // withengar unbound", \
            "jace, vryn's prodigy": "jace, vryn's prodigy // jace, telepath unbound", \
            "thing in the ice": "thing in the ice // awoken horror", \
            "journey to eternity": "journey to eternity // atzal, cave of eternity", \
            "order of midnight": "order of midnight // alter fate", \
            "smitten swordmaster": "smitten swordmaster // curry favor", \
            "beanstalk giant": "beanstalk giant // fertile footsteps", \
            "path of mettle": "path of mettle // metzali, tower of triumph", \
            "conqueror's galleon": "conqueror's galleon // conqueror's foothold", \
            "breaking": "breaking // entering", \
            "nezumi graverobber": "nezumi graverobber // nighteyes the desecrator", \
            "archangel avacyn": "archangel avacyn // avacyn, the purifier", \
            "kytheon, hero of akros": "kytheon, hero of akros // gideon, battle-forged", \
            "storm the vault": "storm the vault // vault of catlacan", \
            "treasure map": "treasure map // treasure cove", \
            "faerie guidemother": "faerie guidemother // gift of the fae", \
            "ardenvale tactician": "ardenvale tactician // dizzying swoop", \
            "flaxen intruder": "flaxen intruder // welcome home", \
            "tuinvale treefolk": "tuinvale treefolk // oaken boon", \
            "rosethorn acolyte": "rosethorn acolyte // seasonal ritual", \
            "shepherd of the flock": "shepherd of the flock // usher to safety", \
            "silverflame squire": "silverflame squire // on alert", \
            "queen of ice": "queen of ice // rage of winter", \
            "curious pair": "curious pair // treats to share", \
            "garenbrig carver": "garenbrig carver // shield's might", \
            "oakhame ranger": "oakhame ranger // bring back", \
            "hypnotic sprite": "hypnotic sprite // mesmeric glare", \
            "animating faerie": "animating faerie // bring to life", \
            "merchant of the vale": "merchant of the vale // haggle", \
            "lonesome unicorn": "lonesome unicorn // rider in need", \
            "liliana, heretical healer": "liliana, heretical healer // liliana, defiant necromancer", \
            "kessig prowler": "kessig prowler // sinuous predator", \
            "duskwatch recruiter": "duskwatch recruiter // krallenhorde howler",\
            "voldaren pariah": "voldaren pariah // abolisher of bloodlines",\
            "growing rites of itlimoc": "growing rites of itlimoc // itlimoc, cradle of the sun",\
            "rune-tail, kitsune ascendant": "rune-tail, kitsune ascendant // rune-tail's essence",\
            "lone rider": "lone rider // it that rides as one",\
            "azor's gateway": "azor's gateway // sanctum of the sun", \
            "primal amulet": "primal amulet // primal wellspring", \
            "give": "give // take", \
            "lim-dul's vault": "lim-dûl's vault", \
            "huntmaster of the fells": "huntmaster of the fells // ravager of the fells", \
            "farm": "farm // market", \
            "commit": "commit // memory", \
            "rags": "rags // riches", \
            "seek": "hide // seek", \
            "profane procession": "profane procession // tomb of the dusk rose", \
            "dowsing dagger": "dowsing dagger // lost vale", \
            "accursed witch": "accursed witch // infectious curse", \
            "golden guardian": "golden guardian // gold-forge garrison", \
            "reaper of night": "reaper of night // harvest fear", \
            "life": "life // death", \
            "cut": "cut // ribbons", \
            "nezumi shortfang": "nezumi shortfang // stabwhisker the odious", \
            "reckless waif": "reckless waif // merciless predator", \
            "extricator of sin": "extricator of sin // extricator of flesh", \
            "gideon, battle-forged": "kytheon, hero of akros // gideon, battle-forged", \
            "garruk relentless": "garruk relentless // garruk, the veil-cursed", \
            "kessig forgemaster": "kessig forgemaster // flameheart werewolf", \
            "solitary hunter": "solitary hunter // one of the pack", \
            "ulvenwald captive": "ulvenwald captive // ulvenwald abomination", \
            "nicol bolas, the ravager": "nicol bolas, the ravager // nicol bolas, the arisen", \
            "vance's blasting cannons": "vance's blasting cannons // spitfire bastion", \
            "avacyn, the purifier": "archangel avacyn // avacyn, the purifier", \
            "autumnal gloom": "autumnal gloom // ancient of the equinox", \
            "aberrant researcher": "aberrant researcher // perfected form", \
            "cryptolith fragment": "cryptolith fragment // aurora of emrakul", \
            "thraben gargoyle": "thraben gargoyle // stonewing antagonizer", \
            "startled awake": "startled awake // persistent nightmare", \
            "final judgement": "final judgment", \
            "shrill howler": "shrill howler // howling chorus", \
            "ludevic's test subject": "ludevic's test subject // ludevic's abomination", \
            "heir of falkenrath": "heir of falkenrath // heir to the night", \
            "jushi apprentice": "jushi apprentice // tomoya the revealer", \
            "arlinn, embraced by the moon": "arlinn kord // arlinn, embraced by the moon", \
            "nicol bolas, the arisen": "nicol bolas, the ravager // nicol bolas, the arisen", \
            "arlinn kord": "arlinn kord // arlinn, embraced by the moon", \
            "chandra, roaring flame": "chandra, fire of kaladesh // chandra, roaring flame", \
            "nissa, sage animist": "nissa, vastwood seer // nissa, sage animist", \
            "liliana, defiant necromancer": "liliana, heretical healer // liliana, defiant necromancer", \
            "jace, telepath unbound": "jace, vryn's prodigy // jace, telepath unbound", \
            "garruk, the veil-cursed": "garruk relentless // garruk, the veil-cursed"
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