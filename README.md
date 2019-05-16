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
