let profiles = [];
let relations = [];

window.addEventListener("DOMContentLoaded", async () => {

    await loadData();

    const params = new URLSearchParams(window.location.search);
    const playerName = params.get("player");
	const rivalry = params.get("rivalry");
	const view = params.get("view") ?? "ranking";

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
	
	if (view === "nemesisTargets") {
		renderNemesisTargets(profile);
	}
	else{
		renderRanking(
			getRivalryRanking(playerRelations, rivalry),
			rivalry
		);

	}
	
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

}


function renderProfile(profile) {

    const s = profile.stats;
	
	document.getElementById("backPlayerName").textContent =
		profile.player;
	
	document.getElementById("backLink").href =
		`player.html?player=${encodeURIComponent(profile.player)}`;
    
    document.getElementById("playerName").textContent =
        "👤 " + profile.player;

    document.getElementById("playerSubtitle").textContent =
        `${s.matches} matches`;
    
}

function getRivalryRanking(relations, rivalry) {

    switch (rivalry) {

        case "dreamMate":

            return relations
                .filter(r =>
                    r.type === "teammate" &&
                    r.matches >= 5
                )
                .sort((a, b) => {

                    if (b.winrate !== a.winrate) {
                        return b.winrate - a.winrate;
                    }

                    return b.matches - a.matches;

                });

        case "nemesis":

            return relations
                .filter(r =>
                    r.type === "opponent" &&
                    r.matches >= 5
                )
                .sort((a, b) => {

                    if (a.winrate !== b.winrate) {
                        return a.winrate - b.winrate;
                    }

                    return b.matches - a.matches;

                });

        case "victim":

            return relations
                .filter(r =>
                    r.type === "opponent" &&
                    r.matches >= 5
                )
                .sort((a, b) => {

                    if (b.winrate !== a.winrate) {
                        return b.winrate - a.winrate;
                    }

                    return b.matches - a.matches;

                });

        case "rival":

            return relations
                .filter(r =>
                    r.type === "opponent" &&
                    r.matches >= 5
                )
                .map(r => ({
                    ...r,
                    rivalScore:
                        r.matches /
                        (1 + Math.abs(r.winrate - 50))
                }))
                .sort((a, b) =>
                    b.rivalScore - a.rivalScore
                );

        default:
            return [];
    }

}

function renderRelationCards(relations){

    fillRelationCard(
        "dreamMate",
        getRivalryRanking(relations, "dreamMate")[0],
        "games together"
    );

    fillRelationCard(
        "nemesis",
        getRivalryRanking(relations, "nemesis")[0],
        "games"
    );

    fillRelationCard(
        "victim",
        getRivalryRanking(relations, "victim")[0],
        "games"
    );

    fillRelationCard(
        "rival",
        getRivalryRanking(relations, "rival")[0],
        "games"
    );
}

function renderRanking(ranking, rivalry) {

    const titles = {
        dreamMate: "Dream Mate",
        nemesis: "Nemesis",
        victim: "Victim",
        rival: "Greatest Rival"
    };

    document.getElementById("tableTitle").textContent =
        titles[rivalry] ?? "Ranking";

    const tbody = document.getElementById("rankingBody");

    tbody.innerHTML = "";

    ranking.forEach((r, index) => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${r.other}</td>
            <td>${r.winrate.toFixed(1)}%</td>
            <td>${r.matches}</td>
        `;

        row.style.cursor = "pointer";

		row.onclick = () => {
		
			window.location.href =
				`player.html?player=${encodeURIComponent(r.other)}`;
		
		};

        tbody.appendChild(row);

    });

}

function computeWinsNeeded(myRelation, currentNemesisRelation) {

    if (!currentNemesisRelation)
        return "-";

    // déjà nemesis
    if (myRelation.other === currentNemesisRelation.player)
        return 0;

    const targetWR =
        currentNemesisRelation.wins /
        currentNemesisRelation.matches;

    for (let extraWins = 1; extraWins <= 100; extraWins++) {

        const newWins =
            myRelation.wins + extraWins;

        const newMatches =
            myRelation.matches + extraWins;

		const left =
			newWins * currentNemesisRelation.matches;
	
		const right =
			currentNemesisRelation.wins * newMatches;

		if (left > right)
			return extraWins;

		if (
			left === right &&
			newMatches > currentNemesisRelation.matches
		)
			return extraWins;
			}

//        const newWR =
//            newWins / newMatches;
//
//        // meilleur ratio
//        if (newWR > targetWR)
//            return extraWins;
//
//        // égalité -> plus de matchs gagne
//        if (
//            newWR === targetWR &&
//            newMatches > currentNemesisRelation.matches
//        )
//            return extraWins;
//    }

    return "-";
}

function renderNemesisTargets(profile) {

    // cacher le tableau ranking
    document.querySelector(".ranking-table").style.display = "none";

    // afficher le tableau target
    document.getElementById("targetTable").style.display = "table";

    document.getElementById("tableTitle").textContent =
        "🎯 Nemesis Targets";

    const tbody = document.getElementById("targetBody");
    tbody.innerHTML = "";

    // tous les adversaires avec au moins 5 matchs
	const opponents = relations
		.filter(r =>
			r.player === profile.player &&
			r.type === "opponent" &&
			r.matches >= 5
		)
		.map(r => {
	
			//-----------------------------------
			// Nemesis actuelle de cet adversaire
			//-----------------------------------
	
			const ranking = relations
				.filter(x =>
					x.player === r.other &&
					x.type === "opponent" &&
					x.matches >= 5
				)
				.sort((a,b) => {
	
					if (a.winrate !== b.winrate) {
						return a.winrate - b.winrate;
					}
	
					return b.matches - a.matches;
	
				});
	
			const currentNemesis = ranking[0];
	
			const reverseRelation = currentNemesis
				? relations.find(x =>
					x.player === currentNemesis.other &&
					x.other === currentNemesis.player &&
					x.type === "opponent"
				)
				: null;
	
	
			const validated =
				currentNemesis &&
				currentNemesis.other === profile.player;
	
	
			const winsNeeded =
				validated
					? 0
					: computeWinsNeeded(r, reverseRelation);
	
	
			return {
				relation: r,
				currentNemesis,
				reverseRelation,
				validated,
				winsNeeded
			};
	
		})
		.sort((a,b) => {
		
			if (a.winsNeeded === "-" && b.winsNeeded !== "-")
				return 1;
		
			if (b.winsNeeded === "-" && a.winsNeeded !== "-")
				return -1;
		
			if (a.winsNeeded !== b.winsNeeded)
				return a.winsNeeded - b.winsNeeded;
		
			return b.relation.winrate - a.relation.winrate;
		
		});
	

	opponents.forEach(item => {
	
		const r = item.relation;
	
		const currentNemesis = item.currentNemesis;
		const reverseRelation = item.reverseRelation;
		const validated = item.validated;
		const winsNeeded = item.winsNeeded;

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${r.other}</td>
            <td>${r.wins}/${r.matches}</td>
            <td>${r.winrate.toFixed(1)}%</td>
			<td>${validated ? "-" : (currentNemesis ? currentNemesis.other : "-")}</td>
			
			<td>${validated ? "-" :
				(reverseRelation
					? `${reverseRelation.wins}/${reverseRelation.matches}`
					: "-")
			}</td>
			
			<td>${validated ? "-" :
				(reverseRelation
					? reverseRelation.winrate.toFixed(1)+"%"
					: "-")
			}</td>
			<td>${validated ? "✅" : "🎯"}</td>
            <td>${winsNeeded}</td>
        `;

        row.style.cursor = "pointer";

        row.onclick = () => {

            window.location.href =
                `player.html?player=${encodeURIComponent(r.other)}`;

        };

        tbody.appendChild(row);

    });

}
