import pickle, random, traceback, threading, sys, copy

from lib.deckScraper import DeckScraper
from lib.cardVectorizor import Vectorizor
from lib.log import Log
from lib.tests.TestConnections import ConnectionSuite

from lib.service import DeckService

log = Log("MAIN", 1).log

prime = True
rebuild = False

def test_connection():
    ConnectionSuite()

def scrape_sites(): 
    dS = DeckScraper()
    service = DeckService()

    try:
        resp = service.get_decks()
        seen = []
        if resp["status_code"] == 200 :
            response = resp["body"]
            seen = [x["url"] for x in response]
        dS.seen = seen

        poss_links = dS.primeFromDB()

        random.shuffle(poss_links)
        log(1, f"Ingesting {len(dS.to_scrape)} links")

        log(1, f"Scraping {len(dS.to_scrape)} initially")
        startCount = copy.deepcopy(len(dS.seen)) 
        totalSeen = 0

        tried = 0
        while(totalSeen < 10000 and len(dS.to_scrape) > 0):
            if prime and tried >= 6:
                tried = 0
                log(0, "===== Searching DB =====")
                poss_links = dS.primeFromDB()

            tried += 1
            seen = copy.deepcopy(dS.seen)
            threads = list()
            log(1, f"Seen {len(dS.seen)} links")
            for index in range(1): #Threading doesn't play nicely with transactional db updates
                lock = threading.Lock()
                x = threading.Thread(target=thread_function, args=(index,dS,lock,))
                threads.append(x)
                x.start()

            for index, thread in enumerate(threads):
                thread.join()
                log(1, f"Thread {index} done")
            
            totalSeen = len(dS.to_scrape) - startCount

            if (len(dS.to_scrape) < 5) and prime:
                log(1, f"Scraped {totalSeen} links")
                poss_links = dS.primeFromDB()
                log(1, f"Scraping {len(dS.to_scrape)} initially")
                if len(poss_links) > 0:
                    random.shuffle(poss_links)
                    dS.to_scrape = poss_links

        log(1, f"Total links seen: {totalSeen}")
        log(1, f"Links remaining unprocessed {len(dS.to_scrape)}")

    except:
        if not prime:
            obj = {"to_scrape": dS.to_scrape}
            pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise

def thread_function(name, dS, lock):
    dS.generate_card_pool(lock)

def buildNewCardDB():
    log(1, "Vectorizing Cards")
    try:
        v = Vectorizor(4)
        v.load_training_sequence(True)
        v.build_clean_array(True)
    except Exception as e: 
        print(e)
        traceback.print_exc()

def vectorizeCards():
    log(1, "Vectorizing Cards")
    model_dimensionality = 2 #TODO: Change back to 4
    try:
        v = Vectorizor(model_dimensionality)
        v.load_training_sequence(False)
        v.graph_cards(True)
    except Exception as e: 
        traceback.print_exc()


if __name__ == "__main__":
    command = sys.argv[1]
    if (command == "test"):
        test_connection()
    elif  (command == "scrape"):
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