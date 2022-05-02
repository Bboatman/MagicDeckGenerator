import re


class DeckMember:
    def __init__(self, name: str, card_id, count=1):
        self.name = name.lower()
        self.multiverse_id = card_id
        self.count = count

    def __repr__(self):
        return '{{"name": "{0}", "multiverse_id": {1}, "count": {2}}}'.format(self.name, self.multiverse_id, self.count)

    def __str__(self):
        return '{{"name": "{0}", "multiverse_id": {1}, "count": {2}}}'.format(self.name, self.multiverse_id, self.count)

    def asDict(self):
        self.name = re.sub(r"[']", "", self.name)
        return {"name": self.name, "multiverse_id": self.multiverse_id, "count": self.count}

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
