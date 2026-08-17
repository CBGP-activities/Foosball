let profiles = [];
let relations = [];
let playerInfos = [];

window.addEventListener("DOMContentLoaded", async () => {

    await loadData();

    const params = new URLSearchParams(window.location.search);
    const playerName = params.get("player");

    if (!playerName) {
        alert("No player specified.");
        return;
    }

    const profile = profiles.find(p => p.player === playerName);

    if (!profile) {
        alert("Unknown player : " + playerName);
        return;
    }

    const playerRelations = relations.filter(
        r => r.player === profile.player
    );

    renderProfile(profile);
    renderRelationCards(playerRelations);
    
    await loadPlayerRecentMatches(profile.player);
});


async function loadData(){

    const response1 =
        await fetch("results/player_profiles.json");

    profiles =
        await response1.json();


    const response2 =
        await fetch("results/player_relations.json");

    relations =
        await response2.json();
        
    const response3 =
		await fetch("results/player_infos.json");
	
	playerInfos =
		await response3.json();

}



function renderProfile(profile) {

    const s = profile.stats;


    document.getElementById("playerName").textContent =
        profile.player;


    document.getElementById("rank").textContent =
        s.rank ? "#" + s.rank : "-";


    document.getElementById("score").textContent =
        s.score.toFixed(2);


    document.getElementById("matches").textContent =
        s.matches;


    document.getElementById("winrate").textContent =
        (100*s.winrate_all_time).toFixed(1)+"%";


    // Nemesis ratio
    const nemesisCount =
        countPlayerNemesis(profile.player);

    const eligibleOpponents =
        countEligibleOpponents(profile.player);


    const nemesisRatio =
        eligibleOpponents > 0
            ? (100 * nemesisCount / eligibleOpponents).toFixed(0)
            : 0;


    document.getElementById("nemesisCount").textContent =
        `${nemesisCount}/${eligibleOpponents} (${nemesisRatio}%)`;



    document.getElementById("mu").textContent =
        s.mu.toFixed(2);


    document.getElementById("sigma").textContent =
        s.sigma.toFixed(2);


    document.getElementById("firstMatch").textContent =
        s.first_match;


    document.getElementById("lastMatch").textContent =
        s.last_match;


    document.getElementById("bestScore").textContent =
        s.highest_trueskill_score.toFixed(2);


    document.getElementById("bestStreak").textContent =
        s.longest_win_streak;


    document.getElementById("worstStreak").textContent =
        s.longest_loss_streak;
    
    document.getElementById("nemesisCountCard").onclick = () => {
		window.location.href =
			`rivalries.html?player=${encodeURIComponent(profile.player)}&view=nemesisTargets`;
	};
	
	const photo = document.getElementById("playerPhoto");
	const comment = document.getElementById("playerComment");
	const headerCard = document.querySelector(".player-header-card");
	
	const info = playerInfos.find(
		p => p.player === profile.player
	);
	
	// Photo
	if (info?.photo) {
		photo.src = info.photo;
		photo.style.display = "block";
		headerCard.classList.remove("no-photo");
	} else {
		photo.style.display = "none";
		headerCard.classList.add("no-photo");
	}
	
	// Commentaire
	if (info?.comment && info.comment.trim() !== "") {
		comment.textContent = info.comment;
		comment.style.display = "block";
	} else {
		comment.style.display = "none";
	}
}



function renderRelationCards(relations){

    const teammates = relations.filter(r => r.type === "teammate");
    const opponents = relations.filter(r => r.type === "opponent");


    const dreamMate = teammates
        .filter(r => r.matches >= 5)
        .sort((a,b) => {

            if (b.winrate !== a.winrate) {
                return b.winrate - a.winrate;
            }

            return b.matches - a.matches;

        })[0];


    const nemesis = opponents
        .filter(r => r.matches >= 5)
        .sort((a,b) => {

            if (a.winrate !== b.winrate) {
                return a.winrate - b.winrate;
            }

            return b.matches - a.matches;

        })[0];


    const victim = opponents
        .filter(r => r.matches >= 5)
        .sort((a,b) => {

            if (b.winrate !== a.winrate) {
                return b.winrate - a.winrate;
            }

            return b.matches - a.matches;

        })[0];


    const rival = opponents
        .filter(r => r.matches >= 5)
        .map(r => ({
            ...r,
            rivalScore:
                r.matches / (1 + Math.abs(r.winrate - 50))
        }))
        .sort((a,b) =>
            b.rivalScore - a.rivalScore
        )[0];



    fillRelationCard(
        "dreamMate",
        dreamMate,
        "games together"
    );


    fillRelationCard(
        "nemesis",
        nemesis,
        "games"
    );


    fillRelationCard(
        "victim",
        victim,
        "games"
    );


    fillRelationCard(
        "rival",
        rival,
        "games"
    );

}




