
from .DeckMember import DeckMember


class Deck:
    def __init__(self, name: str, url: str):
        self.name = name.lower()
        self.url = url
        self.deckMembers = []

    def __str__(self):
        return "name: " + str(self.name) + "\n url: " + str(self.url) + "\n" + \
            " deckMembers: " + str(self.deckMembers)

    def add_member_to_deck(self, member: DeckMember):
        self.deckMembers.append(member)

    def get_deck_size(self):
        body = {}
        deck_size = 0
        for member in self.deckMembers:
            if member.is_sideboard:
                continue
            deck_size += int(member.count)
            if member.name not in body:
                body[member.name] = member
            else:
                body[member.name].increase(member.count)
        return [body, deck_size]

    def build_for_db(self):
        body = self.get_deck_size()[0]

        countList = [int(x.count) for x in body.values()]
        shouldSave = max(countList) <= 40

        return {
            "body": {
                "id": None,
                "name": self.name, "url": self.url,
                "cardInstances": [x.build_for_db() for x in body.values()]
            },
            "shouldSave": shouldSave}
