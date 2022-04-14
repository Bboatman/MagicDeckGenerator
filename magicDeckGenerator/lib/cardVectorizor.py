import json, math, pickle, re, time, copy, random, csv, gc, os
import http.client
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA
from sklearn import preprocessing
from matplotlib import pyplot
from .log import Log
from .service import DeckService
import os
from decouple import config

log = Log("CARD VECTORIZOR", 0).log


class Vectorizor:
    def __init__(self, model_dimensionality = 5):
        log(0, "Initializing")
        dirname = os.path.dirname(__file__)
        self.model_dimensionality = model_dimensionality
        self.card_json_path = os.path.join(dirname, '../models/scryfall-default-cards.json')
        self.word2vec_model_path = os.path.join(dirname,'../models/card_vector_model.model')
        self.model_dimensionality_path = os.path.join(dirname, '../models/card_' + str(self.model_dimensionality) + 'd_model.model')
        self.twod_model_path = os.path.join(dirname,'../models/card_2d_model.model')
        self.keyed_vector_path = os.path.join(dirname,'../models/card_vector.kv')
        self.training_model_path = os.path.join(dirname,"../models/training_seq.p")
        self.card_data_path = os.path.join(dirname,"../models/card_data.p")
        self.train_seq = []
        self.service = DeckService()
        
    def load_training_sequence(self, clean=False):
        try:
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        except Exception as e: 
            print(e)
            self.get_cards_from_json()
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        if clean: 
            log(0, "Cleaning Training Model")
            self.twodmodel = Doc2Vec(vector_size=2, min_count=1, epochs=1, ns_exponent=.75) #TODO Change epochs back to 40
            self.multimodel = Doc2Vec(vector_size=self.model_dimensionality, min_count=1, epochs=1, ns_exponent=.75) #TODO Change epochs back to 40
            self.model = Doc2Vec(vector_size=52, min_count=1, epochs=1, ns_exponent=.75)  #TODO Change epochs back to 40
        else:
            try:
                self.twodmodel = Doc2Vec.load(self.twod_model_path) 
                self.multimodel = Doc2Vec.load(self.model_dimensionality_path) 
                self.model = Doc2Vec.load(self.word2vec_model_path)
            except:
                log(1, "Failed to load")
                self.twodmodel = Doc2Vec(vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
                self.multimodel = Doc2Vec(vector_size=self.model_dimensionality, min_count=1, epochs=40, ns_exponent=.75)
                self.model = Doc2Vec(vector_size=52, min_count=1, epochs=40, ns_exponent=.75)
                clean = True
                
        count = len(self.model.docvecs)
        for i, phrase in enumerate(obj):
            doc = TaggedDocument(simple_preprocess(phrase), [i + count])
            self.train_seq.append(doc)
        
        if clean:
            self.train_model(True)

    def train_model(self, build = False):
        if build: 
            log(0, "Building Vocab")
            self.model.build_vocab(self.train_seq)
            self.twodmodel.build_vocab(self.train_seq)
            self.multimodel.build_vocab(self.train_seq)
        
        log(0, "Training Model")
        self.model.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        self.multimodel.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        self.twodmodel.train(self.train_seq, total_examples=self.model.corpus_count, \
            epochs=self.model.epochs)
        if build:
            f = open(self.word2vec_model_path, "w+")
            f.close()
            f = open(self.model_dimensionality_path, "w+")
            f.close()
            f = open(self.twod_model_path, "w+")
            f.close()
        self.model.save(self.word2vec_model_path)
        self.twodmodel.save(self.twod_model_path)
        self.multimodel.save(self.model_dimensionality_path)
        
    def get_cards_from_json(self, update_training_model= False, \
        write_to_db = False, progress_print = False):
        log(0, "Getting cards from JSON")
        t = time.time()
        json_file = open(self.card_json_path)
        data = json.load(json_file)
        json_file.close()

        if (update_training_model):
            obj = []
        else:
            try:
                obj = pickle.load(open( self.training_model_path, "rb" ))
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
            if len(obj)%2000 == 0:
                if (progress_print):
                    log(0, f"{count} Processed")
                if (update_training_model):
                    pickle.dump(obj, open( self.training_model_path, "wb" ) )
        
        t = time.time() - t
        log(0, f"Got {len(card_array)} cards in {t} time")
        return card_array

    def decompose_data(self, algorithm, n_components, cards, naive, save_to_db):
        t = time.time()
        if (algorithm == "TSNE"):
            alg = TSNE(n_components=self.model_dimensionality)
        elif (algorithm == "MDS"):
            alg = MDS(n_components=self.model_dimensionality)
        elif (algorithm == "SpectralEmbeddingNN"):
            alg = SpectralEmbedding(n_components=self.model_dimensionality, affinity="nearest_neighbors")
        elif (algorithm == "SpectralEmbeddingRBF"):
            alg = SpectralEmbedding(n_components=self.model_dimensionality, affinity="rbf")
        else:
            alg = PCA(n_components=self.model_dimensionality)

        gc.collect()
        if not naive:
            data = [c.long_vec for c in cards]
            first_pass = alg.fit_transform(np.array(data))
        else:
            first_pass = np.array([c.simple_vec for c in cards])
        
        log(0, "First Pass Complete")
        card_values = []
        mean = np.mean(first_pass)
        std = np.std(first_pass)

        for c in cards:
            card_values.append([c.cardType[0], c.cardType[1], c.get_colorIdentity(mean, std), c.get_cmc(mean, std), \
            c.get_toughness(mean, std), c.get_power(mean, std)])
        
        card_values = np.array(card_values)
        first_pass = np.append(first_pass, card_values, axis=1) 

        if (algorithm == "TSNE"):
            alg = TSNE(n_components=n_components)
        elif (algorithm == "MDS"):
            alg = MDS(n_components=n_components)
        elif (algorithm == "SpectralEmbeddingNN"):
            alg = SpectralEmbedding(n_components=n_components, affinity="nearest_neighbors")
        elif (algorithm == "SpectralEmbeddingRBF"):
            alg = SpectralEmbedding(n_components=n_components, affinity="rbf")
        else:
            alg = PCA(n_components=n_components)

        gc.collect()
        algname = algorithm
        try:
            result = alg.fit_transform(first_pass)
        except:
            log(1, "Failed second pass, defaulting to PCA")
            alg = PCA(n_components=n_components)
            result = alg.fit_transform(first_pass)

        t = time.time() - t
        log(0, f"Running {algorithm} on {n_components} dimensions, completed in {t} time")
        ret = []

        if naive:
            algname = "naive" + algorithm
        save_arr = []
        for i,c in enumerate(cards):
            x, y = result[i].tolist()
            if (save_to_db):
                save_arr.append(c.save_decomp_res(algname, x, y, self.model_dimensionality))
            name = c.name
            hexVal = c.generate_color_hex()
            ret.append([name, hexVal] + result[i].tolist())
        

        if (save_to_db):
            body = json.dumps(save_arr)
            print(save_arr[0])
        
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, algname + str(self.model_dimensionality) + "dGraphPoints.csv")
        fieldnames = ['name', 'color']
        if (n_components == 2):
            fieldnames = ['name', 'color', 'x', 'y']
        elif (n_components == 3):
            fieldnames = ['name', 'color', 'x', 'y', 'z']
        else:
            fieldnames += [str(x) for x in range(n_components)]

        log(0, "Data Saved")
        return result
    
    def build_clean_array(self, save_to_db):
        seen = {}
        to_create_array = []
        resp = self.service.get_cards()

        response = resp["body"]
        for card in response:
            c = Card()
            c.build_from_server(card)
            key = c.name
            seen[key] = c
            
        card_array = self.get_cards_from_json(True, True, True)

        log(0, "Cleaning Card Array")
        for t in card_array: 
            key = t.name
            if (key not in seen):
                tokens = t.tokenize_text()
                t.simple_vec = self.multimodel.infer_vector(tokens)
                t.long_vec = self.model.infer_vector(tokens) # There's something wrong with this??
                to_create_array.append(t)
                print(t)
                seen[key] = t
        
        if len(to_create_array) > 0:
            body = [x.get_db_value() for x in to_create_array]
            if (len(body) > 0):
                save_response = self.service.post_bulk_cards(body)
                print("==== SAVING NEW CARDS ====")
                for new_card in save_response['body']:
                    c = Card()
                    c.build_from_server(new_card)
                    key = c.name
                    seen[key] = c
        print(seen["static orb"])
        return [x for x in list(seen.values()) if x != None]


    def graph_cards(self, save_to_db):
        cleaned_array = self.build_clean_array(save_to_db)
        log(0, "Running Graphing on Data Set")
        algs = ["PCA", "TSNE", "SpectralEmbeddingRBF"]
        for alg in algs:
            try:
                gc.collect()
                self.decompose_data(alg, 2, cleaned_array, False, save_to_db)
                gc.collect()
                self.decompose_data(alg, 2, cleaned_array, True, save_to_db)
                log(0, f"{alg} Done")
            except:
                log(2, f"{alg} Failed")

