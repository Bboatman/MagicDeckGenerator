import pickle, random, gc, csv, time, traceback, http.client, json, threading, sys
import numpy as np

from lib.deckScraper import DeckScraper
from lib.cardVectorizor import Vectorizor
from lib.log import Log

from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA

from gensim.utils import simple_preprocess
from playsound import playsound

log = Log("MAIN", 0).log

def scrape_sites(): 
    log_src = "Main"

    dS = DeckScraper()
    #dS.prime()
    #dS.build()
    try:
        headers = {'Content-type': 'application/json'}
        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('GET', '/api/deck/', headers=headers)
        resp = conn.getresponse().read()
        response = json.loads(resp)
        seen = [x["url"] for x in response]

        #obj = pickle.load( open( "./models/pickledLinks.p", "rb" ) )
        #poss_links = obj["to_scrape"]
        dS.seen = seen
        
        poss_links = [{"parent": 'http://tappedout.net/', "url": "mtg-decks/in-edgeways/"}, \
            {"parent": 'http://tappedout.net/', "url": "mtg-decks/06-04-18-meme-deck/"}, \
            {"parent": 'http://tappedout.net/', "url": "mtg-decks/wugy-hug-n-hate/"}, \
            {"parent": 'http://tappedout.net/', "url": "mtg-decks/delirius-manifestation/"}, \
            {"parent": 'https://www.mtgtop8.com/', "url": "event?e=502&d=206461&f=LI"}, \
            {"parent": 'https://www.mtgtop8.com/', "url": "event?e=17041&d=305431&f=EDHM"}, \
            {"parent": 'https://www.mtgtop8.com/', "url": "event?e=26186&d=398844&f=ST"}, \
            {"parent": 'https://www.mtgtop8.com/', "url": "event?e=9191&d=252647&f=LI"}]

        random.shuffle(poss_links)

        if len(poss_links) > 0:
            random.shuffle(poss_links)
            dS.to_scrape = poss_links
            #dS.to_scrape = [] #Uncomment to clean scraping array
            #dS.build() #Uncomment to clean scraping array
            log(0, f"{log_src}  : Ingesting {len(dS.to_scrape)} links")
        else:
            log(1, "%s : Building new scrape model", log_src)
            dS.build()

        while(len(dS.seen) < len(seen) + 100):
            threads = list()
            log(0, f"{log_src} : Seen {len(dS.seen)} links")
            for index in range(3):
                x = threading.Thread(target=thread_function, args=(index,dS,))
                threads.append(x)
                x.start()

            for index, thread in enumerate(threads):
                thread.join()
                log(0, f"{log_src} : thread {index} done")

    except:
        obj = {"to_scrape": dS.to_scrape}
        pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise

def thread_function(name, dS):
    log_src = "Thread"
    log(0, f"{log_src} {name} : starting")
    dS.generate_card_pool()

def vectorizeCards():
    log(0, "Vectorizing Cards")
    model_dimensionality = 3
    new_data_set = False
    try:
        v = Vectorizor(model_dimensionality)
        v.load_training_sequence(new_data_set)
        v.graph_cards(True)
        playsound('/home/brooke/MagicDeckGenerator/magicDeckGenerator/models/cheer.wav')
    except Exception as e: 
        traceback.print_exc()
        playsound('/home/brooke/MagicDeckGenerator/magicDeckGenerator/models/fart.wav')


if __name__ == "__main__":
    #log(0, f"{len(sys.argv)} arguments found")
    command = sys.argv[1]
    if  (command == "scrape"):
        scrape_sites()
    elif (command == "vectorize"):
        vectorizeCards()
    elif (command == "help"):
        print("scrape: Scrape mtgTop8 and tappedOut for deck data")
        print("vectorize: Process Scryfall data and save it to the database")
        print("help: display all command options")
    else: 
        print(f"'{command}' is not a valid command, try using 'help' to see all command options")