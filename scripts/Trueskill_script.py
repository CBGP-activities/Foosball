import pandas as pd
from trueskill import Rating, rate
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# =====================
# PARAMÈTRES
# =====================
INPUT_EXCEL = Path("data/matchs.xlsx")
OUTPUT_DIR = Path("docs/resultats")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MU0 = 25
SIGMA0 = MU0 / 3

# =====================
# LECTURE DES MATCHS
# =====================
df = pd.read_excel(INPUT_EXCEL, sheet_name=SHEET_NAME)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

# =====================
# STRUCTURES
# =====================
ratings = {}
nb_matchs = defaultdict(int)
historique = []

def get_rating(joueur):
    if joueur not in ratings:
        ratings[joueur] = Rating(mu=MU0, sigma=SIGMA0)
    return ratings[joueur]

# =====================
# TRAITEMENT MATCH PAR MATCH
# =====================
for match_id, row in df.iterrows():
    date = row["date"]

    t1_players = [row["rouge_p1"], row["rouge_p2"]]
    t2_players = [row["bleu_p1"], row["bleu_p2"]]

    rouge = [get_rating(p) for p in t1_players]
    bleu = [get_rating(p) for p in t2_players]

    if row["vainqueur"] == "rouge":
        ranks = [0, 1]
    else:
        ranks = [1, 0]

    new_teams = rate([rouge, bleu], ranks=ranks)

    # mise à jour des ratings
    for p, r in zip(t1_players, new_teams[0]):
        ratings[p] = r
        nb_matchs[p] += 1

    for p, r in zip(t2_players, new_teams[1]):
        ratings[p] = r
        nb_matchs[p] += 1

    # snapshot historique
    for joueur, rating in ratings.items():
        historique.append({
            "date": date,
            "match_id": match_id + 1,
            "joueur": joueur,
            "mu": rating.mu,
            "sigma": rating.sigma,
            "score": rating.mu - 3 * rating.sigma
        })

## =====================
## Graphique historique
## =====================
#
## Convertir l'historique en DataFrame
#df_histo = pd.DataFrame(historique)
#df_histo['date'] = pd.to_datetime(df_histo['date'])
#
## Liste des joueurs uniques
#joueurs = df_histo['joueur'].str.strip().unique()
#
## Création du graphique
#plt.figure(figsize=(12,6))
#
#for joueur in joueurs:
#    df_j = df_histo[df_histo['joueur'].str.strip() == joueur].sort_values('date')
#    plt.plot(df_j['date'], df_j['score'], label=joueur, linewidth=1.5)
#
#plt.title("Évolution des scores TrueSkill (μ − 3σ)")
#plt.xlabel("Date")
#plt.ylabel("Score")
#plt.legend()
#plt.grid(True)
#plt.tight_layout()
#
## Formater les dates sur l'axe X
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#plt.gcf().autofmt_xdate()
#
## Sauvegarder le graphe
#plt.savefig(OUTPUT_DIR / "evolution_scores.png", dpi=150)
#plt.close()
#
#print("✅ Graphe évolution généré : resultats/evolution_scores.png")

# =====================
# GRAPHIQUE ÉVOLUTION (1 point / jour / joueur)
# =====================
df_histo = pd.DataFrame(historique)
df_histo["date"] = pd.to_datetime(df_histo["date"])
df_histo["joueur"] = df_histo["joueur"].str.strip()

plt.figure(figsize=(12, 6))

for joueur, df_j in df_histo.groupby("joueur"):

    # garder le dernier score par jour (ordre du CSV conservé)
    df_last = (
        df_j
        .sort_values("date")
        .groupby(df_j["date"].dt.date, as_index=False)
        .last()
    )

    # courbe
    plt.plot(
        df_last["date"],
        df_last["score"],
        linewidth=1.5,
        alpha=0.8,
        label=joueur
    )

    # points
    plt.scatter(
        df_last["date"],
        df_last["score"],
        s=25
    )

plt.title("Évolution des scores TrueSkill (μ − 3σ)")
plt.xlabel("Date")
plt.ylabel("Score")
plt.grid(True, alpha=0.3)
plt.legend(ncol=2, fontsize=9)
plt.tight_layout()

plt.savefig(OUTPUT_DIR / "evolution_scores.png", dpi=150)
plt.close()

print("📈 Graphe évolution généré : resultats/evolution_scores.png")


# =====================
# CLASSEMENT FINAL
# =====================
classement = []
for joueur, rating in ratings.items():
    classement.append({
        "joueur": joueur,
        "mu": rating.mu,
        "sigma": rating.sigma,
        "score": rating.mu - 3 * rating.sigma,
        "matches": nb_matchs[joueur]
    })

df_classement = pd.DataFrame(classement)
df_classement = df_classement.sort_values("score", ascending=False)
df_classement.insert(0, "rang", range(1, len(df_classement) + 1))

# =====================
# EXPORT CSV
# =====================
df_classement.to_csv(OUTPUT_DIR / "classement_actuel.csv", index=False)
pd.DataFrame(historique).to_csv(OUTPUT_DIR / "historique_classement.csv", index=False)

print("✅ Classement généré")
print(" - resultats/classement_actuel.csv")
print(" - resultats/historique_classement.csv")
