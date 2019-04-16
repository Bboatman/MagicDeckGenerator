from deckScraper import DeckScraper
import pickle
import random
from cardVectorizer import Vectorizor

v = Vectorizor()
dS = DeckScraper(v)
#dS.prime() # This is slooooow to start

try:
    obj = pickle.load( open( "./models/pickledLinks.p", "rb" ) )
    poss_links = obj["to_scrape"]
    dS.seen = obj["seen"]
    if len(poss_links) > 0:
        random.shuffle(poss_links)
        print("Ingesting ", len(poss_links), " links")
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