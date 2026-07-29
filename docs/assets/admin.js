// =====================================================
// Foosball Admin
// admin.js
// =====================================================


let players = [];

let selectedPlayers = {
    red1: null,
    red2: null,
    blue1: null,
    blue2: null
};

let winner = null;

let editingMatchId = null;



// =====================================================
// Initialisation
// =====================================================

window.addEventListener("DOMContentLoaded", async () => {

    await loadPlayers();
	await loadRecentMatches();
	
    createPlayerSearch("red1");
    createPlayerSearch("red2");
    createPlayerSearch("blue1");
    createPlayerSearch("blue2");

    initWinnerButtons();
    initDate();

    initAddPlayer();
	initSaveButton();
	
});


// =====================================================
// Chargement joueurs
// =====================================================

async function loadPlayers(){

    const response = await fetch(
        "results/players.json"
    );

    players = await response.json();

}


// =====================================================
// Player Search Component
// =====================================================

function createPlayerSearch(id){

    const container =
        document.getElementById(id);


    container.innerHTML = `

        <div class="search-wrapper">

            <input
                class="player-input"
                placeholder="Choose a player"
                autocomplete="off">

            <div class="suggestions"></div>

        </div>

    `;


    const input =
        container.querySelector(".player-input");


    const suggestions =
        container.querySelector(".suggestions");


    let currentIndex = -1;


    input.addEventListener(
        "input",
        () => {

            showSuggestions(
                id,
                input.value,
                suggestions
            );

            currentIndex = -1;

        }
    );


    input.addEventListener(
        "keydown",
        e => {


            const items =
                suggestions.querySelectorAll(
                    ".suggestion"
                );


            if(e.key==="ArrowDown"){

                e.preventDefault();

                currentIndex++;

                if(currentIndex >= items.length)
                    currentIndex = 0;


                highlight(
                    items,
                    currentIndex
                );

            }


            if(e.key==="ArrowUp"){

                e.preventDefault();

                currentIndex--;

                if(currentIndex < 0)
                    currentIndex =
                    items.length-1;


                highlight(
                    items,
                    currentIndex
                );

            }


            if(e.key==="Enter"){

                e.preventDefault();

                if(items[currentIndex]){

                    selectPlayer(
                        id,
                        items[currentIndex].textContent
                    );

                }

            }


            if(e.key==="Escape"){

                suggestions.innerHTML="";

            }


        }
    );


    document.addEventListener(
        "click",
        e => {

            if(!container.contains(e.target)){

                suggestions.innerHTML="";

            }

        }
    );


}



function showSuggestions(
    id,
    value,
    box
){

    box.innerHTML="";


    if(!value)
        return;


    const selected =
        Object.values(selectedPlayers);


    const results =
        players
        .filter(p =>
            p.toLowerCase()
            .includes(
                value.toLowerCase()
            )
        )
        .filter(p =>
            !selected.includes(p)
        )
        .slice(0,8);



    results.forEach(player=>{


        const div =
            document.createElement("div");


        div.className =
            "suggestion";


        div.textContent =
            player;


        div.onclick = () =>
            selectPlayer(
                id,
                player
            );


        box.appendChild(div);


    });

}



function highlight(items,index){

    items.forEach(
        item =>
            item.classList.remove(
                "active"
            )
    );


    if(items[index])
        items[index]
        .classList
        .add("active");

}



function selectPlayer(
    id,
    player
){

    selectedPlayers[id]=player;


    const container =
        document.getElementById(id);


    const input =
        container.querySelector(
            ".player-input"
        );


    input.value =
        player;


    container
    .querySelector(
        ".suggestions"
    )
    .innerHTML="";


    updateAllSearches();

}



// =====================================================
// Rafraîchir les listes après sélection
// =====================================================

function updateAllSearches(){

    document
    .querySelectorAll(
        ".player-input"
    )
    .forEach(input=>{

        input.dispatchEvent(
            new Event("input")
        );

    });

}



// =====================================================
// Winner buttons
// =====================================================

function initWinnerButtons(){

    const red =
        document.getElementById(
            "winnerRed"
        );


    const blue =
        document.getElementById(
            "winnerBlue"
        );

	red.onclick = () => {
	
		winner = "rouge";
	
		red.classList.add("selected");
		blue.classList.remove("selected");
	
	};
	
	blue.onclick = () => {
	
		winner = "bleu";
	
		blue.classList.add("selected");
		red.classList.remove("selected");
	
	};

}


// =====================================================
// Date
// =====================================================

function initDate(){

    const input =
        document.getElementById(
            "matchDate"
        );


    input.value =
        new Date()
        .toISOString()
        .substring(0,10);

}



// =====================================================
// Ajout nouveau joueur
// =====================================================

function initAddPlayer(){

    const input =
        document.getElementById(
            "newPlayer"
        );


    const button =
        document.getElementById(
            "addPlayer"
        );


    button.onclick = () => {


        const name =
            input.value.trim();


        if(!name)
            return;


        // éviter doublon
        const exists =
            players.some(
                p =>
                p.toLowerCase()
                ===
                name.toLowerCase()
            );


        if(exists){

            alert(
                "This player already exists"
            );

            return;

        }


        // ajout mémoire
        players.push(name);


        // nettoyage
        input.value="";


        // rafraîchir les recherches
        updateAllSearches();


        alert(
            `${name} added`
        );


    };

}


