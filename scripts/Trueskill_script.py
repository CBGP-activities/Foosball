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
MIN_MATCHS_RELATION = 5

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

df_stats["joueur"] = (
    df_stats["joueur"]
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

        "premier_match":
            matches_joueur["date"].min().date(),

        "dernier_match":
            matches_joueur["date"].max().date(),

        "jours_depuis_dernier_match":
            (
                df["date"].max()
                - matches_joueur["date"].max()
            ).days

    }

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
            stats_dates[joueur]["premier_match"],

        "dernier_match":
            stats_dates[joueur]["dernier_match"],

        "jours_depuis_dernier_match":
            stats_dates[joueur]["jours_depuis_dernier_match"],
        
        "taux_victoire_all_time":
            taux_victoire(
                resultats_joueurs[joueur]
            ),


        "taux_victoire_30j":
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


        "pire_ennemi":
            detail_pire_ennemi(joueur),


        "meilleur_coequipier":
            detail_coequipier(joueur),


        "plus_longue_serie_victoires":
            serie_max(
                resultats_joueurs[joueur],
                "V"
            ),


        "plus_longue_serie_defaites":
            serie_max(
                resultats_joueurs[joueur],
                "D"
            ),


        "score_trueskill_max":
            df_j["score"].max(),
        
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

# =====================
# MATRICES RELATIONS
# =====================


joueurs = sorted(ratings.keys())


# ---------------------
# COEQUIPIERS
# ---------------------

matrice_coequipiers = []


for joueur in joueurs:

    ligne = {
        "joueur": joueur
    }

    for autre in joueurs:

        stats = relations[(joueur, autre)]

        if stats["ensemble_matchs"] >= MIN_MATCHS_RELATION:

            ligne[autre] = (
                f"{stats['ensemble_victoires']}/"
                f"{stats['ensemble_matchs']} "
                f"({round(100 * stats['ensemble_victoires'] / stats['ensemble_matchs'], 1)}%)"
            )    

        else:

            ligne[autre] = None


    matrice_coequipiers.append(ligne)



df_coequipiers = pd.DataFrame(
    matrice_coequipiers
)


df_coequipiers.to_csv(
    OUTPUT_DIR / "stats_coequipiers.csv",
    index=False
)



# ---------------------
# ADVERSAIRES
# ---------------------

matrice_adversaires = []


for joueur in joueurs:

    ligne = {
        "joueur": joueur
    }


    for autre in joueurs:

        stats = relations[(joueur, autre)]


        if stats["contre_matchs"] >= MIN_MATCHS_RELATION:

            # taux de victoire de joueur contre autre

            ligne[autre] = (
                f"{stats['contre_victoires']}/"
                f"{stats['contre_matchs']} "
                f"({round(100 * stats['contre_victoires'] / stats['contre_matchs'], 1)}%)"
            )

        else:

            ligne[autre] = None


    matrice_adversaires.append(ligne)



df_adversaires = pd.DataFrame(
    matrice_adversaires
)


df_adversaires.to_csv(
    OUTPUT_DIR / "stats_adversaires.csv",
    index=False
)


print("🤝 Matrices coéquipiers/adversaires générées")

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
