
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
from .service import DeckService
from bs4 import BeautifulSoup
import random

log = Log("DECK SCRAPER", 0).log
searchUnseen = True
maxTop8 = 10

# TODO: Make this variable dependant
urls = [
    {"parent": 'https://www.mtgtop8.com/', "url": "format_limited"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PAU"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PEA"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=BL"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=MO"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PI"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=ST"}
]


class DeckScraper:
    def __init__(self):
        self.start_urls = urls
        self.to_scrape = []
        self.seen = []
        self.service = DeckService()
        self.spider_search = False

    def prime(self):
        pickle.dump({"to_scrape": []}, open("./models/pickledLinks.p", "wb"))

    def build(self):
        self.spider_search = True
        print("Is spider searching")
        for u in self.start_urls:
            url = u['parent'] + u['url']
            try:
                raw_html = Scraper(url).simple_get()
                html = BeautifulSoup(raw_html, 'html.parser')
                if u['parent'].find('mtgtop8') >= 0:
                    for link in html.find_all('a',  href=True):
                        if 'archetype' in link['href']:
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
                resp = self.service.get_unseen()
                names = resp["body"]
                random.shuffle(names)
            else:
                resp = self.service.get_cards()
                names = [x["name"] for x in resp["body"]]
                random.shuffle(names)
            log(0, "Names: " + str(names))
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
                if '&' in nlink['href']:
                    urlVal = nlink['href'].split('&')[0]
                if nlink['href'].find('event?e') >= 0:
                    self.add_to_scrape_pool(
                        urlVal, 'https://www.mtgtop8.com/')

    def generate_card_pool(self, lock=None):
        popped = self.to_scrape.pop()
        url = popped["parent"] + popped['url']
        ret = False

        raw_html = Scraper(url).simple_get()
        log(0, f"Got: {url}")
        deck = []
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
                card_id = 0
                deck_member = DeckMember(name, card_id, count)
                deck.append(deck_member)
        except Exception as e:
            log(0, "Failure to parse cards")
            log(0, e)
            return

        if not self.spider_search:
            return deck

        for nlink in html.find_all('a',  href=True):
            boolval = '?e=' in nlink['href']
            urlVal = nlink['href']
            if '&' in nlink['href']:
                urlVal = nlink['href'].split('&')[0]

            parsedVal = 'https://www.mtgtop8.com/event' + urlVal
            added = []
            if boolval and parsedVal not in self.seen and parsedVal not in added:
                added.append(parsedVal)
                self.add_to_scrape_pool(
                    "event" + urlVal, 'https://www.mtgtop8.com/')

        return deck

    def saveToDB(self, deck):
        builtDeck = deck.build_for_db()
        if builtDeck["shouldSave"]:
            log(0, "Saving Deck")
            body = builtDeck["body"]
            self.service.post_deck(body)
        return builtDeck["shouldSave"]

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


