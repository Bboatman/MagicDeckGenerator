
import json, re, random, time, urllib.parse, pickle, requests
from .scraper import Scraper
from .log import Log
from bs4 import BeautifulSoup
from importlib import import_module
import http.client
from decouple import config

host = config("HOST") 
headers = {'Content-type': 'application/json'}
resp = requests.post(host + "/api/authenticate", data=json.dumps({"username": "admin", "password": "admin"}), headers=headers)
token = json.loads(resp.text)["id_token"]
headers["Authorization"] = "Bearer " + token

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
                log(2, f"Unavailable url: {url}")
        random.shuffle(self.to_scrape)
        log(0, "Done building")

    def primeFromDB(self):
        response = []
        try:
            # TODO: Fix so this is generified to a service https://github.com/Bboatman/MagicDeckGenerator/issues/6
            resp = requests.get(host + "/api/unseen", headers=self.headers)
            response = json.loads(resp.text)
        except:
            print("Issue connecting to the database")

        names = [x['name'] for x in response]
        log(1, names)
        for name in names:
            self.getMtgTop8Prime(name)
            self.getTappedOutPrime(name)


        log(0, self.to_scrape)
        #log(1, f"Total tappedOut to scrape {tCount}")
        #log(1, f"Total mtgTop8 to scrape {mCount}")

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
                if nlink['href'].find('event?e') >= 0:
                    added = self.add_to_scrape_pool(nlink['href'], 'https://www.mtgtop8.com/')
                    if added:
                        count += 1
        
        log(1, f"Found {count} links for {searchStr} in mtgTop8")

    def getTappedOutPrime(self, searchStr):
        sanitized = urllib.parse.quote(searchStr)
        url = f"https://tappedout.net/search/?q={sanitized}"
        raw_html = requests.get(url)
        html = BeautifulSoup(raw_html.text, 'html.parser')
        count = 0
        for link in html.select('a'):
            if link['href'].find("/mtg-decks/") >= 0 and url not in self.seen:
                added = self.add_to_scrape_pool(link['href'], 'http://tappedout.net')
                if added:
                    count += 1
            elif link['href'].find("mtg-decks/") >= 0 and url not in self.seen:
                added = self.add_to_scrape_pool(link['href'], 'http://tappedout.net/')
                if added:
                    count += 1

        log(1, f"Found {count} links for {searchStr} in tappedOut")

    def getMtgTop8Links(self, link):
            url = 'https://www.mtgtop8.com/' + link['href']
            raw_html = Scraper(url).simple_get()
            html = BeautifulSoup(raw_html, 'html.parser')

            for nlink in html.select('a'):
                if nlink['href'].find('event?e') >= 0:
                    self.add_to_scrape_pool(nlink['href'], 'https://www.mtgtop8.com/')
                

    def generate_card_pool(self, lock=None):
        popped = self.to_scrape.pop()
        url = popped["parent"] + popped['url']

        if url in self.seen:
            log(0, f"Seen: {url}")
            return
        else:
            if (lock != None):
                lock.acquire()
                self.seen.append(url)
                lock.release()
            else :
                self.seen.append(url)

            raw_html = Scraper(url).simple_get()
            log(0, f"Got: {url}")
            deck = []
            if raw_html:
                html = BeautifulSoup(raw_html, 'html.parser')
                if popped['parent'] == 'https://www.mtgtop8.com/':
                    deck = self.processMtgTop8(html)
                else:
                    deck = self.processTappedOut(html)

            if len(deck) >= 50 and len(deck) <160:
                log(1, f"Saving: {url}")
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
            try:
                for item in members:
                    if (item.find("div") and item.find("div").contents[0] != None):
                        count = item.find("div").contents[0].strip()
                        name = item.find("span").contents[0]
                        card_id = 0
                        deck.append(DeckMember(name, card_id, count))
            except TypeError as err:
                log(3, err)

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
                card_id = 0
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
        print(body)

    def add_to_scrape_pool(self, link, parent_domain):
        new_url = link
        if new_url not in self.seen and new_url not in [ e['url'] for e in self.to_scrape ] :
            self.to_scrape.append(
                {'url': link, 'parent': parent_domain}
            )
            if len(self.to_scrape) % 100 == 0:
                log(0, f"To Scrape: {len(self.to_scrape)}, adding {new_url}")
                pickle.dump( {"to_scrape": self.to_scrape}, open( "./models/pickledLinks.p", "wb" ) )
            return True
        return False

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
            "hide": "hide // seek", \
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
            "garruk, the veil-cursed": "garruk relentless // garruk, the veil-cursed", \
            "loyal cathar": "loyal cathar // unhallowed cathar", \
            "docent of perfection": "docent of perfection // final iteration", \
            "conduit of storms": "conduit of storms // conduit of emrakul", \
            "tangleclaw werewolf": "tangleclaw werewolf // fibrous entangler", \
            "instigator gang": "instigator gang // wildblood pack", \
            "bloodline keeper": "bloodline keeper // lord of lineage", \
            "villagers of estwald": "villagers of estwald // howlpack of estwald", \
            "fire": "fire // ice", \
            "pious evangel": "pious evangel // wayward disciple", \
            "victory": "onward // victory", \
            "daring sleuth": "daring sleuth // bearer of overwhelming truths", \
            "lambholt pacifist": "lambholt pacifist // lambholt butcher", \
            "lambholt elder": "lambholt elder // silverpelt werewolf", \
            "bushi tenderfoot": "bushi tenderfoot // kenzo the hardhearted", \
            "flesh": "flesh // blood", \
            "afflicted deserter // werewolf ransacker":"afflicted deserter // werewolf ransacker", \
            "daybreak ranger":"daybreak ranger // nightfall predator", \
            "hermit of the natterknolls": "hermit of the natterknolls // lone wolf of the natterknolls", \
            "scorned villager": "scorned villager // moonscarred werewolf", \
            "marton stromgald": "márton stromgald", \
            "mayor of avabruck": "mayor of avabruck // howlpack alpha", \
            "homura, human ascendant": "homura, human ascendant // homura's essence", \
            "wear": "wear // tear", \
            "dusk": "dusk // dawn", \
            "budoka pupil": "budoka pupil // ichiga, who topples oaks", \
            "budoka gardener": "budoka gardener // dokai, weaver of life", \
            "ifh-biff efreet": "ifh-bíff efreet", \
            "driven": "driven // despair", \
            "gruun, the lonely king": "grunn, the lonely king", \
            "sage of ancient lore": "sage of ancient lore // werewolf of ancient hunger", \
            "sasaya, orochi ascendant": "sasaya, orochi ascendant // sasaya's essence", \
            "orochi eggwatcher": "orochi eggwatcher // shidako, broodmistress", \
            "neglected heirloom": "neglected heirloom // ashmouth blade", \
            "hanweir militia captain": "hanweir militia captain // westvale cult leader", \
            "ulrich of the krallenhorde": "ulrich of the krallenhorde // ulrich, uncontested alpha", \
            "akki lavarunner": "akki lavarunner // tok-tok, volcano born", \
            "hadana's climb": "hadana's climb // winged temple of orazca", \
            "chandra, fire of kaladesh": "chandra, fire of kaladesh // chandra, roaring flame", \
            "student of elements": "student of elements // tobita, master of winds", \
            "onward": "onward // victory", \
            "dandan": "dandân", \
            "smoldering werewolf": "smoldering werewolf // erupting dreadwolf", \
            "insult": "insult // injury", \
            "refuse": "refuse // cooperate", \
            "order": "order // chaos", \
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