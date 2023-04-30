create table if not exists cards (
    id serial primary key,
    oracle_id uuid unique,
    tcgplayer_id varchar(10),
    mtgo_id varchar(10),
    arena_id varchar(10),
    cardmarket_id varchar(10),
    scryfall_link_id varchar(10) unique,
    name varchar,
    rarity integer,
    card_type integer,
    toughness float,
    power float,
    cmc float,
    color_identity integer,
    x float,
    y float
);

create table if not exists decks (
    id serial primary key,
    name varchar,
    url varchar,
    size integer
);

create table if not exists card_instances (
    id serial primary key,
    deck_id integer references decks (id),
    count integer,
    missing boolean,
    name varchar,
    is_sideboard boolean,
    scryfall_link_id varchar(10)
);
