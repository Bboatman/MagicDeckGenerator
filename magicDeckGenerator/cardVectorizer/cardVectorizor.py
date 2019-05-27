import json, math, pickle, re, time, copy, random, csv
import http.client
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.utils import simple_preprocess
from sklearn.manifold import TSNE, SpectralEmbedding
from sklearn.decomposition import PCA
from matplotlib import pyplot

class Vectorizor:
    def __init__(self, model_dimensionality = 5):
        print("Initializing")
        self.model_dimensionality = model_dimensionality
        self.word2vec_model_path = '../models/card_vector_model.model'
        self.model_dimensionality_path ='../models/card_' + str(self.model_dimensionality) + 'd_model.model'
        self.twod_model_path = '../models/card_2d_model.model'
        self.keyed_vector_path = '../models/card_vector.kv'
        self.training_model_path = "../models/training_seq.p"
        self.card_data_path = "../models/card_data.p"
        self.train_seq = []
        
    def load_training_sequence(self, clean=False):
        try:
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        except:
            self.get_cards_from_json()
            obj = pickle.load( open( self.training_model_path, "rb" ) )
        if clean: 
            print("Cleaning Training Model")
            self.twodmodel = Doc2Vec(vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
            self.multimodel = Doc2Vec(vector_size=self.model_dimensionality, min_count=1, epochs=40, ns_exponent=.75)
            self.model = Doc2Vec(vector_size=50, min_count=1, epochs=40, ns_exponent=.75)
        else:
            try:
                self.twodmodel = Doc2Vec.load(self.twod_model_path) 
                self.multimodel = Doc2Vec.load(self.model_dimensionality_path) 
                self.model = Doc2Vec.load(self.word2vec_model_path)
            except:
                print("Failed to load")
                self.twodmodel = Doc2Vec(vector_size=2, min_count=1, epochs=40, ns_exponent=.75)
                self.multimodel = Doc2Vec(vector_size=self.model_dimensionality, min_count=1, epochs=40, ns_exponent=.75)
                self.model = Doc2Vec(vector_size=50, min_count=1, epochs=40, ns_exponent=.75)
                clean = True
                
        count = len(self.model.docvecs)
        for i, phrase in enumerate(obj):
            doc = TaggedDocument(simple_preprocess(phrase), [i + count])
            self.train_seq.append(doc)
        
        if clean:
            self.train_model(True)

    def train_model(self, build = False):
        if build: 
            print("Building Vocab")
            self.model.build_vocab(self.train_seq)
            self.twodmodel.build_vocab(self.train_seq)
            self.multimodel.build_vocab(self.train_seq)
        
        print("Training Model")
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
        print("Getting cards from JSON")
        t = time.time()
        json_file = open('../models/scryfall-default-cards.json')
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
            c.card_type = c.get_card_type(self.twodmodel)
            card_array.append(c)
            count += 1
            obj += c.tokenize_text()
            if len(obj)%2000 == 0:
                if (progress_print):
                    print(str(count) + " Processed")
                    print(obj[-10:])
                if (update_training_model):
                    pickle.dump(obj, open( self.training_model_path, "wb" ) )
        
        t = time.time() - t
        print("Got " + str(len(card_array)) + " cards in " + str(t))
        return card_array

    def decompose_data(self, algorithm, n_components, data, cards):
        t = time.time()
        if (algorithm == "TSNE"):
            alg = TSNE(n_components=self.model_dimensionality)
        elif (algorithm == "SpectralEmbeddingNN"):
            alg = SpectralEmbedding(n_components=self.model_dimensionality, affinity="nearest_neighbors")
        elif (algorithm == "SpectralEmbeddingRBF"):
            alg = SpectralEmbedding(n_components=self.model_dimensionality, affinity="rbf")
        else:
            alg = PCA(n_components=self.model_dimensionality)

        first_pass = alg.fit_transform(np.array(data))
        flat_pass = []
        for c in cards:
            new_arr = [c.simple_vec[x] for x in range(self.model_dimensionality)]
            flat_pass.append(new_arr)
        flat_pass = np.array(flat_pass)

        flat_mean = np.mean(flat_pass)
        flat_std = np.std(flat_pass)            
        mean = np.mean(first_pass)
        std = np.std(first_pass)

        card_values = []
        flat_values = []
        for c in cards:
            c_type = c.card_type[0] + c.card_type[1]
            flat_values.append([c_type, c.get_color_identity(flat_mean,flat_std), c.get_cmc(flat_mean,flat_std), \
            c.get_toughness(flat_mean,flat_std), c.get_power(flat_mean,flat_std)])
            card_values.append([c_type, c.get_color_identity(mean,std), c.get_cmc(mean,std), \
            c.get_toughness(mean,std), c.get_power(mean,std)])
        
        flat_values = np.array(flat_values)
        card_values = np.array(card_values)
        first_pass = np.append(first_pass, card_values, axis=1)
        flat_pass = np.append(flat_pass, flat_values, axis=1)        

        if (algorithm == "TSNE"):
            alg = TSNE(n_components=n_components)
        elif (algorithm == "SpectralEmbeddingNN"):
            alg = SpectralEmbedding(n_components=n_components, affinity="nearest_neighbors")
        elif (algorithm == "SpectralEmbeddingRBF"):
            alg = SpectralEmbedding(n_components=n_components, affinity="rbf")
        else:
            alg = PCA(n_components=n_components)

        result = alg.fit_transform(first_pass)
        flat_result = alg.fit_transform(flat_pass)
        t = time.time() - t
        print(algorithm + " " + str(n_components) + "d Complete in " + str(t))
        ret = []
        flat_ret = []
        for i,c in enumerate(cards):
            x, y = result[i].tolist()
            fx, fy = flat_result[i].tolist()
            c.save_decomp_res("naive", fx, fy, self.model_dimensionality)
            c.save_decomp_res(algorithm, x, y, self.model_dimensionality)
            name = c.name
            hexVal = c.generate_color_hex()
            ret.append([name, hexVal] + result[i].tolist())
            flat_ret.append([name, hexVal] + flat_result[i].tolist())
        
        path = algorithm + str(self.model_dimensionality) + "dGraphPoints.csv"
        flat_path = "flat" + algorithm + str(self.model_dimensionality) + "dGraphPoints.csv"
        fieldnames = ['name', 'color']
        if (n_components == 2):
            fieldnames = ['name', 'color', 'x', 'y']
        elif (n_components == 3):
            fieldnames = ['name', 'color', 'x', 'y', 'z']
        else:
            fieldnames += [str(x) for x in range(n_components)]

        with open('../models/' + path, 'w+') as localRet:
            writer = csv.writer(localRet)
            writer.writerow(fieldnames)
            writer.writerows(ret)
            localRet.close()

        with open('../../magicVisualizer/src/assets/data/' + path, 'w+') as visRet:
            writer = csv.writer(visRet)
            writer.writerow(fieldnames)
            writer.writerows(ret)
            visRet.close()
        
        with open('../models/' + flat_path, 'w+') as localFlat:
            writer = csv.writer(localFlat)
            writer.writerow(fieldnames)
            writer.writerows(flat_ret)
            localFlat.close()

        with open('../../magicVisualizer/src/assets/data/' + flat_path, 'w+') as visFlat:
            writer = csv.writer(visFlat)
            writer.writerow(fieldnames)
            writer.writerows(flat_ret)
            visFlat.close()
        print("Data Saved")
        return result
    
    def graph_cards(self, save_to_db):
        arr = []
        try:
            arr, cleaned_array = pickle.load(open( self.card_data_path, "rb" ))
        except:
            card_array = self.get_cards_from_json()
            print("Cleaning Card Array")
            seen_array = []
            cleaned_array = []
            for t in card_array: 
                key = t.name + t.text
                if (key not in seen_array):
                    tokens = t.tokenize_text()
                    vec = self.model.infer_vector(tokens)
                    t.simple_vec = self.multimodel.infer_vector(tokens)
                    arr.append(vec)
                    seen_array.append(key)
                    cleaned_array.append(t)
                    if save_to_db:
                        t.save_to_db()
            pickle.dump([arr, cleaned_array], open( self.card_data_path, "wb" ) )

        print("Running Graphing on Data Set")
        self.decompose_data("PCA", 2, arr, cleaned_array) 
        self.decompose_data("SpectralEmbeddingRBF", 2, arr, cleaned_array)
        self.decompose_data("SpectralEmbeddingNN", 2, arr, cleaned_array) 
        if (self.model_dimensionality) <= 4:
            self.decompose_data("TSNE", 2, arr, cleaned_array)

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
    color_identity = ''
    text = ''
    simple_vec = []

    def __str__(self):
        return self.name + " - " + str(self.multiverse_id) + ": " + self.card_type + "\n" + \
            self.rarity + ", " + str(self.cmc) + "\n" + self.color_identity + " " + \
            self.power + "/" + self.toughness

    def __init__(self, json_info):
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
        self.card_type = json_info['type_line'].split("—")[0].strip()
        rarity = {'common': 0, 'uncommon': 1, 'rare': 2, 'mythic': 3}
        self.rarity = rarity[json_info['rarity'].strip().lower()]
        self.cmc = int(json_info['cmc'])
        self.generate_color_identity(json_info['color_identity'])

    def get_card_type(self, model):
        tokens = self.card_type.lower().split()
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
            power = -2
        if (int(power) > 20):
            power = 20
        return (int(power) * mean) / std

    def get_rarity(self, mean=1, std=1):
        return (self.rarity * mean) / std

    def get_color_identity(self, mean=1, std=1):
        return (self.color_identity * mean) / std

    def get_cmc(self, mean=1, std=1):
        if (self.cmc > 20):
            return 20 * mean / std
        else:
            return (self.cmc * mean) / std

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

    def generate_color_hex(self):
        color = "#777777"
        if (self.color_identity > 5): #Multicolor Gold
            color = "#FFD700"
        elif (self.color_identity == 5): #White
            color = "#FFFFFF"
        elif (self.color_identity == 4): #Black
            color = "#000000"
        elif (self.color_identity == 3): #Green
            color = "#008000"
        elif (self.color_identity == 2): #Blue
            color = "#0000FF"
        elif (self.color_identity == 1): #Red
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

    def save_to_db(self):
        headers = {'Content-type': 'application/json'}
        d = copy.deepcopy(self.__dict__) 
        if 'text' in d:
            d.pop('text') 
        if 'simple_vec' in d:
            d.pop('simple_vec')
        d['card_type'] = float(self.card_type[0] + self.card_type[1])
        
        body = json.dumps(d)
        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('PUT', '/api/cards/', body, headers)

    def save_decomp_res(self, alg, x, y, dimension):
        ret = {
            "x_value": x,
            "y_value": y,
            "algorithm": alg
        }
        ret["alg_weight"] = dimension
        ret["card"] = self.name
        
        body = json.dumps(ret)
        headers = {'Content-type': 'application/json'}
        conn = http.client.HTTPConnection('localhost:8000')
        conn.request('PUT', '/api/card_vector/', body, headers)

def runModel(model_dimensionality):
    v = Vectorizor(model_dimensionality)
    v.load_training_sequence()
    v.graph_cards(True)

runModel(4)