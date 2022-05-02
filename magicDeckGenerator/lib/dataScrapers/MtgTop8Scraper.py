from bs4 import BeautifulSoup
from ..Deck import Deck
from ..DeckMember import DeckMember
from ..log import Log
from .AbstractDataScraper import AbstractDataScraper, FoundLinksResult

priming_urls = [
    {"parent": 'https://www.mtgtop8.com/', "url": "format_limited"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PAU"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PEA"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=BL"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=MO"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=PI"},
    {"parent": 'https://www.mtgtop8.com/', "url": "format?f=ST"}
]

log = Log("MtgTop8 SCRAPER", 0).log


class MtgTop8Scraper(AbstractDataScraper):
    def __init__(self, max_results_per_page):
        self.priming_urls = priming_urls
        self.max_results_per_page = max_results_per_page
        self.url_parent = 'https://www.mtgtop8.com/'
        self.search_url = 'search'
        self.seen_urls = []

    def get_html_for_scrape(self, url: str):
        url = self.url_parent + url
        return super().get_html_for_scrape(url)

    def post_request_to_scrape(self, body: object):
        url = self.url_parent + self.search_url
        return super().post_request_to_scrape(url, body)

    def search_for_card_string(self, card_string: str):
        body = {
            "compet_check[P]": 1,
            "compet_check[M]": 1,
            "compet_check[C]": 1,
            "compet_check[R]": 1,
            "MD_check": 1,
            "SB_check": 1,
            "cards": card_string
        }

        soup = self.post_request_to_scrape(body)
        found_links: FoundLinksResult = self.get_links_from_html(soup)
        found_links.set_card_string(card_string)
        return found_links

    def get_links_from_html(self, soup: BeautifulSoup):
        local_count = 0
        url_list = []
        for link_object in soup.find_all('a', attrs={'href': True}):
            link_url: str = link_object["href"]
            if "?e" in link_url:
                if 'event' not in link_url:
                    link_url = 'event' + link_url
                link_url = link_url.split("&")[0]
                if link_url not in self.seen_urls and local_count < self.max_results_per_page:
                    local_count += 1
                    self.seen_urls.append(link_url)
                    url_list.append(link_url)
                else:
                    log(0, f"Found {local_count} links in MtgTop8")
                    return FoundLinksResult(local_count, url_list, self.url_parent)
        return FoundLinksResult(local_count, url_list, self.url_parent)

    def build_deck_from_html(self, source_url: str):
        soup = self.get_html_for_scrape(source_url)
        members = soup.find_all("div", attrs={"class": "deck_line"})
        titleOptions = soup.find(
            "div", attrs={"class": "chosen_tr"}).find_all("a", attrs={'href': True})
        name = ""
        for t in titleOptions:
            if "?e" in t['href']:
                name = t.text
        deck = Deck(name, source_url)
        try:
            for item in members:
                count = item.contents[0].strip()
                name = item.find("span", attrs={"class": "L14"}).contents[0]
                card_id = 0
                deck_member = DeckMember(name, card_id, count)
                deck.add_member_to_deck(deck_member)

        except Exception as e:
            log(0, "Failure to parse cards on {source_url} in MtgTop8")
            log(0, e)
            return None

        return deck
