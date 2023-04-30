# Magic: The Gathering Deck Generator

## Install Python Dependencies

From project root run

```
pip3 install --user -r requirements.txt
```

## Feeling fancy?

I tried to create a python environment setup tool, pretty sure it works. If you're feeling fancy and/or brave it can be run with the command below.

```
python3 init.py
```

Make sure primeModel has write_to_db set to false if you run this way

# Okay But How Do I Run This Thing??

I get it, you're all set up with all your dependencies and things, but what does this garbage fire code actually do? Well, right now not much, but it's a process, and that process will be outlined below as I slowly work towards a real usable tool

## Start Database

Start the database with

```bash
docker compose up
```

This will automatically run the migrations in `postgres/migrations` as well, the first time it is started.  To tear down the database for a fresh run, do

```bash
docker compose down -v
```

This will delete all of the data, too!

The database will be running locally on `:5432`.  See the docker compose config for local dev connection info.

## Vectorize Your Cards

### Build Card Vectors

Navigate to magicDeckGenerator/cardVectorizor and run the vectorizor. This is going to take a _long_ time the first time it runs. Subsequent runs will be faster as you won't need rebuild the models. I'm hoping to write a tool that takes our shiny csv we generate for the visualizer and throw those straight in the db so we don't have to run them over and over because they are seriously _slow_

If it's your first time running the vectorizor or you want to build clean models

```
python3 main.py buildcards
```

If you want to update existing cards or interpolate a newer dataset

```
python3 main.py vectorize
```

### Visualize Vectorized Card Relationships

So you did the thing. But what did you do aside from a lot of waiting. Well, mosey on over to magicDeckGenerator/magicVisualizer to take a look!

#### Set Up Dependencies (yes there are more)

The visualizer is built as an angular project using angular material. So, install node and then you can do a simple npm install

```

cd magicDeckGenerator/magicVisualizer
npm install

```

#### Run The Visualizer

After that just fire up the angular app and poke around at all that sweet sweet data. Was this necessary for the generator? Not at all! But it's pretty neat, huh?

```

ng serve -o

```

## Gather Deck Data

Okay, now what? So we turned some magic cards into numbers, and that was cool, but we need to do something with that.

### Scraping Time!

Build out deck relationships from mtgTop8

```

python3 main.py scrape

```

### Key SQL I can never remember

Card Coverage (This is how I keep track of card instance coverage across all possible cards for better graph relationship building)

```

select count(distinct(c.parsed_name)) as found_cards from card_instance c;
select count(*) as total_cards from card;

```

Clean up decks with missing card_instances because naming conventions are never standardized

```
SET REFERENTIAL_INTEGRITY FALSE;
BEGIN TRANSACTION;
DELETE FROM deck WHERE id IN (select distinct(deck_id) from card_instance where missing = TRUE);
DELETE FROM card_instance WHERE deck_id in (select distinct(deck_id) from card_instance where missing = TRUE);
COMMIT;
SET REFERENTIAL_INTEGRITY TRUE;

select distinct(deck_id) from card_instance where missing = TRUE;
```

## Big ToDos

- Audit existing decks in db to verify that expected card count matches card-detail information for improve save check
- Actually build The Thing(TM)

## Implementation Ideas

#### Algorithmic ideas to play with

- Similarity measure
- Sparsification of graph
- Closeness Centrality
- Harmonic Centrality

#### Optimize an existing deck

- Graph similarity measure of cards using existing set of cards and all edges contained in that set
- Find top 3 swaps for each card if above certain score
  - Weight by cosine similarity and graph similarity to find top matches

#### Build a deck from exisiting card set

- Limit all edges to exisiting card set
- Add unlimited (60 in case of standard deck type) of each land to card pool

#### Build a deck around certain cards

- Limit edges to those where one node is in card set

#### Build a deck using specific colors

- limit nodes to those with specific color identities

#### Build a deck on a budget

- Play around with positive vs negative weighting using cost vs closeness centrality weighting
- (cost / budget) - (budget / 60) - (edge occurence / highest possible occurance)
- take percent of budget weight, subtract per card budget allocation, subtract edge weight normalized to 1

#### Automated drafting

- From an existing tapped out cube as a whole set
- Alternate taking turns from whole set
- From limited card hands available as generator for players unfamiliar with drafting

Built with {17} cups of coffee and {10} energy drinks