class DeckMember:
    def __init__(self, name, card_id, count=1):
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
        return {"name": self.name, "multiverse_id": self.multiverse_id, "count": self.count}

    def increase(self, number=1):
        if type(self.count) is str:
            self.count = int(self.count)

        self.count += int(number)

    def decrease(self, number=1):
        if type(self.count) is str:
            self.count = int(self.count)

        self.count -= number

    def build_for_db(self):
        return {"parsedName": self.name, "count": self.count}

    def two_face_card_normalizer(self):
        self.name = self.name.replace(" / ", " // ")
        if ("knight of the kitchen sink" in self.name):
            self.name = "knight of the kitchen sink"

        # Last verified: kytheon, hero of akros
        cardnames = {
            "brazen borrower": "brazen borrower // petty theft",
            "fae of wishes": "fae of wishes // granted",
            "murderous rider": "murderous rider // swift end",
            "foulmire knight": "foulmire knight // profane insight",
            "merfolk secretkeeper": "merfolk secretkeeper // venture deeper",
            "bonecrusher giant": "bonecrusher giant // stomp",
            "lovestruck beast": "lovestruck beast // heart's desire",
            "rimrock knight": "rimrock knight // boulder rush",
            "embereth shieldbreaker": "embereth shieldbreaker // battle display",
            "delver of secrets": "delver of secrets // insectile aberration",
            "giant killer": "giant killer // chop down",
            "realm-cloaked giant": "realm-cloaked giant // cast off",
            "search for azcanta": "search for azcanta // azcanta, the sunken ruin",
            "nissa, vastwood seer": "nissa, vastwood seer // nissa, sage animist",
            "westvale abbey": "westvale abbey // ormendahl, profane prince",
            "arguel's blood fast": "arguel's blood fast // temple of aclazotz",
            "legion's landing": "legion's landing // adanto, the first fort",
            "chalice of life": "chalice of life // chalice of death",
            "thaumatic compass": "thaumatic compass // spires of orazca",
            "elbrus, the binding blade": "elbrus, the binding blade // withengar unbound",
            "jace, vryn's prodigy": "jace, vryn's prodigy // jace, telepath unbound",
            "thing in the ice": "thing in the ice // awoken horror",
            "journey to eternity": "journey to eternity // atzal, cave of eternity",
            "order of midnight": "order of midnight // alter fate",
            "smitten swordmaster": "smitten swordmaster // curry favor",
            "beanstalk giant": "beanstalk giant // fertile footsteps",
            "path of mettle": "path of mettle // metzali, tower of triumph",
            "conqueror's galleon": "conqueror's galleon // conqueror's foothold",
            "breaking": "breaking // entering",
            "nezumi graverobber": "nezumi graverobber // nighteyes the desecrator",
            "archangel avacyn": "archangel avacyn // avacyn, the purifier",
            "kytheon, hero of akros": "kytheon, hero of akros // gideon, battle-forged",
            "storm the vault": "storm the vault // vault of catlacan",
            "treasure map": "treasure map // treasure cove",
            "faerie guidemother": "faerie guidemother // gift of the fae",
            "ardenvale tactician": "ardenvale tactician // dizzying swoop",
            "flaxen intruder": "flaxen intruder // welcome home",
            "tuinvale treefolk": "tuinvale treefolk // oaken boon",
            "rosethorn acolyte": "rosethorn acolyte // seasonal ritual",
            "shepherd of the flock": "shepherd of the flock // usher to safety",
            "silverflame squire": "silverflame squire // on alert",
            "queen of ice": "queen of ice // rage of winter",
            "curious pair": "curious pair // treats to share",
            "garenbrig carver": "garenbrig carver // shield's might",
            "oakhame ranger": "oakhame ranger // bring back",
            "hypnotic sprite": "hypnotic sprite // mesmeric glare",
            "animating faerie": "animating faerie // bring to life",
            "merchant of the vale": "merchant of the vale // haggle",
            "lonesome unicorn": "lonesome unicorn // rider in need",
            "liliana, heretical healer": "liliana, heretical healer // liliana, defiant necromancer",
            "kessig prowler": "kessig prowler // sinuous predator",
            "duskwatch recruiter": "duskwatch recruiter // krallenhorde howler",
            "voldaren pariah": "voldaren pariah // abolisher of bloodlines",
            "growing rites of itlimoc": "growing rites of itlimoc // itlimoc, cradle of the sun",
            "rune-tail, kitsune ascendant": "rune-tail, kitsune ascendant // rune-tail's essence",
            "lone rider": "lone rider // it that rides as one",
            "azor's gateway": "azor's gateway // sanctum of the sun",
            "primal amulet": "primal amulet // primal wellspring",
            "give": "give // take",
            "huntmaster of the fells": "huntmaster of the fells // ravager of the fells",
            "farm": "farm // market",
            "commit": "commit // memory",
            "rags": "rags // riches",
            "seek": "hide // seek",
            "profane procession": "profane procession // tomb of the dusk rose",
            "dowsing dagger": "dowsing dagger // lost vale",
            "accursed witch": "accursed witch // infectious curse",
            "golden guardian": "golden guardian // gold-forge garrison",
            "reaper of night": "reaper of night // harvest fear",
            "life": "life // death",
            "cut": "cut // ribbons",
            "hide": "hide // seek",
            "nezumi shortfang": "nezumi shortfang // stabwhisker the odious",
            "reckless waif": "reckless waif // merciless predator",
            "extricator of sin": "extricator of sin // extricator of flesh",
            "gideon, battle-forged": "kytheon, hero of akros // gideon, battle-forged",
            "garruk relentless": "garruk relentless // garruk, the veil-cursed",
            "kessig forgemaster": "kessig forgemaster // flameheart werewolf",
            "solitary hunter": "solitary hunter // one of the pack",
            "ulvenwald captive": "ulvenwald captive // ulvenwald abomination",
            "nicol bolas, the ravager": "nicol bolas, the ravager // nicol bolas, the arisen",
            "vance's blasting cannons": "vance's blasting cannons // spitfire bastion",
            "avacyn, the purifier": "archangel avacyn // avacyn, the purifier",
            "autumnal gloom": "autumnal gloom // ancient of the equinox",
            "aberrant researcher": "aberrant researcher // perfected form",
            "cryptolith fragment": "cryptolith fragment // aurora of emrakul",
            "thraben gargoyle": "thraben gargoyle // stonewing antagonizer",
            "startled awake": "startled awake // persistent nightmare",
            "final judgement": "final judgment",
            "shrill howler": "shrill howler // howling chorus",
            "ludevic's test subject": "ludevic's test subject // ludevic's abomination",
            "heir of falkenrath": "heir of falkenrath // heir to the night",
            "jushi apprentice": "jushi apprentice // tomoya the revealer",
            "arlinn, embraced by the moon": "arlinn kord // arlinn, embraced by the moon",
            "nicol bolas, the arisen": "nicol bolas, the ravager // nicol bolas, the arisen",
            "arlinn kord": "arlinn kord // arlinn, embraced by the moon",
            "chandra, roaring flame": "chandra, fire of kaladesh // chandra, roaring flame",
            "nissa, sage animist": "nissa, vastwood seer // nissa, sage animist",
            "liliana, defiant necromancer": "liliana, heretical healer // liliana, defiant necromancer",
            "jace, telepath unbound": "jace, vryn's prodigy // jace, telepath unbound",
            "garruk, the veil-cursed": "garruk relentless // garruk, the veil-cursed",
            "loyal cathar": "loyal cathar // unhallowed cathar",
            "docent of perfection": "docent of perfection // final iteration",
            "conduit of storms": "conduit of storms // conduit of emrakul",
            "tangleclaw werewolf": "tangleclaw werewolf // fibrous entangler",
            "instigator gang": "instigator gang // wildblood pack",
            "bloodline keeper": "bloodline keeper // lord of lineage",
            "villagers of estwald": "villagers of estwald // howlpack of estwald",
            "fire": "fire // ice",
            "pious evangel": "pious evangel // wayward disciple",
            "victory": "onward // victory",
            "daring sleuth": "daring sleuth // bearer of overwhelming truths",
            "lambholt pacifist": "lambholt pacifist // lambholt butcher",
            "lambholt elder": "lambholt elder // silverpelt werewolf",
            "bushi tenderfoot": "bushi tenderfoot // kenzo the hardhearted",
            "flesh": "flesh // blood",
            "afflicted deserter // werewolf ransacker": "afflicted deserter // werewolf ransacker",
            "daybreak ranger": "daybreak ranger // nightfall predator",
            "hermit of the natterknolls": "hermit of the natterknolls // lone wolf of the natterknolls",
            "scorned villager": "scorned villager // moonscarred werewolf",
            "marton stromgald": "márton stromgald",
            "mayor of avabruck": "mayor of avabruck // howlpack alpha",
            "homura, human ascendant": "homura, human ascendant // homura's essence",
            "wear": "wear // tear",
            "dusk": "dusk // dawn",
            "budoka pupil": "budoka pupil // ichiga, who topples oaks",
            "budoka gardener": "budoka gardener // dokai, weaver of life",
            "ifh-biff efreet": "ifh-bíff efreet",
            "driven": "driven // despair",
            "gruun, the lonely king": "grunn, the lonely king",
            "sage of ancient lore": "sage of ancient lore // werewolf of ancient hunger",
            "sasaya, orochi ascendant": "sasaya, orochi ascendant // sasaya's essence",
            "orochi eggwatcher": "orochi eggwatcher // shidako, broodmistress",
            "neglected heirloom": "neglected heirloom // ashmouth blade",
            "hanweir militia captain": "hanweir militia captain // westvale cult leader",
            "ulrich of the krallenhorde": "ulrich of the krallenhorde // ulrich, uncontested alpha",
            "akki lavarunner": "akki lavarunner // tok-tok, volcano born",
            "hadana's climb": "hadana's climb // winged temple of orazca",
            "chandra, fire of kaladesh": "chandra, fire of kaladesh // chandra, roaring flame",
            "student of elements": "student of elements // tobita, master of winds",
            "onward": "onward // victory",
            "dandan": "dandân",
            "smoldering werewolf": "smoldering werewolf // erupting dreadwolf",
            "insult": "insult // injury",
            "refuse": "refuse // cooperate",
            "order": "order // chaos",
            "skin invasion": "skin invasion // skin shedder"
        }

        if self.name in cardnames:
            self.name = cardnames[self.name]
        elif "garbage elemental" in self.name:
            self.name = "garbage elemental"
        elif "sly spy" in self.name:
            self.name = "sly spy"
        elif "ineffable blessing" in self.name:
            self.name = "ineffable blessing"
        elif "bosium" in self.name:
            self.name = self.name.replace("bosium", "bösium")
        elif "jotun" in self.name:
            self.name = self.name.replace("jotun", "jötun")
        elif "lim-dul" in self.name:
            self.name = self.name.replace("lim-dul", "lim-dûl")


class Deck:
    def __init__(self, name, url):
        self.name = name.lower()
        self.url = url
        self.deckMembers = []

    def __str__(self):
        return self.url

    def add_member_to_deck(self, member):
        self.deckMembers.append(member)

    def get_deck_size(self):
        body = {}
        deck_size = 0
        for member in self.deckMembers:
            deck_size += int(member.count)
            if member.name not in body:
                body[member.name] = member
            else:
                body[member.name].increase(member.count)
        return [body, deck_size]

    def build_for_db(self):
        body = self.get_deck_size()[0]

        countList = [int(x.count) for x in body.values()]
        shouldSave = max(countList) <= 40

        return {
            "body": {
                "id": None,
                "name": self.name, "url": self.url,
                "cardInstances": [x.build_for_db() for x in body.values()]
            },
            "shouldSave": shouldSave}


if __name__ == "__main__":
    dS = DeckScraper([])
    dS.prime()
    dS.build()
