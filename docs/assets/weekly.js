// =====================================================
// Foosball Weekly Summary
// weekly.js
// =====================================================


let summaries = [];
let summary = null;


window.addEventListener(
	"DOMContentLoaded",
		async()=>{

		await loadWeeklySummary();

		populateWeekSelector();

		loadSelectedWeek();

});




// =====================================================
// Load JSON
// =====================================================

async function loadWeeklySummary(){

const response =
await fetch(
"results/weekly_summary.json"
);


summaries =
await response.json();


}

function populateWeekSelector(){


	const selector =
		document.getElementById(
		"weekSelector"
		);
	
	
	summaries
		.slice()
		.reverse()
		.forEach((week,index)=>{
	
	
	const option =
		document.createElement("option");
	
	
	option.value =
		summaries.length-1-index;
	
	
	option.textContent =
		`${formatDate(week.week_start)}
		-
		${formatDate(week.week_end)}`;
	
	
	selector.appendChild(option);
	
	
	});
	
	
	selector.addEventListener(
		"change",
		()=>{
	
		summary =
		summaries[
		selector.value
		];
		
		renderWeeklySummary();
	
		}
	
	);


	document.getElementById(
		"prevWeek"
	)
	.addEventListener(
		"click",
		()=>{
	
			let index =
			Number(selector.value);
	
	
			if(index > 0){
	
				selector.value =
				index-1;
	
				summary =
				summaries[index-1];
	
				renderWeeklySummary();
	
			}
	
		}
	);
	
	
	
	document.getElementById(
		"nextWeek"
	)
	.addEventListener(
		"click",
		()=>{
	
			let index =
			Number(selector.value);
	
	
			if(index < summaries.length-1){
	
				selector.value =
				index+1;
	
				summary =
				summaries[index+1];
	
				renderWeeklySummary();
	
			}
	
		}
	);


}

function loadSelectedWeek(){

	if(summaries.length===0){
		return;
	}
	
	summary =
		summaries[
		summaries.length-1
		];
	
	
	document.getElementById(
		"weekSelector"
		).value =
		summaries.length-1;
	
	
	renderWeeklySummary();

}




// =====================================================
// Main rendering
// =====================================================

function playerLink(name){

return `
<a 
href="player.html?player=${encodeURIComponent(name)}"
class="weekly-player-link">

${name}

</a>
`;

}


function renderWeeklySummary(){


    document.getElementById(
        "weekTitle"
    ).innerHTML =
        `
        📰 Week summary
        <br>
        <small>
        ${formatDate(summary.week_start)}
        -
        ${formatDate(summary.week_end)}
        </small>
        `;



    document.getElementById(
        "intro"
    ).innerHTML =
        generateIntro();



    const container =
        document.getElementById(
            "weeklyContent"
        );


    container.innerHTML = "";


    addSection(
        container,
        "🆕 New faces",
        summary.new_players,
        renderNewPlayers
    );


    addSection(
        container,
        "⚽ Most active players",
        summary.most_active,
        renderActive
    );


    addSection(
        container,
        "🏆 Most victories",
        summary.most_wins,
        renderWins
    );


    addSection(
        container,
        "📈 Biggest TrueSkill improvement",
        summary.best_trueskill_gain,
        renderTrueSkill
    );


    addSection(
        container,
        " Biggest ranking climbers",
        summary.ranking_climbers,
        renderClimbers
    );


    addSection(
        container,
        "🔥 Hot streak",
        summary.hot_streak,
        renderStreak
    );

}



// =====================================================
// Sections
// =====================================================

function addSection(
    container,
    title,
    data,
    renderer
){


    if(!data || data.length===0)
        return;


    const section =
        document.createElement(
            "section"
        );


    section.className =
        "card";


    section.innerHTML =
        `
        <h2>${title}</h2>

        <div class="weekly-ranking">

        ${
            data
            .map(
                (x,i)=>
                renderer(x,i)
            )
            .join("")
        }

        </div>
        `;


    container.appendChild(section);

}



// =====================================================
// Renderers
// =====================================================


function medal(index){

    return [
        "🥇",
        "🥈",
        "🥉"
    ][index] || "⭐";

}



function renderNewPlayers(
    player,
    index
){

    return `
    <div class="weekly-player">

        <span>
        ${medal(index)}
        ${playerLink(player.player)}
        </span>

        <span>
        ${player.matches}
		${plural(player.matches,"game")}
        </span>

    </div>
    `;

}




function renderActive(
    player,
    index
){

    return `
    <div class="weekly-player">

        <span>
        ${medal(index)}
        ${playerLink(player.player)}
        </span>

        <span>
		${player.matches}
		${plural(player.matches,"game")}
        </span>

    </div>
    `;

}




function renderWins(
    player,
    index
){

    return `
    <div class="weekly-player">

        <span>
        ${medal(index)}
        ${playerLink(player.player)}
        </span>

        <span>
		${player.wins}
		${plural(player.wins,"win")}
        (${player.matches}
        ${plural(player.matches,"game")})
        </span>

    </div>
    `;

}




function renderTrueSkill(
    player,
    index
){

    return `
    <div class="weekly-player">

        <span>
        ${medal(index)}
        ${playerLink(player.player)}
        </span>

        <span class="positive">
        +${player.gain.toFixed(2)}
        </span>

    </div>
    `;

}


function renderClimbers(
    player,
    index
){

    return `
    <div class="weekly-player">

        <span>
        ${medal(index)}
        ${playerLink(player.player)}
        </span>

        <span class="positive">
        ⬆ ${player.places}
        ${plural(player.places, "place")}
        <small>
        (${player.old_rank} → ${player.new_rank})
        </small>
        </span>

    </div>
    `;

}





function renderStreak(
    player,
    index
){

    return `
    <div class="weekly-player">

        <span>
        ${medal(index)}
        ${playerLink(player.player)}
        </span>

        <span>
		${player.wins}
		${plural(player.wins,"consecutive win")}
        </span>

    </div>
    `;

}


// =====================================================
// Intro text
// =====================================================

function generateIntro(){


    let text =
        `
        This week,
        <strong>${summary.matches_played}</strong>
        matches were played.
        `;



    if(summary.new_players.length){

        text +=
        `
        Welcome to
        <strong>
        ${summary.new_players.length}
        new player(s)
        </strong>
        joining the competition!
        `;

    }



    if(summary.best_trueskill_gain.length){

        const best =
            summary.best_trueskill_gain[0];


        text +=
        `
        The biggest improvement was achieved by
        <strong>${best.player}</strong>
        with a
        <strong>
        +${best.gain.toFixed(2)}
        </strong>
        TrueSkill gain.
        `;

    }


    return text;

}



// =====================================================
// Helpers
// =====================================================

function formatDate(date){

    return new Date(date)
        .toLocaleDateString(
            "en-US",
            {
                year:"numeric",
                month:"long",
                day:"numeric"
            }
        );

}

function plural(value, singular, pluralForm=null){

    if(value === 1){
        return singular;
    }

    return pluralForm || singular + "s";

}

