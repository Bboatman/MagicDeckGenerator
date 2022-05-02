
import copy
import math
import re
import json


class Card:
    delimiters = "\n", ".", ",", ":"
    regexPattern = '|'.join(map(re.escape, delimiters))
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

    def __str__(self):
        return "Name " + self.name + " - " + str(self.id) + ":\n type: " + str(self.cardType) + "\n" + \
            " rarity: " + str(self.rarity) + "\n cmc: " + str(self.cmc) + "\n color: " + str(self.colorIdentity) + "\n power/toughness: " + \
            str(self.power) + " / " + str(self.toughness)

    def __init__(self, json_info=None):
        if (json_info != None):
            if 'multiverse_ids' in json_info and len(json_info['multiverse_ids']) > 0:
                self.multiverse_id = json_info['multiverse_ids'][0]
            self.name = json_info['name'].lower()
            if 'toughness' in json_info:
                self.toughness = json_info['toughness']
            else:
                self.toughness = "~"
            if 'oracle_text' in json_info:
                self.text = json_info['oracle_text']
            if "type_line" in json_info:
                self.cardType = json_info['type_line'].split("—")[0].strip()
            if type(json_info['rarity']) is str:
                rarity = {'common': 0, 'uncommon': 1, 'rare': 2,
                          'mythic': 3, 'special': 4, 'bonus': 5}
                self.rarity = rarity[json_info['rarity'].strip().lower()]
            elif type(json_info['rarity'] is int):
                self.rarity = json_info['rarity']
            self.cmc = int(json_info['cmc'])
            if 'power' in json_info:
                self.power = json_info['power']
                if type(json_info['power']) is str:
                    self.power = self.get_power()
            else:
                self.power = -1

            if "id" in json_info:
                try:
                    self.id = int(json_info['id'])
                except:
                    self.id = None
            else:
                self.id = None
            if "x" in json_info:
                self.x = json_info["x"]
            else:
                self.x = None
            if "y" in json_info:
                self.y = json_info["y"]
            else:
                self.y = None
            if "color_identity" in json_info:
                self.generate_colorIdentity(json_info['color_identity'])
            elif "colorIdentity" in json_info:
                self.colorIdentity = json_info['colorIdentity']

    def get_cardType(self, model):
        tokens = self.cardType.lower().split()
        return model.infer_vector(tokens)

    def get_toughness(self, mean=1, std=1):
        toughness = self.toughness
        if self.toughness == 'x':
            toughness = math.floor(self.cmc + (self.rarity / 2))
        elif self.toughness == '~':
            toughness = -1
        elif '*' in self.toughness:
            toughness = math.floor(self.cmc + (self.rarity / 2))
        else:
            try:
                toughness = float(self.toughness)
            except:
                print(self.toughness)
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
        elif '*' in self.toughness:
            power = math.floor(self.cmc + (self.rarity / 2))
        else:
            try:
                power = float(self.power)
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

            choices = {'C': 0, 'R': 1, 'U': 2, 'G': 3,
                       'B': 4, 'W': 5, 'RU': 6, 'RG': 7, 'RB': 8,
                       'RW': 9, 'UG': 10, 'UB': 11, 'UW': 12, 'GB': 13,
                       'GW': 14, 'BW': 15, 'RUG': 16, 'RUB': 17,
                       'RUW': 18, 'RGB': 19, 'RGW': 20, 'RBW': 21,
                       'UGB': 22, 'UGW': 23, 'UBW': 24, 'GBW': 25,
                       'RUGB': 26, 'RUGW': 27, 'RUBW': 28, 'RGBW': 29,
                       'UGBW': 30, 'RUGBW': 31}
            self.colorIdentity = choices[colorIdentity]

    def generate_color_hex(self):
        color = "#777777"
        if (self.colorIdentity > 5):  # Multicolor Gold
            color = "#FFD700"
        elif (self.colorIdentity == 5):  # White
            color = "#FFFFFF"
        elif (self.colorIdentity == 4):  # Black
            color = "#000000"
        elif (self.colorIdentity == 3):  # Green
            color = "#008000"
        elif (self.colorIdentity == 2):  # Blue
            color = "#0000FF"
        elif (self.colorIdentity == 1):  # Red
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
        body = self.get_db_value()
        service.post_card(body)

    def get_db_value(self):
        d = copy.deepcopy(self.__dict__)
        if 'text' in d:
            d.pop('text')
        if 'simple_vec' in d:
            d.pop('simple_vec')
        if 'long_vec' in d:
            d.pop('long_vec')
        if 'id' in d and type(d["id"]) is str:
            d.pop('id')

        d["power"] = self.get_power()
        d["toughness"] = self.get_toughness()
        d['cardType'] = float(self.cardType[0] + self.cardType[1])

        if type(d["id"]) is str:
            d.pop("id")

        if 'multiverse_id' in d:
            d.pop("multiverse_id")

        return json.loads(json.dumps(d))

    def save_decomp_res(self, x, y):
        self.x = x
        self.y = y
