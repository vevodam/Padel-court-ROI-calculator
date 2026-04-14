import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Padel Business Model", layout="wide")
st.title("🎾 Finanční model padelových kurtů")

# --- BOČNÍ PANEL S PARAMETRY ---
st.sidebar.header("Vstupní parametry")

n_kurtu = st.sidebar.number_input("Počet kurtů", value=3)
cena_hod = st.sidebar.slider("Cena za hodinu (Kč)", 200, 1000, 400)
obsazenost = st.sidebar.slider("Denní vytížení (hod/den)", 1, 14, 10)
sezona = st.sidebar.slider("Délka sezóny (měsíce)", 1, 12, 7)

st.sidebar.markdown("---")
investice_kurt = st.sidebar.number_input("Investice na 1 kurt", value=600000)
vlastni_kapital_proc = st.sidebar.slider("% Vlastního kapitálu", 0, 100, 20) / 100

st.sidebar.markdown("---")
horizont_let = st.sidebar.slider("Časový horizont (roky)", 1, 15, 5)

# --- VÝPOČTY ---
mesicu = horizont_let * 12
celkova_investice = n_kurtu * investice_kurt
vlastni = celkova_investice * vlastni_kapital_proc
uver = celkova_investice - vlastni

# Zjednodušený měsíční model
mesicni_vynos = n_kurtu * cena_hod * obsazenost * 30.42
mesicni_opex = (celkova_investice * 0.05) / 12  # Odhad 5% z investice na údržbu/nájem

x_osa = np.arange(0, mesicu + 1)
y_vynosy = [0]
y_naklady = [vlastni]

akt_vyn = 0
akt_nak = vlastni

for m in range(1, mesicu + 1):
    if 1 <= (m % 12) <= sezona:
        akt_vyn += mesicni_vynos
    akt_nak += mesicni_opex
    y_vynosy.append(akt_vyn)
    y_naklady.append(akt_nak)

# --- VYKRESLENÍ ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(x_osa, y_vynosy, label="Výnosy", color="green", lw=2)
ax.plot(x_osa, y_naklady, label="Náklady", color="red", lw=2)
ax.set_xlabel("Měsíce")
ax.set_ylabel("CZK")
ax.grid(True, alpha=0.3)
ax.legend()

st.pyplot(fig)

# --- UKAZATELE ---
col1, col2, col3 = st.columns(3)
col1.metric("Celková investice", f"{celkova_investice:,.0f} Kč")
col2.metric("Vlastní kapitál", f"{vlastni:,.0f} Kč")
col3.metric("Úvěr", f"{uver:,.0f} Kč")