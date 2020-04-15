const templateWait = Handlebars.compile(document.querySelector('#waitlist').innerHTML);
var players = null;

document.addEventListener('DOMContentLoaded', () => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    socket.on('players_update', data => {
        players = data.players;
        const content = templateWait({'players':data.players});
        document.querySelector('#body').innerHTML = content;
    });

});
