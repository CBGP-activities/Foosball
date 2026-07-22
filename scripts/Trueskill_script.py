import pandas as pd
from trueskill import Rating, rate
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt


# =====================
# PARAMÈTRES
# =====================
INPUT_EXCEL = Path("data/matchs.xlsx")
OUTPUT_DIR = Path("docs/resultats")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SHEET_NAME = "matchs"

MU0 = 25
SIGMA0 = MU0 / 3

# critères d'affichage du classement
MIN_MATCHS_CLASSEMENT = 10
MOIS_ACTIVITE_CLASSEMENT = 6


# =====================
# LECTURE DES MATCHS
# =====================
df = pd.read_excel(
    INPUT_EXCEL,
    sheet_name=SHEET_NAME
)


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
    .sort_values("date")
    .reset_index(drop=True)
)



# =====================
# STRUCTURES
# =====================
ratings = {}
nb_matchs = defaultdict(int)
historique = []


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
            "joueur": joueur,
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

df_histo["joueur"] = (
    df_histo["joueur"]
    .str.strip()
)



df_histo = df_histo[
    df_histo["joueur"]
    .isin(joueurs_eligibles)
]



plt.figure(figsize=(12, 6))


for joueur, df_j in df_histo.groupby("joueur"):


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
    OUTPUT_DIR / "evolution_scores.png",
    dpi=150
)


plt.close()


print(
    "📈 Graphe évolution généré : resultats/evolution_scores.png"
)



# =====================
# CLASSEMENT FINAL
# =====================

classement = []


for joueur, rating in ratings.items():

    if joueur in joueurs_eligibles:

        classement.append({

            "joueur": joueur,
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
    "rang",
    range(
        1,
        len(df_classement)+1
    )
)



# =====================
# STATISTIQUES JOUEURS
# =====================

df_stats = pd.DataFrame(historique)

df_stats["date"] = pd.to_datetime(
    df_stats["date"]
)

df_stats["joueur"] = (
    df_stats["joueur"]
    .str.strip()
)


stats_joueurs = []


for joueur, df_j in df_stats.groupby("joueur"):

    stats_joueurs.append({

        "joueur": joueur,

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

        "premier_match":
            pd.to_datetime(df_j["date"].min()).date(),

        "dernier_match":
            pd.to_datetime(df_j["date"].max()).date(),
        
        "jours_depuis_dernier_match":
            (
                df["date"].max()
                -
                df_j["date"].max()
            ).days,

        "eligible_classement":
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


df_stats_joueurs.to_csv(
    OUTPUT_DIR / "players_statistiques.csv",
    index=False
)


print(
    "📊 Statistiques joueurs générées"
)



# =====================
# EXPORT CSV
# =====================

df_classement.to_csv(
    OUTPUT_DIR / "classement_actuel.csv",
    index=False
)



df_historique_export = pd.DataFrame(
    historique
)


df_historique_export = (
    df_historique_export[
        df_historique_export["joueur"]
        .isin(joueurs_eligibles)
    ]
)


df_historique_export.to_csv(
    OUTPUT_DIR / "historique_classement.csv",
    index=False
)



print("✅ Classement généré")
print(" - resultats/classement_actuel.csv")
print(" - resultats/historique_classement.csv")
print(" - resultats/players_statistiques.csv")
