import pandas as pd
import pycountry

INPUT = "data/out/peer_groups_human.csv"
OUTPUT = "data/out/peer_groups_human_explained.csv"

# 1) Načti humánní skupiny
df = pd.read_csv(INPUT, dtype={"iso3": str})

# 2) Mapování ISO numeric -> jméno státu
def num_to_name(num_str: str) -> str:
    try:
        rec = pycountry.countries.get(numeric=str(int(num_str)).zfill(3))
        return rec.name if rec else num_str
    except Exception:
        return num_str

df["country_name"] = df["iso3"].apply(num_to_name)

# 3) Názvy a vysvětlení pro každou skupinu (matchuje definice v 33_build_peer_groups_human.py)
cluster_meta = {
    0:  ("EU Core West", "Západní jádro EU s vysokou otevřeností a sofistikovanou poptávkou po průmyslových vstupech."),
    1:  ("EU Nordics", "Severské ekonomiky s vysokou přidanou hodnotou, silná orientace na technologie a služby."),
    2:  ("Baltics", "Malé, velmi otevřené ekonomiky s rychlou integrací do EU hodnotových řetězců."),
    3:  ("Central Europe (V4+AT+SI)", "Průmyslové jádro střední Evropy, vysoký podíl strojírenství a automobilového dodavatelského řetězce."),
    4:  ("Southern EU (Med EU)", "Mediterránní členové EU – smíšený profil (spotřeba, průmysl, stavebnictví)."),
    5:  ("UK & CH", "Velké finanční a obchodní huby s vyspělou poptávkou a vysokou kupní silou."),
    6:  ("Western Balkans", "Přechodové ekonomiky s rostoucí poptávkou po investičním zboží a stavebních vstupech."),
    7:  ("Eastern Partnership & Caucasus", "Východní partnerství a Kavkaz – tranzitní poloha, heterogenní profil, časté regulační frikce."),
    8:  ("Russia & Central Asia", "Rusko + Střední Asie – komoditní základna, importy strojírenských vstupů a spotřebního zboží."),
    9:  ("North America", "Velké, bohaté trhy s vysokou diverzifikací dovozu."),
    10: ("Central America & Caribbean", "Menší, často ostrovní ekonomiky, dovoz širokého spektra základních i spotřebních statků."),
    11: ("South America", "Středně velké až velké trhy, mix komoditních a průmyslových dovozů."),
    12: ("GCC", "Ropná jádra Perského zálivu – vysoká kupní síla, velká poptávka po stavebnictví a technologiích."),
    13: ("Levant & Iran/Iraq/Yemen", "Heterogenní, geopoliticky citlivý region, od high‑tech po základní statky."),
    14: ("North Africa (Med non‑EU)", "Severní Afrika mimo EU – mix průmyslu, spotřeby a energetiky, různé překážky přístupu."),
    15: ("East Asia Advanced", "Japonsko, Korea, Taiwan, Hongkong, Macao – vysoce technické hodnotové řetězce."),
    16: ("China", "Čína jako samostatný blok – obří a specifický importní profil."),
    17: ("Southeast Asia", "ASEAN – rychle rostoucí poptávka, silná výroba a diversifikace partnerů."),
    18: ("South Asia", "Jižní Asie – velké trhy, rostoucí průmysl a infrastruktura."),
    19: ("Sub‑Saharan Africa – West", "Západní Afrika – rostoucí spotřeba, infrastrukturní potřeby, vyšší logistická frikce."),
    20: ("Sub‑Saharan Africa – East & Horn", "Východní Afrika a Africký roh – růst populace a infrastruktury."),
    21: ("Sub‑Saharan Africa – South", "Jižní Afrika + sousedé – větší průmyslová základna a regionální huby."),
    22: ("Oceania & Pacific", "Austrálie, NZ a Pacifik – vysoce otevřené trhy (ANZ) a malé ostrovní ekonomiky."),
}

# 4) Seskup a vytvoř prezentovatelný výstup
grouped = (
    df.groupby("cluster")["country_name"]
      .apply(lambda lst: ", ".join(sorted(lst)))
      .reset_index()
)

grouped["grouping_name"] = grouped["cluster"].map(lambda c: cluster_meta.get(c, ("Group "+str(c), ""))[0])
grouped["explanation"] = grouped["cluster"].map(lambda c: cluster_meta.get(c, ("", ""))[1])
grouped = grouped.rename(columns={"cluster": "grouping_no", "country_name": "countries"})
grouped = grouped[["grouping_no", "grouping_name", "countries", "explanation"]]

# 5) Ulož
grouped.to_csv(OUTPUT, index=False)
print(f"[peer-human] Wrote {OUTPUT} with {len(grouped)} groups.")
