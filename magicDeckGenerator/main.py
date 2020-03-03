import pickle, random, gc, csv, time
from deckScraper import DeckScraper
from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA
from gensim.utils import simple_preprocess
import numpy as np
import http.client
import json


def scrape_sites():
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

        obj = pickle.load( open( "./models/pickledLinks.p", "rb" ) )
        poss_links = obj["to_scrape"]
        dS.seen = seen
        random.shuffle(poss_links)

        if len(poss_links) > 0:
            random.shuffle(poss_links)
            dS.to_scrape = poss_links
            #dS.to_scrape = [] #Uncomment to clean scraping array
            #dS.build() #Uncomment to clean scraping array
            print("Ingesting ", len(dS.to_scrape), " links")
        else:
            print("Building new scrape model")
            dS.build()
        while(len(dS.seen) < len(seen) + 100):
            dS.generate_card_pool()

    except:
        obj = {"to_scrape": dS.to_scrape}
        pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise

    
scrape_sites()