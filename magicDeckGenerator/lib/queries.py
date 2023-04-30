def get_unseen(db):
    cursor = db.cursor()
    q = """select top 10 card.scryfall_id, card.name from cards
           where scryfall_id not in
           (SELECT ci.name, scryfall_id FROM card_instances ci group by name, scryfall_id)
           order by rand()"""
    cursor.execute(q)
    results = cursor.fetchall()
    cursor.close()
    return [x[1] for x in results]

def deck_exists(db, url):
    cursor = db.cursor()
    q = "select id from decks where url = %s"
    cursor.execute(q, (url,))
    exists = cursor.fetchone()
    cursor.close()
    return exists

def save_deck(db, deck):
    cursor = db.cursor()
    deck_q = "insert into decks (name, url, size) values(%s, %s, %s) returning id"
    instance_q = """insert into card_instances
                    (deck_id, count, missing, name, is_sideboard, scryfall_link_id)
                    values(%s, %s, %s, %s, %s, %s)"""
    cursor.execute(deck_q, (deck.name, deck.url, deck.get_deck_size()[1]))
    id = cursor.fetchone()[0]
    for member in deck.deckMembers:
        cursor.execute(instance_q, (id, member.count, False, member.name, member.is_sideboard, member.scryfall_link_id))
    db.commit()
    cursor.close()
