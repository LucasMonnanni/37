const templateWait = Handlebars.compile(document.querySelector('#waitlist').innerHTML);
const templateGameList = Handlebars.compile(document.querySelector('#gamelist').innerHTML);
const templateGame = Handlebars.compile(document.querySelector('#game').innerHTML);
var gameID = 'lobby';
var GAMES;
var inGame = false;
var playerData;
var teamPlayers;
var triunfo = '';
var hand;
var epitetos = ['compañero', 'compañera', 'campeón', 'campeona', 'máquina', 'animal', 'loco turbina', 'vieji', 'viejita', 'hermano', 'hermana']
var freezeClic = false;

function choose(choices) {
  var index = Math.floor(Math.random() * choices.length);
  return choices[index];
}

function render_turn(data)  {
    if (playerData.team == data.current_player.team && playerData.player == data.current_player.player) {
        document.querySelector('#turn').innerHTML = "<h4>Jugás vos, " + choose(epitetos) + "</h4>"
    } else {
        document.querySelector('#turn').innerHTML = "<h4>Juega " + data.current_player.username + "</h4>"
    }
}

function render_hand(socket, data)  {
    document.querySelector('#hand').innerHTML = ''
    for (let i = 0; i<hand.length; i++ ) {
        const button = document.createElement("img")
        var path = '/static/images/'+hand[i][1]+'/'+hand[i][0]+'.png'
        button.src = path
        button.classList.add('card')
        button.style.margin = '1px'
        button.id = 'boton'+i
        button.onclick = () => {
            if (playerData.team == data.current_player.team && playerData.player == data.current_player.player)  {
                suits = hand.map(x => {return x[1]})
                if (hand[i][1]==triunfo || data.current_player.n==1 || !(suits.includes(triunfo)) )    {
                    for (k=0; k<hand.length; k++)   {
                        document.querySelector('#boton'+k).onclick = ()=>{}
                    }
                    document.querySelector('#boton'+i).remove()
                    card_data = {team: playerData.team, player: playerData.player, number: hand[i][0], suit: hand[i][1], id:gameID}
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
    console.log('render_hand')
}

function appendPlayedCard(data) {
    const line = document.createElement("img")
    let path = '/static/images/'+data.card_data.card[1]+'/'+data.card_data.card[0]+'.png'
    line.src = path
    line.title = data.card_data.username
    line.style.margin = '5px'
    line.style.width = '100px'
    document.querySelector('#plays').appendChild(line)
    console.log('appendPlayedCard')
}

function updateScoreBoard(data) {
    var s
    if (data.two)   {
        hand_score = [data.teams.player1.hand_score, data.teams.player2.hand_score]
        score = [data.teams.player1.score, data.teams.player2.score]
    }   else {
        hand_score = [data.teams.teamA.hand_score, data.teams.teamB.hand_score]
        score = [data.teams.teamA.score, data.teams.teamB.score]
    }

    if ((hand_score[0] % 3 == 0)&&(hand_score[1] % 3 == 0)) {
    } else {
        var row = document.createElement('tr')
        s = document.createElement('td')
        s.innerHTML = hand_score[0].toString()
        row.appendChild(s)
        s = document.createElement('td')
        s.innerHTML = hand_score[1].toString()
        row.appendChild(s)
        document.querySelector('#scoreBoard').appendChild(row)
    }
    var total = document.querySelector('#scoreBoardTotal')
    total.innerHTML = ''
    s = document.createElement('td')
    s.innerHTML = score[0].toString()
    total.appendChild(s)
    s = document.createElement('td')
    s.innerHTML = score[1].toString()
    total.appendChild(s)
    console.log('updateScoreBoard')
}

function playAudio(filename)    {
    var audio = new Audio('static/sounds/'+filename);
    audio.play()
    audio.onended = ()=>{
        audio.remove()
    }
}

function initChat(socket)   {
    document.querySelector("#message").addEventListener("keyup", function(event) {
        if (event.keyCode === 13) {
            socket.emit('message_sent', {message:this.value, id:gameID})
            this.value = ''
        }
    })
    socket.on('message', data =>    {
        let taunt = parseInt(data.message)
        if ((taunt!=NaN)&&(taunt<31))   {
            playAudio(taunt+'.ogg')
        } else {
            var c = document.createElement('div')
            c.classList.add('col-6')
            c.innerHTML = '<p><strong>' + data.username + ': </strong>' + data.message
            var r = document.createElement('div')
            r.classList.add('row')
            r.appendChild(c)
            div = document.querySelector('#chat')
            div.appendChild(r)
            div.scrollTop = div.scrollHeight
        }
    })
    console.log('initChat')
}

function freezeClicFn(e) {
    if (freezeClic) {
        e.stopPropagation();
        e.preventDefault();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port)
    document.addEventListener("click", freezeClicFn, true)
    if (gameID == 'lobby') {
        socket.emit('connected')
    } else {
        socket.emit('join_game', {id: gameID})
    }

    socket.on('games_update', data =>   {
        GAMES = data.games
        const content = templateGameList()
        document.querySelector('#body').innerHTML = content
        gameID = 'lobby'
        initChat(socket)
        for (i=0;i<data.games.length;i++)   {
            const r = document.createElement('div')
            r.classList.add('row', 'justify-content-center', 'game', 'p-3')
            g = document.createElement('div')
            g.classList.add('col', 'p-3')
            const game = data.games[i]
            if (game.full) {
                r.classList.add('full')
            }
            g.appendChild(r)
            c = document.createElement('div')
            c.classList.add('col-4')
            b = document.createElement('strong')
            b.innerHTML = data.games[i].name
            r.appendChild(c)
            c.appendChild(b)
            c = document.createElement('div')
            c.classList.add('col-4', 'ml-auto')
            b = document.createElement('strong')
            if (data.games[i].two)  {
                b.innerHTML = "1vs1"
            }   else {
                b.innerHTML = "2vs2"
            }
            r.appendChild(c)
            c.appendChild(b)
            r.onclick = (data) =>{
                socket.emit('join_game', {id: game.id})
            }
            document.querySelector('#games').appendChild(r)
        }
        for (i=0;i<data.lobby.length;i++)   {
            r = document.createElement('div')
            r.classList.add('row')
            r.innerHTML = "<strong>" + data.lobby[i] + "</strong>"
            document.querySelector("#lobby").appendChild(r)
        }
        document.querySelector("#gameName").addEventListener("keyup", function(event) {
            if (event.keyCode === 13) {
                socket.emit('make_game', {name:this.value, two: document.querySelector('#gameTwo').value})
                this.value = ''
            }
        })
        console.log('games_update')
    })

    socket.on('lobby_update', data =>   {
        document.querySelector("#lobby").innerHTML = ''
        for (i=0;i<data.lobby.length;i++)   {
            r = document.createElement('div')
            r.classList.add('row')
            r.innerHTML = "<strong>" + data.lobby[i] + "</strong>"
            document.querySelector("#lobby").appendChild(r)
        }
    })

    socket.on('players_update', data => {
        if (data.two)   {
            teamPlayers = {teamA:[data.teams.player1.username],
            teamB: [data.teams.player2.username]}
        } else {
            teamPlayers = {teamA:[data.teams.teamA.player1.username, data.teams.teamA.player2.username],
            teamB: [data.teams.teamB.player1.username, data.teams.teamB.player2.username]}
        }
        const content = templateWait(teamPlayers)
        document.querySelector('#body').innerHTML = content
        gameID = data.id
        buttonLeave = document.querySelector('#leaveGame')
        buttonLeave.onclick = () => {
            socket.emit('leave_game', {id:gameID})
        }
        if (inGame) {
            const buttonOut = document.createElement("button")
            buttonOut.innerHTML = 'Salir del equipo';
            buttonOut.onclick = () => {
                socket.emit('player_left', {team:playerData.team, player:playerData.player, id:gameID} )
                inGame = false
                playerData = {}
            };
            document.querySelector('#teamOut').appendChild(buttonOut)
        } else {
            if (data.two)   {
                if (data.teams.player1.username==null || data.teams.player2.username==null)  {
                    const buttonA = document.createElement("button")
                    buttonA.innerHTML = 'Entrar'
                    buttonA.onclick = () => {
                        socket.emit('player_enter', {team:'', id:gameID})
                    }
                    document.querySelector('#teamA').appendChild(buttonA)
                };
            } else {
                if (!(data.teams.teamA.full))  {
                    const buttonA = document.createElement("button")
                    buttonA.innerHTML = 'Entrar'
                    buttonA.onclick = () => {
                        socket.emit('player_enter', {team:'teamA', id:gameID})
                    }
                    document.querySelector('#teamA').appendChild(buttonA)
                };
                if (!(data.teams.teamB.full))  {
                    const buttonB = document.createElement("button")
                    buttonB.innerHTML = 'Entrar'
                    buttonB.onclick = () => {
                        socket.emit('player_enter', {team:'teamB', id:gameID})
                    }
                    document.querySelector('#teamB').appendChild(buttonB)
                }
            }
        }
        console.log('players_update')
    })

    socket.on('player_data', data =>    {
        inGame = true
        playerData = {team: data.team, player: data.player}
        console.log('player_data')
    })

    socket.on('game_starts', data =>    {
        gameID = data.id
        if (inGame) {
            if (data.two)   {
                teamPlayers = {teamA:[data.teams.player1.username],
                teamB: [data.teams.player2.username]}
                hand = data.teams[playerData.player].hand
            }   else {
                teamPlayers = {teamA:[data.teams.teamA.player1.username, data.teams.teamA.player2.username],
                teamB: [data.teams.teamB.player1.username, data.teams.teamB.player2.username]}
                hand = data.teams[playerData.team][playerData.player].hand
            }
            const content = templateGame(teamPlayers)
            document.querySelector('#body').innerHTML = content
            updateScoreBoard(data)
            render_turn(data)
            render_hand(socket, data)
            initChat(socket)
        }
        console.log('game_starts')
    })

    socket.on('card_played', data =>    {
        if (data.current_player.n == 2) {triunfo=data.card_data.card[1]}
        appendPlayedCard(data)
        render_turn(data)
        render_hand(socket, data)
        console.log('card_played')
    })

    socket.on('new_round', data =>    {
        triunfo = ''
        appendPlayedCard(data)
        freezeClic = true
        if (playerData.team == data.current_player.team && playerData.player == data.current_player.player) {
            document.querySelector('#turn').innerHTML = "<h5>Levantás vos</h5>"
        } else {
            document.querySelector('#turn').innerHTML = "<h5>Levantó " + data.current_player.username + "</h5>"
        }
        if (data.two)   {
            hand = data.teams[playerData.player].hand
        }
        setTimeout(() => {
            document.querySelector('#plays').innerHTML = ''
            render_hand(socket, data)
            if (data.drawn) {
                var otherPlayer = ['player1', 'player2'].filter((val, ind, arr)=> {return val!=playerData.player})
                const drawn = document.createElement("img")
                var path = '/static/images/'+data.drawn[otherPlayer][1]+'/'+data.drawn[otherPlayer][0]+'.png'
                drawn.src = path
                drawn.classList.add('card')
                drawn.id = 'drawn'
                document.querySelector('#turn').innerHTML = "<h5>" + data.teams[otherPlayer].username + " pescó:</h5>"
                document.querySelector('#plays').appendChild(drawn)
                setTimeout(()=> {
                    document.querySelector('#drawn').remove()
                    render_turn(data)
                    freezeClic = false
                }, 2000)
            } else {
                render_turn(data)
                freezeClic = false
            }
        }, 2000)
        console.log('new_round')
    })

    socket.on('hand_over', data =>    {
        triunfo = ''
        appendPlayedCard(data)
        if (playerData.team == data.current_player.team && playerData.player == data.current_player.player) {
            document.querySelector('#turn').innerHTML = "<h5>Levantás vos</h5>"
        } else {
            document.querySelector('#turn').innerHTML = "<h5>Levantó " + data.current_player.username + "</h5>"
        }
        freezeClic = true
        setTimeout(() =>    {
            if (playerData.team == data.hand_score.winner) {
                document.querySelector('#turn').innerHTML = "<h5>Ganaste " + data.hand_score[playerData.team].toString() + " a " + (11-data.hand_score[playerData.team]).toString() + "</h5>"
            } else {
                document.querySelector('#turn').innerHTML = "<h5>Perdiste " + (11-data.hand_score[playerData.team]).toString() + " a " + data.hand_score[playerData.team].toString() + "</h5>"
            }
            document.querySelector('#plays').innerHTML = ''
            setTimeout(() => {
                updateScoreBoard(data)
                if (data.two)   {
                    hand = data.teams[playerData.player].hand
                } else {
                    hand = data.teams[playerData.team][playerData.player].hand
                }
                render_hand(socket, data)
                render_turn(data)
                freezeClic = false
            }, 5000)
        }, 3000)
        console.log('hand_over')
    })

    socket.on('game_over', data =>    {
        appendPlayedCard(data)
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
        console.log('game_over')
    })
})
