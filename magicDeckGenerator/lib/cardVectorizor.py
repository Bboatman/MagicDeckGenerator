import json
import math
import pickle
import re
import time
import copy
import gc
import os
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
from sklearn.manifold import TSNE

from .Models.Card import Card
from .log import Log
from .service import DeckService
import os
import urllib.request
from requests import get

log = Log("CARD VECTORIZOR", 0).log
update_local_json = False


class Vectorizor:
    def __init__(self, model_dimensionality: int = 5):
        log(0, "Initializing")
        dirname = os.path.dirname(__file__)
        self.model_dimensionality = model_dimensionality
        self.card_json_path = os.path.join(
            dirname, '../models/scryfall-default-cards.json')
        self.word2vec_model_path = os.path.join(
            dirname, '../models/card_vector_model.model')
        self.model_dimensionality_path = os.path.join(
            dirname, '../models/card_' + str(self.model_dimensionality) + 'd_model.model')
        self.twod_model_path = os.path.join(
            dirname, '../models/card_2d_model.model')
        self.keyed_vector_path = os.path.join(
            dirname, '../models/card_vector.kv')
        self.training_model_path = os.path.join(
            dirname, "../models/training_seq.p")
        self.card_data_path = os.path.join(dirname, "../models/card_data.p")
        self.train_seq = []
        self.service = DeckService()

    def load_training_sequence(self, clean: bool = False):
        if (clean):
            url = 'https://api.scryfall.com/bulk-data/oracle-cards'
            path = os.getcwd()  # this only works if running from main
            path += "/models"

            print('Beginning file download with urllib2...')
            try:
                resp = get(url)
                downloadLoc = json.loads(resp.text)["download_uri"]
                print(downloadLoc)
                print(path)
                urllib.request.urlretrieve(
                    downloadLoc, path + "/scryfall-default-cards.json")
            except:
                print("Issue connecting to card ref download")

        try:
            obj = pickle.load(open(self.training_model_path, "rb"))
        except Exception as e:
            print(e)
            self.get_cards_from_json()
            obj = pickle.load(open(self.training_model_path, "rb"))
        if clean:
            log(0, "Cleaning Training Model")
            self.twodmodel = Doc2Vec(
                vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
        else:
            try:
                self.twodmodel = Doc2Vec.load(self.twod_model_path)
            except:
                log(1, "Failed to load")
                self.twodmodel = Doc2Vec(
                    vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
                clean = True

        count = len(self.twodmodel.docvecs)
        for i, phrase in enumerate(obj):
            doc = TaggedDocument(simple_preprocess(phrase), [i + count])
            self.train_seq.append(doc)

        if clean:
            self.train_model(True)

    def train_model(self, build: bool = False):
        if build:
            log(0, "Building Vocab")
            self.twodmodel.build_vocab(self.train_seq)

        log(0, "Training Model")
        self.twodmodel.train(self.train_seq, total_examples=self.twodmodel.corpus_count,
                             epochs=self.twodmodel.epochs)
        if build:
            f = open(self.word2vec_model_path, "w+")
            f.close()
            f = open(self.model_dimensionality_path, "w+")
            f.close()
            f = open(self.twod_model_path, "w+")
            f.close()
        self.twodmodel.save(self.twod_model_path)

    def get_cards_from_json(self, update_training_model: bool = False,
                            write_to_db: bool = False, progress_print: bool = False):
        log(0, "Getting cards from JSON")
        t = time.time()
        json_file = open(self.card_json_path)
        data = json.load(json_file)
        json_file.close()

        if (update_training_model):
            obj = []
        else:
            try:
                obj = pickle.load(open(self.training_model_path, "rb"))
            except:
                obj = []
                update_training_model = True

        count = 0
        card_array = []

        for entry in data:
            c = Card(entry)
            try:
                c.cardType = c.get_cardType(self.twodmodel)
            except:
                pass
            card_array.append(c)
            count += 1
            obj += c.tokenize_text()
            if len(obj) % 8000 == 0:
                if (progress_print):
                    log(0, f"{count} Processed")
                if (update_training_model):
                    pickle.dump(obj, open(self.training_model_path, "wb"))

        t = time.time() - t
        log(0, f"Got {len(card_array)} cards in {t} time")
        return card_array

    def decompose_data(self, cards: list, save_to_db: bool):
        t = time.time()
        alg = TSNE(n_components=2)

        data = []
        referencable_cards = []
        for c in cards:
            c.simple_vec = np.array(c.simple_vec)
            if c.simple_vec is None or c.simple_vec.size != 2:
                print("Card {} has no descriptive text.".format(c.name))
            else:
                data.append(c.simple_vec)
                referencable_cards.append(c)

        if type(data).__module__ != 'numpy':
            print(data[0])
            data = np.array(data)

        first_pass = alg.fit_transform(data)
        print("PRINTING FIRST CARD:\n", data[0])
        log(0, "First Pass Complete")
        card_values = []
        mean = np.mean(first_pass)
        std = np.std(first_pass)
        print(mean, std)

        for c in referencable_cards:
            card_values.append([c.cardType[0], c.cardType[1], c.get_colorIdentity(mean, std), c.get_cmc(mean, std),
                                c.get_toughness(mean, std), c.get_power(mean, std)])

        card_values = np.array(card_values)
        first_pass = np.append(first_pass, card_values, axis=1)

        alg = TSNE(n_components=2)

        gc.collect()
        log(0, "Starting Second Pass")
        result = alg.fit_transform(first_pass)

        t = time.time() - t
        log(0,
            f"Running TSNE on 2 dimensions, completed in {t} time")
        ret = []

        save_arr = []
        for i, c in enumerate(referencable_cards):
            x, y = result[i].tolist()
            c.save_decomp_res(x, y)
            name = c.name
            hexVal = c.generate_color_hex()
            save_arr.append(c)
            ret.append([name, hexVal] + result[i].tolist())

        if (save_to_db):
            self.bulk_update_and_propogate_changes(referencable_cards)

        log(0, "Data Saved")
        return result

    def build_clean_array(self, save_to_db):
        seen = {}
        to_create_array = []
        resp = self.service.get_cards()

        response = resp["body"]
        for card in response:
            c = Card(card)
            key = c.name
            seen[key] = c

        print(len(seen))

        card_array = self.get_cards_from_json(True, True, True)

        log(0, "Cleaning Card Array")
        for t in card_array:
            key = t.name
            if (key not in seen):
                to_create_array.append(t)
                self.generate_text_vector(t, seen)
                print(t)
                seen[key] = t
            else:
                existing_card = seen[key]
                existing_card.text = t.text
                existing_card.cardType = t.cardType
                existing_card.toughness = t.toughness
                existing_card.power = t.power
                self.generate_text_vector(existing_card, seen)

        if len(to_create_array) > 0:
            print("Doing Bulk update")
            seen = self.bulk_update_and_propogate_changes(
                to_create_array, seen)

        ret = [x for x in list(seen.values()) if x != None]
        print(ret[0])
        return ret

    def bulk_update_and_propogate_changes(self, to_create_array: list, master_obj={}):
        body = [x.get_db_value() for x in to_create_array]
        if (len(body) > 0):
            save_response = self.service.post_bulk_cards(body)
            print(save_response)
            if (save_response["status_code"] == 201):
                processed_cards: list = []
                for new_card in save_response['body']:
                    c: Card = Card(new_card)
                    self.generate_text_vector(c, master_obj)
                    processed_cards.append(c)
                return master_obj

    def generate_text_vector(self, card, master_obj):
        key = card.name
        tokens = card.tokenize_text()
        card.simple_vec = np.array(self.twodmodel.infer_vector(tokens))
        master_obj[key] = card

    def graph_cards(self, save_to_db):
        cleaned_array = self.build_clean_array(save_to_db)
        log(0, "Running Graphing on Data Set")
        self.decompose_data(cleaned_array, save_to_db)
