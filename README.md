# Magic: The Gathering Deck Generator

## Feeling fancy?

I tried to create a python environment setup tool, pretty sure it works. Feeling brave? It can be run with the command below. Use the -h flag to see variable names if you want to use it to set up your .env file automagically.

```
python3 init.py
```

## Install Python Dependencies

From project root run

```
pip3 install --user -r requirements.txt
```

## Necessary Data

Save this file to magicDeckGenerator/models
[Skyforge Card Data Set](https://archive.scryfall.com/json/scryfall-default-cards.json)

## Prime Your Models

Model priming can be built from magicDeckGenerator/cardVectorizor. If you have a database set up, create a .env file with the following variables:

- PGUSER=$dbUsername
- PGHOST=$host
- PGPASSWORD=$dbPassword  
- PGDATABASE=$dbName
- DJANGO_SECRET=$secretDjangoKey

In one terminal start database with

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

If not running from database, you can still build the vector models for cards with

```
cd magicDeckGenerator/cardVectorizor
python vectorizor.py
```

Make sure primeModel has write_to_db set to false if you run this way

# Okay But How Do I Run This Thing??

I get it, you're all set up with all your dependencies and things, but what does this garbage fire code actually do? Well, right now not much, but it's a process, and that process will be outlined below as I slowly work towards a real usable tool

## Vectorize Your Cards

### Build Card Vectors

Navigate to magicDeckGenerator/cardVectorizor and run the vectorizor. This is going to take a *long* time the first time it runs. Subsequent runs will be faster as you won't need rebuild the models. I'm hoping to write a tool that takes our shiny csv we generate for the visualizer and throw those straight in the db so we don't have to run them over and over because they are seriously *slow*

```
cd magicDeckGenerator/cardVectorizor
python vectorizor.py
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

Built with {10} cups of coffee

## Big ToDos
- Audit existing decks in db to verify that expected card count matches card-detail information for improve save check

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
