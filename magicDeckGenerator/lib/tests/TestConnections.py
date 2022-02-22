import json, http.client, unittest, requests
from decouple import config
from importlib import import_module

endpoint = config("HOST")

class TestSuite(unittest.TestCase):
    def setUp(self):
        self.headers = {'Content-type': 'application/json'}
        resp = requests.post(endpoint + "/api/authenticate", data=json.dumps({"username": "admin", "password": "admin"}), headers=self.headers)
        token = json.loads(resp.text)["id_token"]
        self.headers["Authorization"] = "Bearer " + token

    def authenticate(self):
        resp = requests.post(endpoint + "/api/authenticate", data=json.dumps({"username": "admin", "password": "admin"}), headers=self.headers)
        token = json.loads(resp.text)["id_token"]
        self.headers["Authorization"] = "Bearer " + token
        self.assertEqual(resp.status_code, 200)

    def get_decks(self):
        resp = requests.get(endpoint + "/api/decks", headers=self.headers)
        print(resp.text)
        self.assertEqual(resp.status_code, 200)
    
    def get_unseen(self):
        resp = requests.get(endpoint + "/api/unseen", headers=self.headers)
        print(resp.text)
        self.assertEqual(resp.status_code, 200)

    def post_deck(self):
        resp = requests.post(endpoint + "/api/decks", headers=self.headers)
        self.assertEqual(resp.status_code, 200)

class ConnectionSuite():
    def __init__(self):
        suite = unittest.TestSuite()
        suite.addTest(TestSuite("authenticate"))
        suite.addTest(TestSuite("get_decks"))
        # suite.addTest(TestSuite("get_unseen"))
        # suite.addTest(TestSuite("authenticate"))
        runner = unittest.TextTestRunner()
        runner.run(suite)