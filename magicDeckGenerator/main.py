import pickle, random, gc, csv, time
from .deckScraper import DeckScraper
from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA
from gensim.utils import simple_preprocess
import numpy as np
import http.client
import json
import threading
from .log import Log

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
            log(0, "%s : Ingesting %d links", log_src, len(dS.to_scrape))
        else:
            log(1, "%s : Building new scrape model", log_src)
            dS.build()

        while(len(dS.seen) < len(seen) + 100):
            threads = list()
            log(0, "%s : Seen %d links", log_src, len(dS.seen))
            for index in range(3):
                x = threading.Thread(target=thread_function, args=(index,dS,))
                threads.append(x)
                x.start()

            for index, thread in enumerate(threads):
                thread.join()
                log(0, "%s : thread %d done", log_src, index)

    except:
        obj = {"to_scrape": dS.to_scrape}
        pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise


def thread_function(name, dS):
    log_src = "Thread"
    log(0, "%s %s : starting", log_src, name)
    dS.generate_card_pool()

    
scrape_sites()