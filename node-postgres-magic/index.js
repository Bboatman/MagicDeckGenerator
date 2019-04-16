const express = require('express')
const bodyParser = require('body-parser')
const app = express()
const port = 3000

const user = require('./queries/user')
const card = require('./queries/card')
const deck = require('./queries/deck')
const edge = require('./queries/weighted_edge')

app.use(bodyParser.json())
app.use(
  bodyParser.urlencoded({
    extended: true,
  })
);

app.get('/', (request, response) => {
    response.json({ info: 'Node.js, Express, and Postgres API' })
});

app.listen(port, () => {
  console.log(`App running on port ${port}.`)
});

app.get('/users', user.getUsers)
app.get('/users/:id', user.getUserById)
app.post('/users', user.createUser)
app.put('/users/:id', user.updateUser)
app.delete('/users/:id', user.deleteUser)

app.get('/card', card.getCards)
app.get('/card/:id', card.getCardById)
app.post('/card', card.createCard)
app.post('/cards', card.createCards)
app.delete('/card/:id', card.deleteCard)

app.get('/edge', edge.getEdges)
app.get('/edge/:id', edge.getEdgesForCard)
app.post('/edge', edge.createEdge)
app.post('/edges', edge.createEdges)
app.delete('/edge/:id', edge.deleteEdge)

app.post('/deck', deck.ingestDeck)