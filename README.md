# Magic: The Gathering Deck Generator

## Feeling fancy?

I tried to create a environment setup tool, pretty sure it works. Feeling brave? It can be run with the command below. Use the -h flag to see variable names if you want to use it to set up your .env file automagically.

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

Built with {9} cups of coffee
