import unittest

from lib.dataScrapers.MtgTop8Scraper import MtgTop8Scraper
from lib.log import Log
from lib.dataScrapers.AbstractDataScraper import FoundLinksResult
log = Log("TEST MTGTOP8", 0).log


class Top8Tests(unittest.TestCase):
    def setUp(self):
        self.scraper = MtgTop8Scraper(5)
        self.test_deck = "event?e=35573"
        self.test_non_edh_deck = "event?e=35852"
        self.test_card = "static orb"

    def get_html_for_scrape(self):
        soup = self.scraper.get_html_for_scrape(self.test_deck)
        self.assertGreater(
            len(soup.text), 0, "Soup result is empty when it is known to be populated")

    def post_request_to_scrape(self):
        body = {
            "compet_check[P]": 1,
            "compet_check[M]": 1,
            "compet_check[C]": 1,
            "compet_check[R]": 1,
            "MD_check": 1,
            "SB_check": 1,
            "cards": self.test_card
        }
        soup = self.scraper.post_request_to_scrape(body)
        self.assertGreater(
            len(soup.text), 0, "Soup result is empty when it is known to be populated")

    def get_links_from_html(self):
        soup = self.scraper.get_html_for_scrape(self.test_deck)
        found_links = self.scraper.get_links_from_html(soup)
        self.assertGreater(len(found_links.url_list), 0,
                           "List is empty when it is know to be populated")
        self.assertTrue(len(found_links.url_list) ==
                        len(set(found_links.url_list)), "Duplicates exist in list")
        self.assertTrue(all(
            ['event' in x for x in found_links.url_list]), "Missing correct url formatting")
        self.assertTrue(
            all(['&' not in x for x in found_links.url_list]), "Has extra data in list")

    def search_for_card_string(self):
        found_links = self.scraper.search_for_card_string(self.test_card)
        self.assertGreater(len(found_links.url_list), 0,
                           "List is empty when it is know to be populated")
        self.assertTrue(len(found_links.url_list) ==
                        len(set(found_links.url_list)), "Duplicates exist in list")
        self.assertTrue(all(
            ['event' in x for x in found_links.url_list]), "Missing correct url formatting")
        self.assertTrue(
            all(['&' not in x for x in found_links.url_list]), "Has extra data in list")

    def build_deck_from_html(self):
        deck = self.scraper.build_deck_from_html(self.test_deck)
        count = sum([int(x.count) for x in deck.deckMembers])
        self.assertEqual(count,
                         100, "Deck count does not match anticipated, returning {count}")
        self.assertNotEqual(deck.name, deck.url, "Name parsing is broken")
        self.assertEqual(deck.name, "isamaru",
                         "Name parsing is broken, returning {deck.name}")

    def build_deck_check_increment_function(self):
        deck = self.scraper.build_deck_from_html(self.test_non_edh_deck)
        count = sum([int(x.count) for x in deck.deckMembers])
        self.assertEqual(count,
                         75, "Deck count does not match anticipated, returning {count}")
        self.assertNotEqual(deck.name, deck.url, "Name parsing is broken")
        self.assertEqual(deck.name, "crashing footfalls cascade",
                         "Name parsing is broken, returning {deck.name}")


class Top8Suite():
    def __init__(self):
        suite = unittest.TestSuite()
        suite.addTest(Top8Tests("get_html_for_scrape"))
        suite.addTest(Top8Tests("post_request_to_scrape"))
        suite.addTest(Top8Tests("get_links_from_html"))
        suite.addTest(Top8Tests("search_for_card_string"))
        suite.addTest(Top8Tests("build_deck_from_html"))
        suite.addTest(Top8Tests("build_deck_check_increment_function"))
        runner = unittest.TextTestRunner()
        runner.run(suite)