function fillRelationCard(id, relation, label){

    const content = document.getElementById(id);
    const card = document.getElementById(id + "Card");


    if(!relation){

        content.innerHTML = `
            <div class="relation-name">-</div>
            <div class="relation-info">Not enough games</div>
        `;

        card.classList.remove("clickable");

        return;
    }


    content.innerHTML = `
        <div class="relation-name">
            ${relation.other}
        </div>

        <div class="relation-winrate">
            ${relation.winrate.toFixed(1)}%
        </div>

        <div class="relation-info">
            ${relation.matches} ${label}
        </div>
    `;


    card.classList.add("clickable");


    card.onclick = () => {

        window.location.href =
            `rivalries.html?player=${encodeURIComponent(relation.player)}&rivalry=${encodeURIComponent(id)}`;

    };

}




function countPlayerNemesis(playerName) {

    const players = [...new Set(
        relations.map(r => r.player)
    )];


    let count = 0;


    players.forEach(opponentPlayer => {

        const opponents = relations
            .filter(r =>
                r.player === opponentPlayer &&
                r.type === "opponent" &&
                r.matches >= 5
            )
            .sort((a,b) => {

                if (a.winrate !== b.winrate) {
                    return a.winrate - b.winrate;
                }

                return b.matches - a.matches;

            });


        const nemesis = opponents[0];


        if (nemesis && nemesis.other === playerName) {
            count++;
        }

    });


    return count;

}




function countEligibleOpponents(playerName) {

    const opponents = new Set();


    relations.forEach(r => {

        if (
            r.type === "opponent" &&
            r.matches >= 5 &&
            (r.player === playerName || r.other === playerName)
        ) {

            const opponent =
                r.player === playerName
                    ? r.other
                    : r.player;


            opponents.add(opponent);

        }

    });


    return opponents.size;

}

async function loadPlayerRecentMatches(playerName) {

    const { data, error } = await supabaseClient
        .from("matches")
        .select("*")
        .or(
            `rouge_p1.eq.${playerName},` +
            `rouge_p2.eq.${playerName},` +
            `bleu_p1.eq.${playerName},` +
            `bleu_p2.eq.${playerName}`
        )
        .order("id", { ascending: false })
        .limit(10);


    if (error) {

        console.error(
            "Error loading player matches:",
            error
        );

        document.getElementById(
            "playerRecentMatches"
        ).innerHTML = `
            <tr>
                <td colspan="3">
                    Unable to load matches.
                </td>
            </tr>
        `;

        return;
    }


    renderPlayerRecentMatches(
        data || [],
        playerName
    );

}


function renderPlayerRecentMatches(
    matches,
    playerName
) {

    const tbody =
        document.getElementById(
            "playerRecentMatches"
        );


    tbody.innerHTML = "";


    if (!matches.length) {

        tbody.innerHTML = `
            <tr>
                <td colspan="3" style="
                    text-align:center;
                    color:var(--muted);
                ">
                    No matches found.
                </td>
            </tr>
        `;

        document.getElementById(
            "recentWinrate"
        ).textContent = "-";

        return;

    }


    // =====================================================
    // WIN RATE - LAST 10 MATCHES
    // =====================================================

    let wins = 0;


    matches.forEach(match => {

        const playerIsRed =
            match.rouge_p1 === playerName ||
            match.rouge_p2 === playerName;


        const playerIsBlue =
            match.bleu_p1 === playerName ||
            match.bleu_p2 === playerName;


        const playerWon =
            (playerIsRed && match.vainqueur === "rouge") ||
            (playerIsBlue && match.vainqueur === "bleu");


        if (playerWon) {

            wins++;

        }

    });


    const winrate =
        (100 * wins) / matches.length;


    document.getElementById(
        "recentWinrate"
    ).textContent =
        winrate.toFixed(1) + "%";


    // =====================================================
    // AFFICHAGE DES MATCHS
    // Même affichage que index.html
    // =====================================================

    matches.forEach(match => {

            const tr =
                document.createElement("tr");


            const redWinner =
                match.vainqueur === "rouge";


            const blueWinner =
                match.vainqueur === "bleu";


            tr.innerHTML = `

                <td class="match-date">
                    ${formatDate(match.date)}
                </td>


                <td class="${
                    redWinner
                        ? "winner"
                        : ""
                }">

                    🔴
                    ${match.rouge_p1}
                    /
                    ${match.rouge_p2}

                </td>


                <td class="${
                    blueWinner
                        ? "winner"
                        : ""
                }">

                    🔵
                    ${match.bleu_p1}
                    /
                    ${match.bleu_p2}

                </td>

            `;


            tbody.appendChild(tr);

        });

}


// =====================================================
// HELPERS
// =====================================================

function formatDate(dateString) {

    return new Date(dateString)
        .toLocaleDateString(
            "fr-FR"
        );

}