// =====================================================
// Sauvegarde d'un match
// =====================================================

async function saveMatch(){


    const date =
        document.getElementById(
            "matchDate"
        ).value;


    if(
        !selectedPlayers.red1 ||
        !selectedPlayers.red2 ||
        !selectedPlayers.blue1 ||
        !selectedPlayers.blue2
    ){

        alert(
            "Please select the 4 players"
        );

        return;

    }


    if(!winner){

        alert(
            "Please select the winner"
        );

        return;

    }



    const match = {


        date: date,


        rouge_p1:
            selectedPlayers.red1,


        rouge_p2:
            selectedPlayers.red2,


        bleu_p1:
            selectedPlayers.blue1,


        bleu_p2:
            selectedPlayers.blue2,


        vainqueur:
            winner


    };


	try {
	
	
		let data;
		let error;
		
		if (editingMatchId) {
		
			({ data, error } = await supabaseClient
				.from("matches")
				.update(match)
				.eq("id", editingMatchId));
		
		} else {
		
			({ data, error } = await supabaseClient
				.from("matches")
				.insert(match));
		
		}
	
	
	
		if(error){
		
			console.error("Supabase error:", error);
		
			alert(
				"❌ " + error.message
			);
		
			return;
		
		}
	
	
		alert("✅ Match saved!");
		
		resetMatchForm();
		
		await loadRecentMatches();
		
		
		console.log("Saved:", data);
	
	
	}
	catch(e){
	
		console.error(e);
	
		alert(
			"❌ Connection error"
		);
	
	}


}
function initSaveButton(){

    document
    .getElementById(
        "saveMatch"
    )
    .onclick = saveMatch;

}

function resetMatchForm(){

    editingMatchId = null;

	document.getElementById("saveMatch").textContent =
		"✔ Save Match";
    
    selectedPlayers.red1 = null;
    selectedPlayers.red2 = null;
    selectedPlayers.blue1 = null;
    selectedPlayers.blue2 = null;

    winner = null;

    document
        .querySelectorAll(".player-input")
        .forEach(input => {

            input.value = "";

        });

    document
        .querySelectorAll(".suggestions")
        .forEach(list => {

            list.innerHTML = "";

        });

    document
        .getElementById("winnerRed")
        .classList.remove("selected");

    document
        .getElementById("winnerBlue")
        .classList.remove("selected");
        
    document
		.querySelector("#red1 .player-input")
		.focus();

}


async function loadRecentMatches() {

    const { data, error } = await supabaseClient
        .from("matches")
        .select("*")
        .order("id", { ascending: false })
        .limit(20);

    if (error) {

        console.error(error);
        return;

    }

    const container =
        document.getElementById("recentMatches");

    container.innerHTML = "";

    data.forEach(match => {

        const card = document.createElement("div");

        card.className = "recent-match";

        card.innerHTML = `
            <div class="recent-date">
                📅 ${match.date}
            </div>

            <div class="recent-red">
                🔴 ${match.rouge_p1} • ${match.rouge_p2}
            </div>

            <div class="recent-blue">
                🔵 ${match.bleu_p1} • ${match.bleu_p2}
            </div>

            <div class="recent-winner">
                🏆 Winner :
                ${match.vainqueur === "rouge" ? "🔴 Red" : "🔵 Blue"}
            </div>

            <div class="recent-actions">

                <button onclick="editMatch(${match.id})">
                    ✏ Edit
                </button>

                <button onclick="deleteMatch(${match.id})">
                    🗑 Delete
                </button>

            </div>
        `;

        container.appendChild(card);

    });

}


    
async function editMatch(id){

    const { data, error } = await supabaseClient
        .from("matches")
        .select("*")
        .eq("id", id)
        .single();

    if(error){

        console.error(error);
        return;

    }

    editingMatchId = data.id;

    document.getElementById("saveMatch").textContent =
        "💾 Update Match";

    selectedPlayers.red1 = data.rouge_p1;
    selectedPlayers.red2 = data.rouge_p2;
    selectedPlayers.blue1 = data.bleu_p1;
    selectedPlayers.blue2 = data.bleu_p2;

    document.querySelector("#red1 .player-input").value = data.rouge_p1;
    document.querySelector("#red2 .player-input").value = data.rouge_p2;
    document.querySelector("#blue1 .player-input").value = data.bleu_p1;
    document.querySelector("#blue2 .player-input").value = data.bleu_p2;

    winner = data.vainqueur;

	document.getElementById("winnerRed")
		.classList.toggle("selected", winner==="rouge");
	
	document.getElementById("winnerBlue")
		.classList.toggle("selected", winner==="bleu");

    document.getElementById("matchDate").value =
        data.date;
        
    window.scrollTo({
        top:0,
        behavior:"smooth"
    });

}

async function deleteMatch(id){

    if(!confirm("Delete this match?"))
        return;

    const { error } = await supabaseClient
        .from("matches")
        .delete()
        .eq("id", id);

    if(error){

        alert(error.message);
        return;

    }

    await loadRecentMatches();

}
