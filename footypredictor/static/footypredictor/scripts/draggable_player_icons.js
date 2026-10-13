console.log("draggable_player_icons.js loaded");

let newX = 0, newY = 0, startX = 0, startY = 0;
let currentPlayer = null;

// Get all player elements from both pitches
const allPlayers = document.querySelectorAll('.player');

// Add event listeners to all players
allPlayers.forEach(player => {
    player.addEventListener('mousedown', mouseDown);
});

function mouseDown(e) {
    currentPlayer = e.target;
    startX = e.clientX;
    startY = e.clientY;

    document.addEventListener('mousemove', mouseMove);
    document.addEventListener('mouseup', mouseUp);
}

function mouseMove(e) {
    if (!currentPlayer) return;

    newX = startX - e.clientX;
    newY = startY - e.clientY;

    startX = e.clientX;
    startY = e.clientY;

    currentPlayer.style.top = (currentPlayer.offsetTop - newY) + "px";
    currentPlayer.style.left = (currentPlayer.offsetLeft - newX) + "px";
}

function mouseUp(e) {
    document.removeEventListener('mousemove', mouseMove);
    currentPlayer = null;
}

//Parameter: Player object
function player_magnet(player){

    let initials = player.getInitials();
    return (
        <div className="player_magnet">
            <title>{initials}<br /> {player.number}</title>
        </div>
    )
}

class Player{
    constructor(name, number, x_coord, y_coord){
        this.name = name;
        this.number = number;
        this.x_coord = x_coord;
        this.y_coord = y_coord;
    }

    getInitials(){ // Split wherever there is a space in the sentence
    return this.name.split(/\s+/).map(word => word[0]).join('')
}
}