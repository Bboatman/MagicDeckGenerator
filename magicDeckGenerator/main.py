import pickle, random, gc, csv, time
from deckScraper import DeckScraper
from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA
from gensim.utils import simple_preprocess
import numpy as np


#dS.prime()
#dS.build()


def scrape_sites():
    dS = DeckScraper()
    try:
        obj = pickle.load( open( "./models/pickledLinks.p", "rb" ) )
        poss_links = obj["to_scrape"]
        random.shuffle(poss_links)
        dS.seen = obj['seen']
        #dS.to_scrape = [] #Uncomment to clean scraping array
        if len(poss_links) > 0:
            random.shuffle(poss_links)
            print("Ingesting ", len(dS.to_scrape), " links")
            dS.to_scrape = poss_links
        else:
            print("Building new scrape model")
            dS.build()
        while(len(dS.to_scrape) > 0):
            dS.generate_card_pool()

    except:
        obj = {"seen" : dS.seen, "to_scrape": dS.to_scrape}
        pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise

    
scrape_sites()