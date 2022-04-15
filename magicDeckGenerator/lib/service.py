import requests, json
from decouple import config
from importlib import import_module

endpoint = config("HOST")

class DeckService:
    def __init__(self):
        self.headers = {'Content-type': 'application/json'}
        self.authenticate()
        
    def authenticate(self):
        resp = requests.post(endpoint + "/api/authenticate", data=json.dumps({"username": "admin", "password": "admin"}), headers=self.headers)
        token = json.loads(resp.text)["id_token"]
        self.headers["Authorization"] = "Bearer " + token

    def get_decks(self):
        resp = requests.get(endpoint + "/api/decks", headers=self.headers)
        return {"status_code": resp.status_code, "body": json.loads(resp.text)}
        
    def get_cards(self):
        resp = requests.get(endpoint + "/api/cards", headers=self.headers)
        return {"status_code": resp.status_code, "body": json.loads(resp.text)}
    
    def get_unseen(self):
        resp = requests.get(endpoint + "/api/unseen", headers=self.headers)
        body = json.loads(resp.text)
        print("=====")
        print(len(body))
        return {"status_code": resp.status_code, "body": body}

    def post_deck(self, deck):
        resp = requests.post(endpoint + "/api/decks", json.dumps(deck), headers=self.headers)
        return {"status_code": resp.status_code}
    
    def post_bulk_cards(self, card_array: list):
        if (card_array[0]["id"]):
            resp = requests.patch(endpoint + "/api/cards/bulk", json.dumps(card_array), headers=self.headers)
        else:
            resp = requests.post(endpoint + "/api/cards/bulk", json.dumps(card_array), headers=self.headers)
        return {"status_code": resp.status_code, "body": json.loads(resp.text)}
    
    def post_card(self, card):
        resp = requests.post(endpoint + "/api/cards", json.dumps(card), headers=self.headers)
        return {"status_code": resp.status_code}