import pickle
import random
import traceback
import threading
import sys
import urllib.request
from requests import get

from lib.deckScraper import DeckScraper
from lib.cardVectorizor import Vectorizor
from lib.log import Log

from lib.service import DeckService
from tests.TestMtgTop8Scraper import Top8Suite

log = Log("MAIN", 1).log

prime = True
rebuild = False
searchCards = True
maxDecks = 1000


def scrape_sites():
    dS = DeckScraper()
    service = DeckService()

    try:
        resp = service.get_decks_urls()
        seen = []
        if resp["status_code"] == 200:
            response = resp["body"]
            seen = response
            print(response)
        dS.seen = seen

        if searchCards:
            # Do prelim check against database for searchable cards cards
            poss_links = dS.primeFromDB()
            random.shuffle(poss_links)
            dS.to_scrape = poss_links
        else:
            # Use constant urls from scraper file as priming urls
            dS.build()

        log(1, f"Ingesting {len(dS.to_scrape)} links")

        log(1, f"Scraping {len(dS.to_scrape)} initially")
        totalSeen = 0

        toTry = len(dS.to_scrape) * .4
        seenThisSearch = 0
        while(len(dS.to_scrape) > 0):
            threads = list()
            # Threading doesn't play nicely with transactional db updates
            for index in range(1):
                lock = threading.Lock()
                x = threading.Thread(target=thread_function,
                                     args=(index, dS, lock, totalSeen))
                threads.append(x)
                x.start()

            for index, thread in enumerate(threads):
                thread.join()
                log(1, f"Thread {index} done")

            if seenThisSearch % 10 == 0:
                # Prevent getting stuck processing a single searched card or deck type
                random.shuffle(dS.to_scrape)

            totalSeen += 1
            seenThisSearch += 1

            if ((len(dS.to_scrape) < 5) or seenThisSearch > toTry) and prime and totalSeen < maxDecks and searchCards:
                log(1, f"Scraped {totalSeen} links, {seenThisSearch} processed this iteration")
                log(0, "===== Searching DB =====")
                poss_links = dS.primeFromDB()
                log(1, f"Scraping {len(dS.to_scrape)} initially")
                if len(poss_links) > 0:
                    random.shuffle(poss_links)
                    dS.to_scrape = poss_links
                    toTry = len(dS.to_scrape) / 2
                    log(0, "Tries Before Research=" + str(toTry))
                seenThisSearch = 0

        log(1, f"Total links seen: {totalSeen}")
        log(1, f"Links remaining unprocessed {len(dS.to_scrape)}")

    except:
        if not prime:
            obj = {"to_scrape": dS.to_scrape}
            pickle.dump(obj, open("./models/pickledLinks.p", "wb"))
        raise


def thread_function(name, dS, lock, saveCount):
    saved = dS.generate_card_pool(lock)
    if (saved):
        saveCount += 1
    return


def buildNewCardDB(v=Vectorizor(4)):
    log(1, "Vectorizing Cards")
    try:
        v = Vectorizor(4)
        v.load_training_sequence(True)
        v.build_clean_array(False)
    except Exception as e:
        print(e)
        traceback.print_exc()


def vectorizeCards():
    log(1, "Vectorizing Cards")
    model_dimensionality = 4
    try:
        v = Vectorizor(model_dimensionality)
        v.load_training_sequence(False)
        v.graph_cards(True)
    except Exception as e:
        traceback.print_exc()


def runTests():
    Top8Suite()


if __name__ == "__main__":
    command = sys.argv[1]
    if (command == "scrape"):
        scrape_sites()
    elif (command == "vectorize"):
        vectorizeCards()
    elif (command == "buildcards"):
        buildNewCardDB()
    elif (command == 'loadnew'):
        buildNewCardDB()
        vectorizeCards()
    elif (command == 'test'):
        runTests()
    elif (command == "help"):
        print("scrape: Scrape mtgTop8 for deck data")
        print("buildcards: Process Scryfall data and save it to the database")
        print("vectorize: Use machine learning to vectorize cards and reduce their dimensionality")
        print("loadnew: download new scryfall data, update models, then vectorize to bring all cards up to date relationally")
        print("help: display all command options")
    else:
        print(
            f"'{command}' is not a valid command, try using 'help' to see all command options")