class Card:
    delimiters = "\n", ".", ",", ":"
    regexPattern = '|'.join(map(re.escape, delimiters))
    id = 0
    multiverse_id = 0
    name = ''
    cardType = ''
    rarity = ''
    cmc = 0
    toughness = '-1'
    power = '-1'
    colorIdentity = ''
    text = ''
    simple_vec = []
    long_vec = []

    def __str__(self):
        return "Name " + self.name + " - " + str(self.id) + ": type " + str(self.cardType) + "\n" + \
            "rarity " + str(self.rarity) + ", cmc" + str(self.cmc) + "\n color" + str(self.colorIdentity) + " " + \
            str(self.power) + "/" + str(self.toughness)

    def __init__(self, json_info=None):
        if (json_info != None):
            if 'multiverse_ids' in json_info and len(json_info['multiverse_ids']) > 0:
                self.multiverse_id = json_info['multiverse_ids'][0]
            self.name = json_info['name'].lower()
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
            self.cardType = json_info['type_line'].split("—")[0].strip()
            rarity = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3, 'special': 4, 'bonus' : 5}
            self.rarity = rarity[json_info['rarity'].strip().lower()]
            self.cmc = int(json_info['cmc'])
            self.generate_colorIdentity(json_info['color_identity'])

    def build_from_server(self, info):
        self.id = info['id']
        self.name = info['name']

    def get_cardType(self, model):
        tokens = self.cardType.lower().split()
        return model.infer_vector(tokens)

    def get_toughness(self, mean=1, std=1):
        toughness = self.toughness
        if self.toughness == 'x':
            toughness = math.floor(self.cmc + (self.rarity / 2))
        elif self.toughness == '~':
            toughness = -1
        elif self.toughness == '*':
            toughness = math.floor(self.cmc + (self.rarity / 2))
        else:
            try:
                toughness = int(self.toughness)
            except:
                toughness = -2
        if (int(toughness) > 20):
            toughness = 20
        return (int(toughness) * mean) / std
    
    def get_power(self, mean=1, std=1):
        power = self.power
        if self.power == 'x':
            power = math.floor(self.cmc + (self.rarity / 2))
        elif self.power == '~':
            power = -1
        elif self.power == '*':
            power = math.floor(self.cmc + (self.rarity / 2))
        else:
            try:
                power = int(self.power)
            except:
                power = -2
        if (int(power) > 20):
            power = 20
        return (int(power) * mean) / std

    def get_rarity(self, mean=1, std=1):
        return (self.rarity * mean) / std

    def get_colorIdentity(self, mean=1, std=1):
        return (self.colorIdentity * mean) / std

    def get_cmc(self, mean=1, std=1):
        if (self.cmc > 20):
            return 20 * mean / std
        else:
            return (self.cmc * mean) / std

    def generate_colorIdentity(self, color_array):
        if len(color_array) == 0:
            self.colorIdentity = 0
        else:
            colorIdentity = ''
            if ('R' in color_array):
                colorIdentity += 'R'
            if ('U' in color_array):
                colorIdentity += 'U'
            if ('G' in color_array):
                colorIdentity += 'G'
            if ('B' in color_array):
                colorIdentity += 'B'
            if ('W' in color_array):
                colorIdentity += 'W'

            choices = {'C': 0, 'R': 1, 'U': 2, 'G': 3, \
            'B': 4, 'W': 5, 'RU': 6, 'RG': 7, 'RB': 8, \
            'RW': 9, 'UG': 10, 'UB': 11, 'UW': 12, 'GB': 13, \
            'GW': 14, 'BW': 15, 'RUG': 16, 'RUB': 17, \
            'RUW': 18, 'RGB': 19, 'RGW': 20, 'RBW': 21, \
            'UGB': 22, 'UGW': 23, 'UBW': 24, 'GBW': 25, \
            'RUGB': 26, 'RUGW': 27, 'RUBW': 28, 'RGBW': 29, \
            'UGBW': 30, 'RUGBW': 31}
            self.colorIdentity = choices[colorIdentity]

    def generate_color_hex(self):
        color = "#777777"
        if (self.colorIdentity > 5): #Multicolor Gold
            color = "#FFD700"
        elif (self.colorIdentity == 5): #White
            color = "#FFFFFF"
        elif (self.colorIdentity == 4): #Black
            color = "#000000"
        elif (self.colorIdentity == 3): #Green
            color = "#008000"
        elif (self.colorIdentity == 2): #Blue
            color = "#0000FF"
        elif (self.colorIdentity == 1): #Red
            color = "#FF0000"
        return color

    def tokenize_text(self):
        text = self.text.lower()
        name = self.name.lower()
        txt = text.replace(name, "~self~")
        arr = re.split(self.regexPattern, txt)
        tokens = [x.strip() for x in arr]
        tokens = filter(None, tokens)
        return tokens

    def save_to_db(self, service):
        headers = {'Content-type': 'application/json'}
        d = copy.deepcopy(self.__dict__) 
        if 'text' in d:
            d.pop('text') 
        if 'simple_vec' in d:
            d.pop('simple_vec')
        if 'long_vec' in d:
            d.pop('long_vec')
        d['cardType'] = float(self.cardType[0] + self.cardType[1])
        
        body = json.dumps(d)
        resp = service.post_card(body)

    def get_db_value(self):
        d = copy.deepcopy(self.__dict__) 
        if 'text' in d:
            d.pop('text') 
        if 'simple_vec' in d:
            d.pop('simple_vec')
        if 'long_vec' in d:
            d.pop('long_vec')
        d["power"] = self.get_power()
        d["toughness"] = self.get_toughness()
        d['cardType'] = float(self.cardType[0] + self.cardType[1])
        
        return json.loads(json.dumps(d))

    def save_decomp_res(self, alg, x, y, dimension):
        ret = {
            "x_value": x,
            "y_value": y,
            "algorithm": alg
        }
        ret["alg_weight"] = dimension
        ret["card"] = self.name

        return ret
