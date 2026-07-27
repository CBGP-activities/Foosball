// =====================================================
// Foosball Rankings
// app.js
// =====================================================

let ranking = [];
let history = [];
let recentMatches = [];
let playerStats = [];

const COLORS = [
    "#e63946",
    "#457b9d",
    "#2a9d8f",
    "#f4a261",
    "#6a4c93",
    "#118ab2",
    "#ef476f",
    "#8ac926",
    "#ff9f1c",
    "#3a86ff",
    "#8338ec",
    "#ff006e"
];

window.addEventListener("DOMContentLoaded", async () => {

    await loadData();

    // updateHeader();
    renderRanking();
    renderRecentMatches();
    drawHistoryChart();

});

// =====================================================
// Chargement JSON
// =====================================================

async function loadData() {

    console.log("ranking");
    ranking = await fetchJSON("results/current_ranking.json");

    console.log("history");
    history = await fetchJSON("results/ranking_history.json");

    console.log("recent");
    recentMatches = await fetchJSON("results/recent_matches.json");

    console.log("stats");
    playerStats = await fetchJSON("results/player_stats.json");

}

async function fetchJSON(path) {

    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(path);
    }

    return response.json();

}

// =====================================================
// Header
// =====================================================

function updateHeader() {

    document.getElementById("playerCount").textContent =
        ranking.length;

    const totalMatches =
        ranking.reduce(
            (sum, p) => sum + p.matches,
            0
        ) / 4;

    document.getElementById("matchCount").textContent =
        Math.round(totalMatches);

}

// =====================================================
// Classement
// =====================================================

function renderRanking() {

    const tbody = document.getElementById("rankingBody");

    tbody.innerHTML = "";

    ranking.forEach((row, i) => {

        const tr = document.createElement("tr");

        if(i===0) tr.classList.add("top1");
        if(i===1) tr.classList.add("top2");
        if(i===2) tr.classList.add("top3");

        tr.innerHTML = `
            <td>${row.rank}</td>
            <td>${row.player}</td>
			<td>${Number(row.score).toFixed(2)}</td>
			<td>${Number(row.mu).toFixed(2)}</td>
			<td>${Number(row.sigma).toFixed(2)}</td>
            <td>${row.matches}</td>
        `;
        
		tr.style.cursor = "pointer";
		
		tr.addEventListener("click", () => {
			window.location.href =
				`player.html?player=${encodeURIComponent(row.player)}`;
		});
		
        tbody.appendChild(tr);

    });

}

// =====================================================
// Matchs récents
// =====================================================

function renderRecentMatches() {

    const tbody = document.getElementById("recentMatches");
    tbody.innerHTML = "";

    recentMatches
        .slice()
        .reverse()
        .forEach(match => {

            const tr = document.createElement("tr");

            const redWinner = match.winner === "red";
            const blueWinner = match.winner === "blue";

            tr.innerHTML = `
                <td class="match-date">
                    ${formatDate(match.date)}
                </td>

                <td class="${redWinner ? "winner" : ""}">
                    🔴 ${match.team_red.join(" / ")}
                </td>

                <td class="${blueWinner ? "winner" : ""}">
                    🔵 ${match.team_blue.join(" / ")}
                </td>
            `;

            tbody.appendChild(tr);

        });

}

// =======================
// VARIABLES
// =======================
let chart = null;
let fullDatasets = [];
let allMatchDates = [];
let xMode = "category";
let currentRange = "all";

// =======================
function colorForIndex(i,total){
    return `hsl(${Math.round(360*i/total)},70%,45%)`;
}

function drawHistoryChart(){

    const classementOrder =
        ranking.map(r => r.player);

    drawAllPlayersChart(
        history,
        classementOrder
    );

}

// =====================================================
// Graphique évolution
// =====================================================

