import json
import urllib.request
from requests import get
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.test.utils import get_tmpfile
import sys
import pickle
from rake_nltk import Rake
import re

card_path = './models/scryfall-default-cards.json'
doc2vec_path = "./models/card_doc2vec"
card_vec_path = './models/card_vecs.p'

color_identities = {'': 0, 'C': 0, 'R': 1, 'U': 2, 'G': 3,
                    'B': 4, 'W': 5, 'RU': 6, 'GR': 7, 'BR': 8,
                    'RW': 9, 'GU': 10, 'BU': 11, 'UW': 12, 'BG': 13,
                    'GW': 14, 'BW': 15, 'GRU': 16, 'BRU': 17,
                    'RUW': 18, 'BGR': 19, 'GRW': 20, 'BRW': 21,
                    'BGU': 22, 'GUW': 23, 'BUW': 24, 'BGW': 25,
                    'BGRU': 26, 'GRUW': 27, 'BRUW': 28, 'BGRW': 29,
                    'BGUW': 30, 'BGRUW': 31}


def load_cards():
    url = 'https://api.scryfall.com/bulk-data/oracle-cards'
    print('Beginning file download with urllib2...')
    path = './models'
    try:
        resp = get(url)
        downloadLoc = json.loads(resp.text)["download_uri"]
        urllib.request.urlretrieve(
            downloadLoc, path + "/scryfall-default-cards.json")
        print('Retrieved cards from scryfall')
    except:
        print("Issue connecting to card ref download")


def get_card_json():
    print('Loading in card json')
    data = []
    with open(card_path, encoding='utf-8') as my_file:
        data = json.load(my_file)
    return data


def get_card_type_list(card_data):
    types = list(set([x['type_line'] for x in card_data]))
    return types


def get_card_rarity(card_data):
    types = list(set([x['rarity'] for x in card_data]))
    return types


def convert_str_val_to_num(value):
    if value == "*":
        return 20.0
    elif value == "1+*" or value == "2+*":
        return 20.0
    elif value == "*+1":
        return 20.0
    elif value == '∞':
        return 20.0
    elif value == '?':
        return 0
    elif value == '*²':
        return 20.0
    elif value == '7-*':
        return 3.5
    elif value == None:
        return None
    else:
        return float(value)


def format_card_data(card_json, card_types, card_rarity):
    try:
        scryfall_link = card_json['scryfall_uri'].split('/')
        card = {
            'oracle_id': card_json['oracle_id'],
            'tcgplayer_id': card_json.get('tcgplayer_id', None),
            'mtgo_id': card_json.get('mtgo_id', None),
            'arena_id': card_json.get('arena_id', None),
            'cardmarket_id': card_json.get('cardmarket_id', None),
            'scryfall_link_id': ''.join(scryfall_link[4:6]),
            'name': card_json['name'],
            'rarity': card_rarity.index(card_json['rarity']),
            'card_type': card_types.index(card_json['type_line']),
            'toughness': convert_str_val_to_num(card_json.get('toughness', None)),
            'power': convert_str_val_to_num(card_json.get('power', None)),
            'cmc': convert_str_val_to_num(card_json.get('cmc', None)),
            'color_identity': color_identities[''.join(card_json['color_identity'])],
            'x': None,
            'y': None,
            'text': card_json.get('oracle_text', ''),
            'text_vec': None
        }
        return card
    except [KeyError, ValueError] as e:
        print(e, card['name'])


def build_doc2vec_model(cards):
    corpus = ''.join([card['text'].replace(
        "//", " ") + " \n" for card in cards])
    r = Rake()
    r.extract_keywords_from_text(corpus)
    tags = []
    phrases = r.get_ranked_phrases_with_scores()
    phrases.reverse()
    for tag in phrases[:150000]:
        if tag[1] not in tags and tag[0] > 1.0:
            tags.append(tag[1])
    documents = [TaggedDocument(doc['text'].split(" "), tags)
                 for doc in cards]
    model = Doc2Vec(documents, vector_size=4, window=2, min_count=1, workers=4)
    model.save(doc2vec_path)


def generate_text_vector(card):
    model = Doc2Vec.load(doc2vec_path)
    document = card['text'].split(" ")
    vector = model.infer_vector(doc_words=document)
    return vector


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

if __name__ == "__main__":
    commands = sys.argv
    if 'build' in commands:
        # load_cards()
        print("Is building")

    data = get_card_json()
    card_types = get_card_type_list(data)
    card_rarity = get_card_rarity(data)

    formatted_cards = [format_card_data(
        x, card_types, card_rarity) for x in data]

    try:
        text_vec_cards = pickle.load(open(card_vec_path, 'rb'))
    except [FileNotFoundError, EOFError]:
        f = open(card_vec_path, "x")
        text_vec_cards = formatted_cards

    if ('build' in commands):
        print('Building Model')
        build_doc2vec_model(formatted_cards)

    print('Generating text vectors')
    process_count = 0
    for x in range(len(formatted_cards)):
        if text_vec_cards[x]['text_vec'] is None:
            vector = generate_text_vector(formatted_cards[x])
            formatted_cards[x]['text_vec'] = vector
        if (process_count % 100 == 1):
            printProgressBar(prefix=' Progress:', iteration=process_count/100, total=len(formatted_cards)/100)
            pickle.dump(formatted_cards, open(card_vec_path, "wb"))

        process_count += 1

    if process_count > 0:
        # If we processed any, do one extra dump for good measure to capture those missed in the % check
        pickle.dump(formatted_cards, open(card_vec_path, "wb"))
