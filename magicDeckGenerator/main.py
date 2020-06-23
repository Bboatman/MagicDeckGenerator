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

prime = True
rebuild = False

def scrape_sites(): 
    dS = DeckScraper()

    try:
        headers = {'Content-type': 'application/json'}
        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('GET', '/api/deck/', headers=headers)
        resp = conn.getresponse().read()
        response = json.loads(resp)
        seen = [x["url"] for x in response]
        dS.seen = seen

        if prime:
            if (rebuild):
                dS.prime()
                dS.build()
            else:
                # Builds scraping links by searching for decks with unmatched cards on tappedOut and top8
                poss_links = dS.primeFromDB()
        else:
            obj = pickle.load( open( "./models/pickledLinks.p", "rb" ) )
            poss_links = obj["to_scrape"]
        
        
       
        random.shuffle(poss_links)

        if len(poss_links) > 0:
            random.shuffle(poss_links)
            dS.to_scrape = poss_links
            #dS.to_scrape = [] #Uncomment to clean scraping array
            #dS.build() #Uncomment to clean scraping array
            log(0, f"Ingesting {len(dS.to_scrape)} links")
        else:
            log(1, f"Building new scrape model")
            dS.build()

        while((len(dS.seen) < len(seen) + 100) and len(dS.to_scrape) > 0):
            threads = list()
            log(0, f"Seen {len(dS.seen)} links")
            for index in range(3):
                x = threading.Thread(target=thread_function, args=(index,dS,))
                threads.append(x)
                x.start()

            for index, thread in enumerate(threads):
                thread.join()
                log(0, f"Thread {index} done")

    except:
        if not prime:
            obj = {"to_scrape": dS.to_scrape}
            pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise

def thread_function(name, dS):
    log_src = "Thread"
    log(0, f"Thread {name} : starting")
    dS.generate_card_pool()

def buildNewCardDB():
    log(0, "Vectorizing Cards")
    try:
        v = Vectorizor(4)
        v.load_training_sequence(True)
        v.build_clean_array(True)
        playsound('/home/brooke/MagicDeckGenerator/magicDeckGenerator/models/cheer.wav')
    except Exception as e: 
        traceback.print_exc()
        playsound('/home/brooke/MagicDeckGenerator/magicDeckGenerator/models/fart.wav')

def vectorizeCards():
    log(0, "Vectorizing Cards")
    model_dimensionality = 4
    try:
        v = Vectorizor(model_dimensionality)
        v.load_training_sequence(False)
        v.graph_cards(True)
        playsound('/home/brooke/MagicDeckGenerator/magicDeckGenerator/models/cheer.wav')
    except Exception as e: 
        traceback.print_exc()
        playsound('/home/brooke/MagicDeckGenerator/magicDeckGenerator/models/fart.wav')


if __name__ == "__main__":
    command = sys.argv[1]
    if  (command == "scrape"):
        scrape_sites()
    elif (command == "vectorize"):
        vectorizeCards()
    elif (command == "buildcards"):
        buildNewCardDB()
    elif (command == "help"):
        print("scrape: Scrape mtgTop8 and tappedOut for deck data")
        print("buildcards: Process Scryfall data and save it to the database")
        print("vectorize: Use machine learning to vectorize cards and reduce their dimensionality")
        print("help: display all command options")
    else: 
        print(f"'{command}' is not a valid command, try using 'help' to see all command options")