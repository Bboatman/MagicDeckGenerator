from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import http.client
import json
import numpy
from matplotlib import pyplot
import pickle
import re 
import time
import copy
import random 
import numpy as np
import csv

class Vectorizor:
    def __init__(self):
        print("Initializing")
        self.word2vec_model_path = '../models/card_vector_model.model'
        self.keyed_vector_path = '../models/card_vector.kv'
        self.training_model_path = "../models/training_seq.p"
        self.train_seq = []
        
    def load_training_sequence(self, clean=False):
        try:
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        except:
            self.get_cards_from_json()
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        if clean: 
            self.model = Doc2Vec(vector_size=50, min_count=1, epochs=40, ns_exponent=.75)
        else:
            self.model = Doc2Vec.load(self.word2vec_model_path) 
        count = len(self.model.docvecs)
        for i, phrase in enumerate(obj):
            doc = TaggedDocument(simple_preprocess(phrase), [i + count])
            self.train_seq.append(doc)

    def train_model(self, build = False):
        if build: 
            print("Building Vocab")
            self.model.build_vocab(self.train_seq)
        
        print("Training Model")
        self.model.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        self.model.save(self.word2vec_model_path)

    def vectorize(self, card_array, n_components=3, save_to_db=False):
        arr = []
        name_array = []
        cleaned_array = []
        for t in card_array: 
            if (t.name not in name_array):
                vec = self.model.infer_vector(t.tokenize_text())
                arr.append(vec)
                name_array.append(t.name)
                cleaned_array.append(t)
        pca = PCA(n_components=n_components)
        print("Running PCA on data set")
        result = pca.fit_transform(np.array(arr))

        print("Mapping Cards")
        if (n_components == 3):
            for i,c in enumerate(cleaned_array):
                pca_1, pca_2, pca_3 = result[i]
                c.text_vector_1 = pca_1.item()
                c.text_vector_2 = pca_2.item()
                c.text_vector_3 = pca_3.item()
                if(save_to_db): c.save_to_db()
            print("Cards Saved")
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

    def get_cards_from_json(self, update_training_model= False, \
        write_to_db = False, progress_print = False):
        print("Getting cards from JSON")
        json_file = open('../models/scryfall-default-cards.json')
        data = json.load(json_file)
        json_file.close()

        if (update_training_model):
            obj = []
        else:
            try:
                obj = pickle.load( open( self.training_model_path, "rb" ) )
            except: 
                obj = []
                update_training_model = True

        count = 0
        card_array = []

        for entry in data:
            c = Card(entry)
            card_array.append(c)
            count += 1
            obj += c.tokenize_text()
            if len(obj)%2000 == 0:
                if (progress_print):
                    print(str(count) + " Processed")
                    print(obj[-10:])
                if (update_training_model):
                    pickle.dump(obj, open( self.training_model_path, "wb" ) )

        return card_array

    
    def graph_cards(self):
        arr = []
        card_array = self.get_cards_from_json()
        name_array = []
        cleaned_array = []
        for t in card_array: 
            if (t.name not in name_array):
                vec = self.model.infer_vector(t.tokenize_text())
                arr.append(vec)
                name_array.append(t.name)
                cleaned_array.append(t)
        pca = PCA(n_components=2)
        print("Running PCA on data set")
        result = pca.fit_transform(np.array(arr))
        point_array = []
        for i,c in enumerate(cleaned_array):
            color = "#777777"
            pca_1, pca_2 = result[i]
            if (c.color_identity > 5):
                color = "#FFD700"
            elif (c.color_identity == 5): #White
                color = "#FFFFFF"
            elif (c.color_identity == 4): #Black
                color = "#000000"
            elif (c.color_identity == 3): #Green
                color = "#008000"
            elif (c.color_identity == 2): #Blue
                color = "#0000FF"
            elif (c.color_identity == 1): #Red
                color = "#FF0000"
            point = [c.name, color, pca_1, pca_2]
            point_array.append(point)
        with open('../models/2dGraphPoints.csv', 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows(point_array)

        csvFile.close()

class Card:
    delimiters = "\n", ".", ",", ":"
    regexPattern = '|'.join(map(re.escape, delimiters))
    id = 0
    multiverse_id = 0
    name = ''
    card_type = ''
    rarity = ''
    cmc = 0
    toughness = '~'
    power = '~'
    text_vector_1 = 0
    text_vector_2 = 0
    text_vector_3 = 0
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

    def tokenize_text(self):
        text = self.text.lower()
        name = self.name.lower()
        txt = text.replace(name, "~self~")
        arr = re.split(self.regexPattern, txt)
        tokens = [x.strip() for x in arr]
        tokens = filter(None, tokens)
        return tokens

    def save_to_db(self):
        headers = {'Content-type': 'application/json'}
        d = copy.deepcopy(self.__dict__) 
        if 'text' in d:
            d.pop('text') 
        body = json.dumps(d)

        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('POST', '/api/cards/', body, headers)

def primeModel(write_to_db):
    v = Vectorizor()
    with open(v.training_model_path, "wb" ) as f:
        pickle.dump([], f)
    card_array = v.get_cards_from_json(v, write_to_db)
    model = Doc2Vec(vector_size=50, min_count=1, epochs=40, ns_exponent=.75)   
    with open(v.word2vec_model_path, "wb" ) as f:
        model.save(v.word2vec_model_path)
    
    v.load_training_sequence(True)
    v.train_model(True)
    v.vectorize(card_array, save_to_db=write_to_db)
    v.graph_cards()

def buildModel(clean = False):
    v = Vectorizor()
    v.load_training_sequence()
    v.train_model(clean)
    v.graph_cards()

#primeModel(True)
buildModel()