const templateWait = Handlebars.compile(document.querySelector('#waitlist').innerHTML);
const templateFull = Handlebars.compile(document.querySelector('#gameFull').innerHTML);
const templateGame = Handlebars.compile(document.querySelector('#game').innerHTML);
var inGame = false;
var playerData;
var teamPlayers;
var triunfo = '';
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
        button.style.margin = '1px'
        button.style.width = '100px'
        button.id = 'boton'+i
        button.onclick = () => {
            if (playerData.team == data.current_player.team && playerData.player == data.current_player.player)  {
                suits = hand.map(x => {return x[1]})
                if (hand[i][1]==triunfo || data.current_player.n==1 || !(suits.includes(triunfo)) )    {
                    for (k=0; k<hand.length; k++)   {
                        document.querySelector('#boton'+k).onclick = ()=>{}
                    }
                    document.querySelector('#boton'+i).remove()
                    card_data = {team: playerData.team, player: playerData.player, number: hand[i][0], suit: hand[i][1]}
                    socket.emit('play_card', card_data)
                    hand.splice(i, 1)
                } else {
                    document.querySelector('#turn').innerHTML = "<h2>No te hagás el gil, que tenés " + triunfo + "s</h2>"
                }
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

function updateScoreBoard(data) {
    var s
    if ((data.teams.teamA.hand_score % 3 == 0)&&(data.teams.teamB.hand_score % 3 == 0)) {
    } else {
        var row = document.createElement('tr')
        s = document.createElement('td')
        s.innerHTML = data.teams.teamA.hand_score.toString()
        row.appendChild(s)
        s = document.createElement('td')
        s.innerHTML = data.teams.teamB.hand_score.toString()
        row.appendChild(s)
        document.querySelector('#scoreBoard').appendChild(row)
    }
    var total = document.querySelector('#scoreBoardTotal')
    total.innerHTML = ''
    s = document.createElement('td')
    s.innerHTML = data.teams.teamA.score.toString()
    total.appendChild(s)
    s = document.createElement('td')
    s.innerHTML = data.teams.teamB.score.toString()
    total.appendChild(s)
}

function playAudio(filename)    {
    var audio = new Audio('static/sounds/'+filename);
    audio.play()
    audio.onended(()=>{
        audio.remove()
    })
}

document.addEventListener('DOMContentLoaded', () => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port)

    socket.on('message', data =>    {
        taunt = parseInt(data.message)
        if ((taunt!=NaN)&&(taunt<31))   {
            playAudio(taunt+'.ogg')
        } else {
            var c = document.createElement('div')
            c.class = 'col-6'
            c.innerHTML = '<p><strong>' + data.username + ': </strong>' + data.message
            var r = document.createElement('div')
            r.class = 'row'
            r.appendChild(c)
            div = document.querySelector('#chat')
            div.appendChild(r)
            div.scrollTop = div.scrollHeight
        }
    })

    socket.emit('connected')
    socket.on('players_update', data => {
        teamPlayers = {teamA:[data.teams.teamA.player1.username, data.teams.teamA.player2.username],
        teamB: [data.teams.teamB.player1.username, data.teams.teamB.player2.username]}
        const content = templateWait(teamPlayers)
        document.querySelector('#body').innerHTML = content
        if (inGame) {
            const buttonOut = document.createElement("button")
            buttonOut.innerHTML = 'Salir';
            buttonOut.onclick = () => {
                socket.emit('player_left', playerData )
                inGame = false
            };
            document.querySelector('#teamOut').appendChild(buttonOut)
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
        if (inGame) {
            teamPlayers = {teamA:[data.teams.teamA.player1.username, data.teams.teamA.player2.username],
            teamB: [data.teams.teamB.player1.username, data.teams.teamB.player2.username]}
            const content = templateGame(teamPlayers)
            document.querySelector('#body').innerHTML = content
            updateScoreBoard(data)
            hand = data.teams[playerData.team][playerData.player].hand
            render_hand(socket, data)
            document.querySelector("#message").addEventListener("keyup", function(event) {
                if (event.keyCode === 13) {
                    socket.emit('message_sent', {message:this.value})
                    this.value = ''
                }
            })
        }
    })

    socket.on('card_played', data =>    {
        if (data.current_player.n == 2) {triunfo=data.card[1]}
        appendPlayedCard(data)
        render_hand(socket, data)
    })

    socket.on('new_round', data =>    {
        triunfo = ''
        appendPlayedCard(data)
        if (playerData.team == data.current_player.team && playerData.player == data.current_player.player) {
            document.querySelector('#turn').innerHTML = "<h5>Ganasteee</h5>"
        } else {
            document.querySelector('#turn').innerHTML = "<h5>Ganó " + data.current_player.username + "</h5>"
        }
        setTimeout(() => {
            document.querySelector('#plays').innerHTML = ''
            render_hand(socket, data)
        }, 3000)
    })

    socket.on('hand_over', data =>    {
        appendPlayedCard(data)
        setTimeout(() => {
            if (inGame) {
                updateScoreBoard(data)
                document.querySelector('#plays').innerHTML = ''
                hand = data.teams[playerData.team][playerData.player].hand
                render_hand(socket, data)
            }
        }, 5000)
    })

    socket.on('game_over', data =>    {
        appendPlayedCard(data)
        var mensaje
        mensaje = document.createElement('b')
        banner = document.createElement('h3')
        if (data.teams[playerData.team].winner == true)    {
            mensaje.innerHTML = 'Bien ahí wache'
            winners = teamPlayers[data.winner]
            sound = 'victory.wav'
        }   else {
            winners = teamPlayers[data.winner]
            mensaje.innerHTML = 'A veces se gana, a veces se pierde; pero siempre cagoneás'
            sound = 'defeat.wav'
        }
        setTimeout(() => {
            updateScoreBoard(data)
            banner.innerHTML = '¡Ganaron ' + winners[0] + ' y ' + winners[1] + '!'
            document.querySelector('#plays').innerHTML = ''
            document.querySelector('#turn').innerHTML = mensaje
            document.querySelector('#hand').appendChild(banner)
            playAudio(sound)
        }, 5000)
    })
})
