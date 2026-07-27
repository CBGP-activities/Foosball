import os
import pandas as pd
from trueskill import Rating, rate
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import json
from supabase import create_client

# =====================
# PARAMÈTRES
# =====================
USE_SUPABASE = True
INPUT_EXCEL = Path("data/matchs.xlsx")
SHEET_NAME = "matchs"
if USE_SUPABASE:
	SUPABASE_URL = os.environ["SUPABASE_URL"]
	SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

OUTPUT_DIR = Path("docs/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MU0 = 25
SIGMA0 = MU0 / 3

# critères d'affichage du classement
MIN_MATCHS_CLASSEMENT = 10
MOIS_ACTIVITE_CLASSEMENT = 6
MIN_MATCHS_RELATION = 5
STATS_SEULEMENT_JOUEURS_ACTIFS = False

# =====================
# EXPORT CSV + JSON
# =====================

def export_data(df, filename):

    df.to_csv(
        OUTPUT_DIR / f"{filename}.csv",
        index=False
    )

    with open(
        OUTPUT_DIR / f"{filename}.json",
        "w",
        encoding="utf-8"
    ) as f:

        clean_df = df.where(pd.notnull(df), None)
        json.dump(
			clean_df.to_dict(orient="records"),
			f,
			ensure_ascii=False,
			indent=2,
			default=str
		)
        
# =====================
# LECTURE DES MATCHS
# =====================
def load_matches():

    if USE_SUPABASE:

        print("Lecture des matchs depuis Supabase...")

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        response = (
            supabase
            .table("matches")
            .select("*")
            .order("id")
            .execute()
        )

        df = pd.DataFrame(response.data)

        df = df[[
			"id",
            "date",
            "rouge_p1",
            "rouge_p2",
            "bleu_p1",
            "bleu_p2",
            "vainqueur"
        ]]

        return df

    else:

        print("Lecture des matchs depuis Excel...")

        return pd.read_excel(
            INPUT_EXCEL,
            sheet_name=SHEET_NAME
        )

def export_excel_backup(df):

    backup_path = Path("data/matchs.xlsx")

    backup_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_excel(
        backup_path,
        index=False,
        sheet_name="matchs"
    )

    print(
        "💾 Backup Excel créé :",
        backup_path
    )
	
df = load_matches()
if USE_SUPABASE:
    export_excel_backup(df)
	
# =====================
# NETTOYAGE DES NOMS JOUEURS
# =====================
colonnes_joueurs = [
    "rouge_p1",
    "rouge_p2",
    "bleu_p1",
    "bleu_p2"
]


for col in colonnes_joueurs:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


df["date"] = pd.to_datetime(df["date"])

df = (
    df
    .sort_values("id")
    .reset_index(drop=True)
)


def export_players(df):

    players = sorted(
        pd.concat(
            [df[col] for col in colonnes_joueurs]
        )
        .dropna()
        .unique()
        .tolist()
    )

    with open(
        OUTPUT_DIR / "players.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            players,
            f,
            ensure_ascii=False,
            indent=2
        )

export_players(df)

# =====================
# STRUCTURES
# =====================
ratings = {}
nb_matchs = defaultdict(int)
historique = []
resultats_joueurs = defaultdict(list)

relations = defaultdict(
    lambda: {
        "ensemble_matchs": 0,
        "ensemble_victoires": 0,
        "contre_matchs": 0,
        "contre_victoires": 0
    }
)

def get_rating(joueur):

    if joueur not in ratings:
        ratings[joueur] = Rating(
            mu=MU0,
            sigma=SIGMA0
        )

    return ratings[joueur]



# =====================
# TRAITEMENT MATCH PAR MATCH
# =====================
for match_id, row in df.iterrows():

    date = row["date"]


    t1_players = [
        row["rouge_p1"],
        row["rouge_p2"]
    ]

    t2_players = [
        row["bleu_p1"],
        row["bleu_p2"]
    ]


    rouge = [
        get_rating(p)
        for p in t1_players
    ]

    bleu = [
        get_rating(p)
        for p in t2_players
    ]


    if row["vainqueur"] == "rouge":
        ranks = [0, 1]
    else:
        ranks = [1, 0]


    new_teams = rate(
        [rouge, bleu],
        ranks=ranks
    )
    
    # =====================
    # ENREGISTREMENT STATS MATCH
    # =====================

    rouge_gagne = row["vainqueur"] == "rouge"

    # =====================
    # ENREGISTREMENT RELATIONS
    # =====================

    # rouge avec bleu comme adversaires
    for joueur in t1_players:
    
        for coeq in t1_players:
    
            if joueur != coeq:
                relations[(joueur, coeq)]["ensemble_matchs"] += 1

                if rouge_gagne:
                    relations[(joueur, coeq)]["ensemble_victoires"] += 1


        for adv in t2_players:

            relations[(joueur, adv)]["contre_matchs"] += 1

            if rouge_gagne:
                relations[(joueur, adv)]["contre_victoires"] += 1



    # bleu avec rouge comme adversaires
    for joueur in t2_players:

        for coeq in t2_players:

            if joueur != coeq:
                relations[(joueur, coeq)]["ensemble_matchs"] += 1

                if not rouge_gagne:
                    relations[(joueur, coeq)]["ensemble_victoires"] += 1


        for adv in t1_players:

            relations[(joueur, adv)]["contre_matchs"] += 1

            if not rouge_gagne:    
                relations[(joueur, adv)]["contre_victoires"] += 1


    for joueur in t1_players:

        resultats_joueurs[joueur].append({

            "date": date,
            "resultat": "V" if rouge_gagne else "D",
            "coequipiers": [
                p for p in t1_players
                if p != joueur
            ],
            "adversaires": t2_players

        })


    for joueur in t2_players:

        resultats_joueurs[joueur].append({

            "date": date,
            "resultat": "D" if rouge_gagne else "V",
            "coequipiers": [
                p for p in t2_players
                if p != joueur
            ],
            "adversaires": t1_players

        })

    # mise à jour ratings
    for p, r in zip(t1_players, new_teams[0]):

        ratings[p] = r
        nb_matchs[p] += 1


    for p, r in zip(t2_players, new_teams[1]):

        ratings[p] = r
        nb_matchs[p] += 1



    # historique complet
    for joueur, rating in ratings.items():

        historique.append({

            "date": date,
            "match_id": match_id + 1,
            "player": joueur,
            "mu": rating.mu,
            "sigma": rating.sigma,
            "score": rating.mu - 3 * rating.sigma

        })



# =====================
# JOUEURS ÉLIGIBLES
# =====================

date_limite = (
    df["date"].max()
    -
    pd.DateOffset(
        months=MOIS_ACTIVITE_CLASSEMENT
    )
)


joueurs_actifs = set(

    df[
        df["date"] >= date_limite
    ][
        colonnes_joueurs
    ]
    .values
    .flatten()

)

joueurs_actifs = {
    str(joueur).strip()
    for joueur in joueurs_actifs
}


joueurs_eligibles = {

    joueur

    for joueur in ratings.keys()

    if nb_matchs[joueur] >= MIN_MATCHS_CLASSEMENT
    and joueur in joueurs_actifs

}



# =====================
# GRAPHIQUE ÉVOLUTION
# =====================

df_histo = pd.DataFrame(historique)

df_histo["date"] = pd.to_datetime(
    df_histo["date"]
)

df_histo["player"] = (
    df_histo["player"]
    .str.strip()
)



df_histo = df_histo[
    df_histo["player"]
    .isin(joueurs_eligibles)
]



plt.figure(figsize=(12, 6))


for joueur, df_j in df_histo.groupby("player"):


    df_last = (
        df_j
        .sort_values("date")
        .groupby(
            df_j["date"].dt.date,
            as_index=False
        )
        .last()
    )


    plt.plot(
        df_last["date"],
        df_last["score"],
        linewidth=1.5,
        alpha=0.8,
        label=joueur
    )


    plt.scatter(
        df_last["date"],
        df_last["score"],
        s=25
    )



plt.title(
    "Évolution des scores TrueSkill (μ − 3σ)"
)

plt.xlabel("Date")
plt.ylabel("Score")

plt.grid(
    True,
    alpha=0.3
)

plt.legend(
    ncol=2,
    fontsize=9
)

plt.tight_layout()


plt.savefig(
    OUTPUT_DIR / "score_evolution.png",
    dpi=150
)


plt.close()


# =====================
# CLASSEMENT FINAL
# =====================

classement = []


for joueur, rating in ratings.items():

    if joueur in joueurs_eligibles:

        classement.append({

            "player": joueur,
            "mu": rating.mu,
            "sigma": rating.sigma,
            "score": rating.mu - 3 * rating.sigma,
            "matches": nb_matchs[joueur]

        })


df_classement = pd.DataFrame(classement)


df_classement = (
    df_classement
    .sort_values(
        "score",
        ascending=False
    )
)


df_classement.insert(
    0,
    "rank",
    range(
        1,
        len(df_classement)+1
    )
)



# =====================
# STATISTIQUES JOUEURS
# =====================

def taux_victoire(matchs):

    if len(matchs) == 0:
        return 0

    return (
        sum(m["resultat"] == "V" for m in matchs)
        /
        len(matchs)
    )



def serie_max(matchs, resultat):

    max_serie = 0
    serie = 0

    for m in matchs:

        if m["resultat"] == resultat:
            serie += 1
            max_serie = max(max_serie, serie)

        else:
            serie = 0

    return max_serie



def pire_ennemi(joueur):

    stats = defaultdict(
        lambda: {"D": 0, "total": 0}
    )

    for match in resultats_joueurs[joueur]:

        for adv in match["adversaires"]:

            stats[adv]["total"] += 1

            if match["resultat"] == "D":
                stats[adv]["D"] += 1

    stats_filtrees = {
        adv: valeurs
        for adv, valeurs in stats.items()
        if valeurs["total"] >= MIN_MATCHS_RELATION
    }

    if not stats_filtrees:
        return None

    return max(
        stats_filtrees,
        key=lambda x: (
            stats_filtrees[x]["D"] / stats_filtrees[x]["total"],
            stats_filtrees[x]["total"]
        )
    )

def meilleur_coequipier(joueur):

    stats = defaultdict(
        lambda: {"V":0,"total":0}
    )


    for match in resultats_joueurs[joueur]:

        for coeq in match["coequipiers"]:

            stats[coeq]["total"] += 1

            if match["resultat"] == "V":
                stats[coeq]["V"] += 1

    stats_filtrees = {
        coeq: valeurs
        for coeq, valeurs in stats.items()
        if valeurs["total"] >= MIN_MATCHS_RELATION
    }

    if not stats_filtrees:
        return None

    return max(
        stats_filtrees,
        key=lambda x: (
            stats_filtrees[x]["V"] / stats_filtrees[x]["total"],
            stats_filtrees[x]["total"]
        )
    ) 

# =====================
# FORMATAGE RELATIONS
# =====================

def detail_coequipier(joueur):

    candidat = meilleur_coequipier(joueur)

    if candidat is None:
        return None

    stats = relations[(joueur, candidat)]

    return (
        f"{candidat} "
        f"({stats['ensemble_victoires']}/"
        f"{stats['ensemble_matchs']} "
        f"{round(100 * stats['ensemble_victoires'] / stats['ensemble_matchs'],1)}%)"
    )



def detail_pire_ennemi(joueur):

    candidat = pire_ennemi(joueur)

    if candidat is None:
        return None

    stats = relations[(joueur, candidat)]

    return (
        f"{candidat} "
        f"({stats['contre_matchs'] - stats['contre_victoires']}/"
        f"{stats['contre_matchs']} "
        f"{round(100 * (stats['contre_matchs'] - stats['contre_victoires']) / stats['contre_matchs'],1)}%)"
    )


df_stats = pd.DataFrame(historique)

df_stats["date"] = pd.to_datetime(
    df_stats["date"]
)

df_stats["player"] = (
    df_stats["player"]
    .str.strip()
)


stats_dates = {}

for joueur in ratings.keys():

    matches_joueur = df[
        (df["rouge_p1"] == joueur)
        | (df["rouge_p2"] == joueur)
        | (df["bleu_p1"] == joueur)
        | (df["bleu_p2"] == joueur)
    ]

    stats_dates[joueur] = {

        "first_match":
           matches_joueur["date"].min().strftime("%Y-%m-%d"),

        "last_match":
            matches_joueur["date"].max().strftime("%Y-%m-%d"),

        "days_since_last_match":
            (
                df["date"].max()
                - matches_joueur["date"].max()
            ).days

    }

stats_joueurs = []


for joueur, df_j in df_stats.groupby("player"):

    stats_joueurs.append({

        "player": joueur,

        "matches": nb_matchs[joueur],

        "mu": (
            ratings[joueur].mu
            if joueur in ratings
            else None
        ),

        "sigma": (
            ratings[joueur].sigma
            if joueur in ratings
            else None
        ),

        "score": (
            ratings[joueur].mu
            -
            3 * ratings[joueur].sigma
            if joueur in ratings
            else None
        ),

        
        "first_match":
            stats_dates[joueur]["first_match"],

        "last_match":
            stats_dates[joueur]["last_match"],

        "days_since_last_match":
            stats_dates[joueur]["days_since_last_match"],
        
        "winrate_all_time":
            taux_victoire(
                resultats_joueurs[joueur]
            ),


        "winrate_last_30_days":
            taux_victoire(
                [
                    m
                    for m in resultats_joueurs[joueur]
                    if m["date"] >= (
                        df["date"].max()
                        -
                        pd.Timedelta(days=30)
                    )
                ]
            ),


        "worst_enemy":
            detail_pire_ennemi(joueur),


        "best_teammate":
            detail_coequipier(joueur),


        "longest_win_streak":
            serie_max(
                resultats_joueurs[joueur],
                "V"
            ),


        "longest_loss_streak":
            serie_max(
                resultats_joueurs[joueur],
                "D"
            ),


        "highest_trueskill_score":
            df_j["score"].max(),
        
        "ranking_eligible":
            joueur in joueurs_eligibles

    })


df_stats_joueurs = pd.DataFrame(
    stats_joueurs
)


df_stats_joueurs = (
    df_stats_joueurs
    .sort_values(
        "score",
        ascending=False
    )
)

rangs = (
    df_classement
    .set_index("player")["rank"]
    .to_dict()
)

df_stats_joueurs["rank"] = (
    df_stats_joueurs["player"]
    .map(rangs)
)

df_stats_joueurs_clean = (
    df_stats_joueurs
    .astype(object)
    .where(pd.notnull(df_stats_joueurs), None)
)
export_data(
    df_stats_joueurs_clean,
    "player_stats"
)


relations_export = []

for (joueur, autre), stats in relations.items():

    # Coéquipiers
    if stats["ensemble_matchs"] >= MIN_MATCHS_RELATION:

        relations_export.append({

            "player": joueur,

            "other": autre,

            "type": "teammate",

            "matches": stats["ensemble_matchs"],

            "wins": stats["ensemble_victoires"],

            "losses": (
                stats["ensemble_matchs"]
                - stats["ensemble_victoires"]
            ),

            "winrate": round(
                100
                * stats["ensemble_victoires"]
                / stats["ensemble_matchs"],
                1
            )

        })

    # Adversaires
    if stats["contre_matchs"] >= MIN_MATCHS_RELATION:

        relations_export.append({

            "player": joueur,

            "other": autre,

            "type": "opponent",

            "matches": stats["contre_matchs"],

            "wins": stats["contre_victoires"],

            "losses": (
                stats["contre_matchs"]
                - stats["contre_victoires"]
            ),

            "winrate": round(
                100
                * stats["contre_victoires"]
                / stats["contre_matchs"],
                1
            )

        })

df_relations = pd.DataFrame(relations_export)

export_data(
    df_relations,
    "player_relations"
)


print(
    "📊 Statistiques joueurs générées"
)



# =====================
# EXPORT JSON+CSV
# =====================

export_data(
    df_classement,
    "current_ranking"
)



df_historique_export = pd.DataFrame(
    historique
)


df_historique_export = (
    df_historique_export[
        df_historique_export["player"]
        .isin(joueurs_eligibles)
    ]
)


export_data(
    df_historique_export,
    "ranking_history"
)

# =====================
# EXPORT PROFILS JOUEURS
# =====================

profiles = []


for joueur in ratings.keys():

    historique_joueur = (
		df_historique_export[
			df_historique_export["player"] == joueur
		]
		[
			[
				"date",
				"score"
			]
		]
		.assign(
			date=lambda x: x["date"].dt.strftime("%Y-%m-%d")
		)
		.to_dict(
			orient="records"
		)
	)


    relations_joueur = (
        df_relations[
            df_relations["player"] == joueur
        ]
        .to_dict(
            orient="records"
        )
    )


    stats_joueur = (
		df_stats_joueurs
			.loc[df_stats_joueurs["player"] == joueur]
			.replace({pd.NA: None, float("nan"): None})
			.iloc[0]
			.to_dict()
	)


    profiles.append({

        "player": joueur,

        "stats": stats_joueur,

        "history": historique_joueur,

        "relations": relations_joueur

    })


df_profiles = pd.DataFrame(profiles)

with open(
    OUTPUT_DIR / "player_profiles.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        profiles,
        f,
        ensure_ascii=False,
        indent=2,
        default=str
    )

df_profiles.to_csv(
    OUTPUT_DIR / "player_profiles.csv",
    index=False
)


# =====================
# RECENT MATCHES EXPORT
# =====================

recent_matches = (
    df
    .tail(20)
    .apply(
        lambda row: {

            "date": row["date"],

            "team_red": [
                row["rouge_p1"],
                row["rouge_p2"]
            ],

            "team_blue": [
                row["bleu_p1"],
                row["bleu_p2"]
            ],

            "winner": "red" if row["vainqueur"] == "rouge" else "blue"

        },
        axis=1
    )
    .tolist()
)


df_recent_matches = pd.DataFrame(
    recent_matches
)

export_data(
    df_recent_matches,
    "recent_matches"
)
