const templateWait = Handlebars.compile(document.querySelector('#waitlist').innerHTML);
const templateFull = Handlebars.compile(document.querySelector('#gameFull').innerHTML);
const templateGame = Handlebars.compile(document.querySelector('#game').innerHTML);
const templateGameOver = Handlebars.compile(document.querySelector('#gameOver').innerHTML);
var inGame = false;
var playerData;
var Data;
var hand;
var epitetos = ['compañero', 'compañera', 'campeón', 'campeona', 'máquina', 'animal', 'loco turbina', 'vieji', 'viejita', 'hermano', 'hermana']

function choose(choices) {
  var index = Math.floor(Math.random() * choices.length);
  return choices[index];
}

function render_hand(socket, data)  {
    if (playerData.team == data.current_player.team && playerData.player == data.current_player.player) {
        document.querySelector('#turn').innerHTML = "<h4>Jugás vos, " + choose(epitetos) + "</h4>"
    } else {
        document.querySelector('#turn').innerHTML = "<h4>Juega " + data.current_player.username + "</h4>"
    }
    document.querySelector('#hand').innerHTML = ''
    for (let i = 0; i<hand.length; i++ ) {
        const button = document.createElement("img")
        var path = '/static/images/'+hand[i][1]+'/'+hand[i][0]+'.png'
        button.src = path
        button.class = 'card'
        button.style.margin = '5px'
        button.style.width = '100px'
        button.id = 'boton'+i
        button.onclick = () => {
            if (playerData.team == data.current_player.team && playerData.player == data.current_player.player)  {
                document.querySelector('#boton'+i).remove()
                card_data = {team: playerData.team, player: playerData.player, number: hand[i][0], suit: hand[i][1]}
                socket.emit('play_card', card_data)
                hand.splice(i, 1)
            } else {
                document.querySelector('#turn').innerHTML = "<h2>Te dije que juega " + data.current_player.username + ", paparule</h2>"
            }
        }
        document.querySelector('#hand').appendChild(button)
    }
}

function appendPlayedCard(data) {
    const line = document.createElement("img")
    let path = '/static/images/'+data.card[1]+'/'+data.card[0]+'.png'
    line.src = path
    line.title = data.username
    line.style.margin = '5px'
    line.style.width = '100px'
    document.querySelector('#plays').appendChild(line)
}

document.addEventListener('DOMContentLoaded', () => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port)
    socket.emit('connected')
    socket.on('players_update', data => {
        Data = data;
        teamAPlayers = [data.teams.teamA.player1.username, data.teams.teamA.player2.username]
        teamBPlayers = [data.teams.teamB.player1.username, data.teams.teamB.player2.username]
        const content = templateWait({teamAPlayers, teamBPlayers})
        document.querySelector('#body').innerHTML = content
        if (inGame) {
            const buttonOut = document.createElement("button")
            buttonOut.innerHTML = 'Salir';
            buttonOut.onclick = () => {
                socket.emit('player_left', playerData )
                inGame = false
            };
            document.querySelector('#teamB').appendChild(buttonOut)
        } else {
            if (!(data.teams.teamA.full))  {
                const buttonA = document.createElement("button")
                buttonA.innerHTML = 'Entrar'
                buttonA.onclick = () => {
                    socket.emit('player_enter', {team:'teamA'})
                }
                document.querySelector('#teamA').appendChild(buttonA)
            };
            if (!(data.teams.teamB.full))  {
                const buttonB = document.createElement("button")
                buttonB.innerHTML = 'Entrar'
                buttonB.onclick = () => {
                    socket.emit('player_enter', {team:'teamB'})
                }
                document.querySelector('#teamB').appendChild(buttonB)
            }
        }
    })

    socket.on('player_data', data =>    {
        inGame = true
        playerData = data
    })

    socket.on('game_full',() => {
        const content = templateFull()
        document.querySelector('#body').innerHTML = content
    })

    socket.on('game_starts', data =>    {
        Data = data;
        if (inGame) {
            const content = templateGame()
            document.querySelector('#body').innerHTML = content
            hand = data.teams[playerData.team][playerData.player].hand
            render_hand(socket, data)
        }
    })

    socket.on('card_played', data =>    {
        Data = data
        appendPlayedCard(data)
        render_hand(socket, data)
    })

    socket.on('new_round', data =>    {
        Data = data
        appendPlayedCard(data)
        setTimeout(() => {
            document.querySelector('#plays').innerHTML = ''
            render_hand(socket, data)
        }, 1000)
    })

    socket.on('game_over', data =>    {
        Data = data
        appendPlayedCard(data)
        if (data.winner.team == playerData.team)    {
            mensaje = 'Bien ahí wache'
        }   else {
            mensaje = 'A veces se gana, a veces se pierde; pero siempre cagoneás'
        }
        setTimeout(() => {
            const content = templateGameOver({player1: data.winner.players[0],player2: data.winner.players[1],score1: data.winner.score[0],score2: data.winner.score[1],mensaje:mensaje})
            document.querySelector('#body').innerHTML = content
        }, 1000)
    })
})
