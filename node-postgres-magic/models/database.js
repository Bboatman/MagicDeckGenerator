const pg = require('pg');

const client = new pg.Client();

console.log("")
client.connect();
const makeCardTable = client.query(
    'CREATE TABLE card(id SERIAL, name VARCHAR(150) not null, multiverse_id INT CONSTRAINT pk_card_multiverse_id PRIMARY KEY);');
makeCardTable.on('end', () => { client.end(); });

const makeDeckTable = client.query(
    'CREATE TABLE deck(id SERIAL, name VARCHAR not null CONSTRAINT pk_deck_name PRIMARY KEY, contents VARCHAR not null);');
makeDeckTable.on('end', () => { client.end(); });

const makeEdgeTable = client.query(
    'CREATE TABLE weighted_edge(node_a INT,node_b INT,count_a INT,count_b INT,CONSTRAINT pk_weighted_edge_node_a_node_b PRIMARY KEY (node_a,node_b));');
makeEdgeTable.on('end', () => { client.end(); });