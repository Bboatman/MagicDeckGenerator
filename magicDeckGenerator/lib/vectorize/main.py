import json
import urllib.request
from requests import get
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.test.utils import get_tmpfile
import sys
import pickle
from rake_nltk import Rake
from sklearn.manifold import TSNE
import numpy as np
import plotly.express as px

card_path = './models/scryfall-default-cards.json'
doc2vec_path = "./models/card_doc2vec"
card_vec_path = './models/card_vecs.p'
full_card_path = './models/full_cards.p'
graph_point_path = './models/graphPoints.csv'

color_identities = {'': 0, 'C': 0, 'R': 1, 'U': 2, 'G': 3,
                    'B': 4, 'W': 5, 'RU': 6, 'GR': 7, 'BR': 8,
                    'RW': 9, 'GU': 10, 'BU': 11, 'UW': 12, 'BG': 13,
                    'GW': 14, 'BW': 15, 'GRU': 16, 'BRU': 17,
                    'RUW': 18, 'BGR': 19, 'GRW': 20, 'BRW': 21,
                    'BGU': 22, 'GUW': 23, 'BUW': 24, 'BGW': 25,
                    'BGRU': 26, 'GRUW': 27, 'BRUW': 28, 'BGRW': 29,
                    'BGUW': 30, 'BGRUW': 31}

hex_colors = {
    0: 'grey',
    1: 'red',
    2: 'blue',
    3: 'green',
    4: 'black',
    5: 'white',
    10: 'orange'
}


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
    # 20 is the highest concievable size of weird cards
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


def set_card_color(card):
    color = card['color_identity']
    if color > 5:
        color = 10
    return {
        'name': card['name'],
        'color': str(color),
        'x': card['x'],
        'y': card['y'],
        'text': card['text']
    }


def create_csv(processed_card_data):
    card_mapping = [set_card_color(card)
                    for card in processed_card_data[:100]]

    fig = px.scatter(card_mapping, x='x', y='y',
                     color='color',
                     color_discrete_map={
                         '0': 'grey',
                         '1': 'red',
                         '2': 'blue',
                         '3': 'green',
                         '4': 'black',
                         '5': 'white',
                         '10': 'orange'
                     }, hover_data=['name', 'text'])

    fig.show()

def build_doc2vec_model(cards):
    corpus = ''.join([card['text'].replace(
        "//", " ") + " \n" for card in cards])
    r = Rake()
    r.extract_keywords_from_text(corpus)
    tags = []
    phrases = r.get_ranked_phrases_with_scores()
    phrases.reverse()
    for tag in phrases[:100000]:
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


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    if iteration == total:
        print()


def get_card_array(card):
    rarity = card['rarity']
    type = card['card_type']
    toughness = card.get('toughness', -1)
    power = card.get('power', -1)
    identity = card['color_identity']
    text_vec = card['text_vec']
    if (toughness is None):
        toughness = -1
    if (power is None):
        power = -1
    arr = [rarity, type, toughness, power, identity]
    return [y for x in [arr, text_vec] for y in x]


def project_cards(cards):
    print('Doing TSNE')
    alg = TSNE(n_components=2)
    card_data = [get_card_array(x) for x in cards]
    np_card_data = np.array(card_data)
    return alg.fit_transform(np_card_data)


if __name__ == "__main__":
    commands = sys.argv
    if 'show' in commands:
        full_cards = pickle.load(open(full_card_path, "rb"))
        vec_cards = pickle.load(open(card_vec_path, "rb"))
        filtered = list(
            filter(lambda card: card['text_vec'] is not None, vec_cards))
        print(len(full_cards))
        print(full_cards[28655])
        print(len(filtered))
        print(filtered[15803])

        exit()

    if 'draw' in commands:
        full_cards = pickle.load(open(full_card_path, "rb"))
        create_csv(full_cards)
        exit()

    if 'build' in commands:
        # load_cards()
        print("Is building")

    data = get_card_json()
    #TODO: Filter cards with no text - they are art cards and are not playable
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
        text_vec_cards = formatted_cards  # Wipe old vectors if we rebuild model

    print('Generating text vectors')
    process_count = 0
    for x in range(len(formatted_cards)):
        if text_vec_cards[x]['text_vec'] is None:
            vector = generate_text_vector(formatted_cards[x])
            formatted_cards[x]['text_vec'] = vector
        else:
            formatted_cards[x] = text_vec_cards[x]
        if (process_count % 100 == 1):
            print_progress_bar(
                prefix=' Progress:', iteration=process_count/100, total=len(formatted_cards)/100)
            pickle.dump(formatted_cards, open(card_vec_path, "wb"))

        process_count += 1
        if (process_count == len(formatted_cards)):
            print_progress_bar(
                prefix=' Progress:', iteration=process_count/100, total=len(formatted_cards)/100)


    if process_count > 0:
        # If we processed any, do one extra dump for good measure to capture those missed in the % check
        pickle.dump(formatted_cards, open(card_vec_path, "wb"))

    tsne_values = project_cards(formatted_cards)
    formatted_cards = list(formatted_cards)
    for i, c in enumerate(tsne_values):
        x, y = c.tolist()
        formatted_cards[i]['x'] = x
        formatted_cards[i]['y'] = y

    pickle.dump(formatted_cards, open(full_card_path, "wb"))
