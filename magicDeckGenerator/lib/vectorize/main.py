import json
import urllib.request
from requests import get

card_path = './models/scryfall-default-cards.json'
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


def format_card_data(card, card_types, card_rarity):
    try:
        scryfall_link = card['scryfall_uri'].split('/')
        card = {
            'oracle_id': card['oracle_id'],
            'tcgplayer_id': card.get('tcgplayer_id', None),
            'mtgo_id': card.get('mtgo_id', None),
            'arena_id': card.get('arena_id', None),
            'cardmarket_id': card.get('cardmarket_id', None),
            'scryfall_link_id': ''.join(scryfall_link[4:6]),
            'name': card['name'],
            'rarity': card_rarity.index(card['rarity']),
            'card_type': card_types.index(card['type_line']),
            'toughness': convert_str_val_to_num(card.get('toughness', None)),
            'power': convert_str_val_to_num(card.get('power', None)),
            'cmc': convert_str_val_to_num(card.get('cmc', None)),
            'color_identity': color_identities[''.join(card['color_identity'])],
            'x': None,
            'y': None
        }
        return card
    except [KeyError, ValueError] as e:
        print(e, card['name'])


if __name__ == "__main__":
    data = get_card_json()
    card_types = get_card_type_list(data)
    card_rarity = get_card_rarity(data)

    formatted_cards = [format_card_data(
        x, card_types, card_rarity) for x in data]
    print(formatted_cards[0])