function drawAllPlayersChart(historique, classementOrder){

    const joueurs = classementOrder.filter(j =>
        historique.some(d=>d.player===j)
    );

    allMatchDates = [...new Set(historique.map(d=>d.date))].sort();

    const datasets = joueurs.map((joueur,index)=>{
        const color = colorForIndex(index,joueurs.length);
        const rows = historique.filter(d=>d.player===joueur);

        const lastPerDay = {};
        rows.forEach(r=>lastPerDay[r.date]=r);

        const timeData = Object.values(lastPerDay)
            .sort((a,b)=>a.date.localeCompare(b.date))
            .map(d=>{
                const date = new Date(d.date);
				date.setHours(23,59,0,0);
				
				return {
					x: date,
					y: parseFloat(d.score)
				};
            });

        return {
            label: joueur,
            borderColor: color,
            backgroundColor: color,
            borderWidth: 1.5,
            tension: 0.3,
            fill:false,
            pointRadius:1,
            pointHoverRadius:6,
            timeData,
            data: timeData
        };
    });

    fullDatasets = datasets.map(ds=>({
        ...ds,
        timeData:[...ds.timeData]
    }));

    chart = new Chart(document.getElementById("allPlayersChart"), {
        type:"line",
        data:{datasets},
        options:getChartOptions()
    });

    setRange("all");
}

// =======================
function getChartOptions(){
    return {
        responsive:true,
        interaction:{mode:"nearest",intersect:false},
        plugins:{
            legend:{position:"right", labels:{color:"#222", boxWidth:14, usePointStyle:true, pointStyle:"circle"} },
            tooltip:{
                callbacks:{
                    label: ctx =>
                        `${ctx.dataset.label} : ${ctx.parsed.y.toFixed(2)}`
                }
            }
        },
        scales:{
            x:{ type:"time", time:{unit:"day"}, title:{display:true,text:"Date"}, ticks:{color:"#444"}, grid:{color:"#ddd"} },
            y:{ title:{display:true,text:"Score"}, ticks:{color:"#444"}, grid:{color:"#ddd"} }
        }

    };
}

// =======================
function toggleXAxis(){
    xMode = xMode==="time" ? "category" : "time";
    setRange(currentRange);
}

// =======================
// FILTRES
// =======================
function setRange(type){
    currentRange = type;
    const now = new Date();
    let start = null;

    if(type==="week"){
        start = new Date();
        start.setDate(now.getDate()-7);
    } else if(type==="year"){
        start = new Date(now.getFullYear(),0,1);
    }

    applyRange(start, now);
}

function setCustomRange(){
    const f = document.getElementById("fromDate").value;
    const t = document.getElementById("toDate").value;
    if(!f || !t) return;

    const start = new Date(f);
    const end = new Date(t);
    end.setHours(23,59,59,999); // ⬅️ inclure toute la journée

    currentRange = "custom";
    applyRange(start, end);
}

function applyRange(startDate, endDate){

    let visibleDates = [];

    chart.data.datasets.forEach((ds,i)=>{
        const filtered = fullDatasets[i].timeData.filter(p=>{
            if(startDate && p.x < startDate) return false;
            if(endDate && p.x > endDate) return false;
            return true;
        });

        filtered.forEach(p=>{
            visibleDates.push(p.x.toISOString().split("T")[0]);
        });

        if(xMode==="time"){
            ds.data = filtered;
        } else {
            const byDate = {};
            filtered.forEach(p=>{
                byDate[p.x.toISOString().split("T")[0]] = p.y;
            });

            ds.data = [...new Set(visibleDates)]
                .sort()
                .map(d=>({x:d,y:byDate[d] ?? null}));
        }
    });

    chart.options.scales.x = xMode==="time"
        ? {type:"time",time:{unit:"day"},title:{display:true,text:"Date"}}
        : {type:"category",labels:[...new Set(visibleDates)].sort(),title:{display:true,text:"Match days"}};

    chart.update();
}


// =====================================================
// Helpers
// =====================================================

function formatDate(dateString) {

    return new Date(dateString)
        .toLocaleDateString(
            "fr-FR"
        );

}
