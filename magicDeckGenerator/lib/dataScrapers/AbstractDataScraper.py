from bs4 import BeautifulSoup
from matplotlib.pyplot import cla
from numpy import number
import requests

from ..log import Log
from ..service import DeckService
from ..scraper import Scraper

log = Log("ABSTRACT SCRAPER", 0).log


class AbstractDataScraper:
    def __init__(self, max_results_per_page: int):
        pass

    def search_for_card_string(self, card_string: str):
        """
            Generates a list of scrapable links from a searchable string keyword

            Args:
                card_string: str

            Returns:
                scrapable_urls: FoundLinksResult
        """
        pass

    def get_links_from_html(self, soup: BeautifulSoup):
        """
            Generates a list of scrapable links from given html

            Args:
                soup: BeautifulSoup

            Returns:
                scrapable_urls: FoundLinksResult
        """
        pass

    def build_deck_from_html(self, source_url: str):
        """
            Build the deck object from given html

            Args:
                source_url: str

            Returns:
                deckObject: Deck 
        """
        pass

    def get_html_for_scrape(self, url: str):
        """
            Gets a BeautifulSoup to scrape for data from a url

            Args:
                url: str

            Returns:
                soup: BeautifulSoup
        """

        raw_html = Scraper(url).simple_get()
        soup = BeautifulSoup(raw_html, 'html.parser')
        return soup

    def post_request_to_scrape(self, url: str, body: object):
        """
            Gets a BeautifulSoup to scrape for data from a url through post request

            Args:
                url: str

            Returns:
                soup: BeautifulSoup
        """
        try:
            raw_html = requests.post(url, json=body)
            soup = BeautifulSoup(raw_html.text, 'html.parser')
            return soup
        except:
            log(0, "Failure to get data from src {url}")
            return


class FoundLinksResult:
    def __init__(self, found_count: number, url_list: list, url_parent: str, ):
        self.found_count = found_count
        self.url_list = url_list
        self.url_parent = url_parent

    def __str__(self):
        return "found_count: " + str(self.found_count) + "\n url_parent: " + str(self.url_parent) + "\n" + \
            " url_list: " + str(self.url_list)

    def set_card_string(self, card_string: str):
        self.card_str = card_string
