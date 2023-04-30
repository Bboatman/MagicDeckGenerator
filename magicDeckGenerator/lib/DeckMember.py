import re


class DeckMember:
    def __init__(self, is_sideboard, name: str, card_id, count=1):
        self.name = name.lower()
        self.scryfall_link_id = card_id
        self.count = count
        self.is_sideboard = is_sideboard

    def __repr__(self):
        return '{{"name": "{0}", "scryfall_link_id": {1}, "count": {2}, "is_sideboard": {3}}}'.format(self.name, self.scryfall_link_id, self.count, self.is_sideboard)

    def __str__(self):
        return '{{"name": "{0}", "scryfall_link_id": {1}, "count": {2}, "is_sideboard": {3}}}'.format(self.name, self.scryfall_link_id, self.count, self.is_sideboard)

    def asDict(self):
        self.name = re.sub(r"[']", "", self.name)
        return {"name": self.name, "scryfall_link_id": self.scryfall_link_id, "count": self.count, "is_sideboard": self.is_sideboard}

    def increase(self, number=1):
        if type(self.count) is str:
            self.count = int(self.count)

        self.count += int(number)

    def decrease(self, number=1):
        if type(self.count) is str:
            self.count = int(self.count)

        self.count -= number

    def build_for_db(self):
        return {"parsedName": self.name, "count": self.count}
