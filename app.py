from pathlib import Path

import pandas as pd
import streamlit as st

import matplotlib as mp
import matplotlib.pyplot as plt
import plotly.express as px

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="L'électricité dans 12 quartiers", page_icon="⚡", layout="wide")

st.title("L'électricité dans 12 quartiers")
st.caption("Relevés mensuels de janvier 2024 à décembre 2025. Données fictives.")

brut = pd.read_csv(DOSSIER / "consommation_brut.csv")
st.write(f"Le fichier brut compte {len(brut)} lignes.")
st.dataframe(brut.head(10), hide_index=True)

@st.cache_data
def charger():
    return pd.read_csv(DOSSIER / "consommation_propre.csv")

propre = charger()
st.write(f"Le fichier propre compte {len(propre)} lignes.")

communes = sorted(propre["commune"].unique())
choix_commune = st.sidebar.multiselect("Commune", communes, default=communes)
choix_annee = st.sidebar.selectbox("Annee", [2024, 2025], index=1)

if not choix_commune:
    st.warning("Veuillez choisir une commune")
else:
    filtre = propre[propre["commune"].isin(choix_commune)] #Pour choix commune
    filtre = filtre[pd.to_datetime(filtre["mois"]).dt.year == choix_annee]
    st.dataframe(filtre)

st.write("2025, toutes communes")

col1, col2, col3 = st.columns(3)

col1.metric("Consommation Totale", f"{(propre[pd.to_datetime(propre["mois"]).dt.year == 2025]["kwh"].sum() / 1000000).round(2)} millions de kWh")
col2.metric("Consommation moyenne par abonne", f"{(propre[pd.to_datetime(propre["mois"]).dt.year == 2025]["kwh"] / propre[pd.to_datetime(propre["mois"]).dt.year == 2025]["abonnes"]).mean().round(1)} kWh par abonne")
col3.metric("Heure journaliere moyenne de courant", f"{propre[pd.to_datetime(propre["mois"]).dt.year == 2025]["heures_courant"].mean().round(1)} heures de courant")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Conso Abonne Quartier", "Evolution consommation par commune", "Chaleur ou courant?", "Coupures plus longues", "Releves sortant du lot"])

with tab1:
    st.title("2025")
    st.title("Consommations par type")
    propre_2025 = propre[pd.to_datetime(propre["mois"]).dt.year == 2025]
    consos_types = propre_2025.groupby("type")["kwh_par_abonne"].mean().round(1)
    st.bar_chart(consos_types)

    consos_types_df = propre_2025.groupby("type")["kwh_par_abonne"].mean().round(1).reset_index()
    st.metric("Consommations par type pour 2025", f"Commercial : {consos_types_df.loc[0, "kwh_par_abonne"]} et Residentiel : {consos_types_df.loc[1, "kwh_par_abonne"]} kWh par abonne")

    st.title("Consommation par quartier")
    consos_quartier = propre_2025.groupby("quartier")["kwh_par_abonne"].mean().round(1).sort_values(ascending=False)
    st.bar_chart(consos_quartier)
    

with tab2:
    st.title("Evolution de la consommation par commune")
    conso_commune_mois = propre.pivot_table(index="mois", columns="commune", values="kwh_par_abonne")
    st.line_chart(conso_commune_mois)
    conso_commune_annee = propre.pivot_table(index=["commune"], columns="annee", values="kwh", aggfunc="sum")
    conso_commune_annee["hausse_%"] = ((conso_commune_annee[2025] / conso_commune_annee[2024] - 1) * 100)
    conso_commune_annee["hausse_%"] = conso_commune_annee["hausse_%"].round(1)  
    hausse_max = conso_commune_annee.nlargest(1, "hausse_%")
    signe = ""
    if hausse_max["hausse_%"].reset_index().loc[0, "hausse_%"] >= 0:
        signe = "+"
    else:
        signe = ""
    st.metric("Plus grande hausse de 2024 a 2025", f"{hausse_max.index[0]} {signe}{hausse_max["hausse_%"].reset_index().loc[0, "hausse_%"]}%")

with tab3:
    st.title("Chaleur ou Courant?")
    avec_meteo_residentiel = propre[propre["type"] == "Résidentiel"]
    st.scatter_chart(avec_meteo_residentiel, x="heures_courant", y="kwh_par_abonne")
    st.metric("Correlations", f"{avec_meteo_residentiel["kwh_par_abonne"].corr(avec_meteo_residentiel["heures_courant"]).round(2)} et {avec_meteo_residentiel["kwh_par_abonne"].corr(avec_meteo_residentiel["temperature_c"]).round(2)}")

with tab4:
    st.title("Coupures plus longues")
    cap_infos = propre[propre["commune"] == "Cap-Haïtien"][["mois", "heures_courant"]]
    cap_graphe = cap_infos["heures_courant"].plot(kind="hist", edgecolor="white", bins=15, title="Repartition des Heures courant au Cap-Haitien")
    cap_graphe.set_ylabel("Heures Courant")
    st.pyplot(cap_graphe.get_figure())

    copy_propre = propre.copy()
    copy_propre["mois"] = pd.to_datetime(copy_propre["mois"])
    

    st.metric("Nombre de releves sous 8 heures", f"{(copy_propre[(copy_propre["mois"].dt.year == 2025) & (copy_propre["heures_courant"] < 8)][["mois", "heures_courant", "quartier"]]).shape[0]} releves sous 8 heures")

with tab5:
    st.title("Plus grandes consommations")

    plus_grandes_consos = propre.nlargest(3, "kwh")[["mois", "quartier", "type", "kwh"]]

    plus_grandes_consos["label"] = (plus_grandes_consos["quartier"] + " - " + plus_grandes_consos["mois"].astype(str))

    st.bar_chart(plus_grandes_consos, x="label", y="kwh", color="type", horizontal=True, x_label="Quartier et Date")