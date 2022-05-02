import unittest
from decouple import config
from importlib import import_module
from ..lib.service import DeckService

endpoint = config("HOST")


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.service = DeckService()

    def get_decks(self):
        resp = self.service.get_decks()
        self.assertEqual(resp["status_code"], 200)

    def get_cards(self):
        resp = self.service.get_cards()
        self.assertEqual(resp["status_code"], 200)
        self.assertGreater(len(resp["body"]), 0)

    def get_unseen(self):
        resp = self.service.get_unseen()
        self.assertEqual(resp["status_code"], 200)

    def post_deck(self):
        resp = self.service.post_deck()
        self.assertEqual(resp["status_code"], 200)


class ConnectionSuite():
    def __init__(self):
        suite = unittest.TestSuite()
        suite.addTest(ConnectionTests("get_decks"))
        suite.addTest(ConnectionTests("get_cards"))
        runner = unittest.TextTestRunner()
        runner.run(suite)
