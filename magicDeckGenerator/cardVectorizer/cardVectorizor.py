from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
from sklearn.manifold import TSNE
import http.client
import json
import numpy
from matplotlib import pyplot
import pickle
import re 
import time
import copy
import random 

class Vectorizor:
    def __init__(self):
        print("Intializing")
        delimiters = "\n", ".", ",", ":"
        self.regexPattern = '|'.join(map(re.escape, delimiters))
        self.word2vec_model_path = '../models/card_vector_model.model'
        self.keyed_vector_path = '../models/card_vector.kv'
        self.training_model_path = "../models/training_seq.p"
        self.train_seq = []
        
    def load_training_sequence(self):
        obj = pickle.load( open( self.training_model_path, "rb" ) )
        if len(obj) == 0: 
            self.model = Doc2Vec(vector_size=50, min_count=1, epochs=40, ns_exponent=.75)
        else:
            self.model = Doc2Vec.load(self.word2vec_model_path) 
        count = len(self.model.docvecs)
        for i, phrase in enumerate(obj):
            doc = TaggedDocument(simple_preprocess(phrase), [i + count])
            self.train_seq.append(doc)

    def clean_training_model(self):
        with open(self.training_model_path, "wb" ) as f:
            pickle.dump([], f)

    def tokenize_text(self, text, name):
        txt = text.replace(name, "~self~")
        arr = re.split(self.regexPattern, txt)
        tokens = [x.strip() for x in arr]
        tokens = filter(None, tokens)
        return tokens

    def train_model(self, build = False):
        print(build)
        if build: self.model.build_vocab(self.train_seq)
        self.model.train(self.train_seq, total_examples=self.model.corpus_count, epochs=self.model.epochs)
        self.model.save(self.word2vec_model_path)
        
    def fit_term(self, term_vector):
        term_array = self.model.infer_vector(term_vector)
        tsne = TSNE(n_components=3)
        result = tsne.fit_transform(term_array)
        return result

    def graph_vocab(self):
        X = self.model[self.model.wv.vocab]
        tsne = TSNE(n_components=3)
        result = tsne.fit_transform(X)
        # create a scatter plot of the projection
        pyplot.scatter(result[:, 0], result[:, 1])
        words = list(self.model.wv.vocab)
        for i, word in enumerate(words):
            pyplot.annotate(word, xy=(result[i, 0], result[i, 1]))
        pyplot.show()

class Card:
    id = 0
    multiverse_id = 0
    name = ''
    card_type = ''
    rarity = ''
    cmc = 0
    toughness = '~'
    power = '~'
    text_tsne_1 = 0
    text_tsne_2 = 0
    text_tsne_3 = 0
    color_identity = ''
    text = ''

    def __str__(self):
        return self.name + " - " + str(self.multiverse_id) + ": " + self.card_type + "\n" + \
            self.rarity + ", " + str(self.cmc) + "\n" + self.color_identity + " " + \
            self.power + "/" + self.toughness

    def __init__(self, json_info):
        if 'multiverse_ids' in json_info and len(json_info['multiverse_ids']) > 0:
            self.multiverse_id = json_info['multiverse_ids'][0]
        self.name = json_info['name']
        if 'power' in json_info:
            self.power = json_info['power']
        else: 
            self.power = "~"
        if 'toughness' in json_info:
            self.toughness = json_info['toughness']
        else :
            self.toughness = "~"
        if 'oracle_text' in json_info:
            self.text = json_info['oracle_text']
        self.card_type = json_info['type_line'].split("—")[0].strip()
        rarity = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3}
        self.rarity = rarity[json_info['rarity'].strip().lower()]
        self.cmc = int(json_info['cmc'])
        self.generate_color_identity(json_info['color_identity'])

    def generate_color_identity(self, color_array):
        if len(color_array) == 0:
            self.color_identity = 0
        else:
            color_identity = ''
            if ('R' in color_array):
                color_identity += 'R'
            if ('U' in color_array):
                color_identity += 'U'
            if ('G' in color_array):
                color_identity += 'G'
            if ('B' in color_array):
                color_identity += 'B'
            if ('W' in color_array):
                color_identity += 'W'

            choices = {'C': 0, 'R': 1, 'U': 2, 'G': 3, \
            'B': 4, 'W': 5, 'RU': 6, 'RG': 7, 'RB': 8, \
            'RW': 9, 'UG': 10, 'UB': 11, 'UW': 12, 'GB': 13, \
            'GW': 14, 'BW': 15, 'RUG': 16, 'RUB': 17, \
            'RUW': 18, 'RGB': 19, 'RGW': 20, 'RBW': 21, \
            'UGB': 22, 'UGW': 23, 'UBW': 24, 'GBW': 25, \
            'RUGB': 26, 'RUGW': 27, 'RUBW': 28, 'RGBW': 29, \
            'UGBW': 30, 'RUGBW': 31}
            self.color_identity = choices[color_identity]

    def save_to_db(self):
        headers = {'Content-type': 'application/json'}
        d = copy.deepcopy(self.__dict__) 
        if 'text' in d:
            d.pop('text') 
        body = json.dumps(d)

        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('POST', '/api/cards/', body, headers)
        response = conn.getresponse()
    
def loadData(start_pt = 0, write_to_db = False):
    v = Vectorizor()
    json_file = open('../models/scryfall-default-cards.json')
    data = json.load(json_file)
    json_file.close()
    obj = pickle.load( open( v.training_model_path, "rb" ) )
    count = 0
    for entry in data[start_pt:]:
        c = Card(entry)
        if write_to_db: c.save_to_db()
        count += 1
        obj += v.tokenize_text(c.text, c.name)
        if len(obj)%100 == 0:
            print(str(count) + " Processed")
            print(obj[-10:])
            pickle.dump(obj, open( v.training_model_path, "wb" ) )

def buildModel(clean = False):
    v = Vectorizor()
    if clean: v.clean_training_model()
    v.load_training_sequence()
    v.train_model(clean)
    v.graph_vocab()

buildModel(True)