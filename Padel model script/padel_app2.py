import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf # Knihovna pro finanční funkce

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Padel Feasibility Study", layout="wide")
st.title("🎾 Studie proveditelnosti: Padelové kurty")

# --- BOČNÍ PANEL - VSTUPNÍ POLE ---
st.sidebar.header("🎛 Nastavení modelu")

with st.sidebar.expander("🏗 Investice a financování", expanded=True):
    n_kurtu = st.number_input("Počet kurtů", min_value=1, value=3, step=1)
    investice_kurt = st.number_input("Cena za 1 kurt (Kč)", min_value=0, value=800000, step=10000)
    vlastni_kapital_proc = st.number_input("% vlastního kapitálu", min_value=0, max_value=100, value=20) / 100
    diskontni_mira = st.number_input("Roční diskontní míra (%)", min_value=0.0, value=8.0, step=0.5) / 100

with st.sidebar.expander("🎾 Provozní parametry", expanded=True):
    cena_hod = st.number_input("Cena za hodinu (Kč)", min_value=0, value=450, step=50)
    obsazenost = st.number_input("Průměrná obsazenost (hod/den)", min_value=0.0, max_value=14.0, value=8.0, step=0.5)
    sezona = st.number_input("Délka sezóny (měsíce)", min_value=1, max_value=12, value=7)
    opex_mesic = st.number_input("Fixní měsíční náklady (Kč)", min_value=0, value=30000, step=1000)

with st.sidebar.expander("⏳ Časový horizont", expanded=True):
    horizont_let = st.number_input("Doba sledování (roky)", min_value=1, max_value=30, value=10)

# --- VÝPOČTY ---
mesicu = horizont_let * 12
celkova_investice = n_kurtu * investice_kurt
mesicni_vynos = n_kurtu * cena_hod * obsazenost * 30.42

cash_flows_mesicni = [-celkova_investice] # Měsíc 0 je výdej investice
akumulovany_cf = [-celkova_investice]

for m in range(1, mesicu + 1):
    # Příjmy pouze v sezóně
    vynos = mesicni_vynos if 1 <= (m % 12) <= sezona else 0
    # Čistý měsíční tok (Vynos - Náklady)
    cisty_tok = vynos - opex_mesic
    cash_flows_mesicni.append(cisty_tok)
    akumulovany_cf.append(akumulovany_cf[-1] + cisty_tok)

# Výpočet NPV (převod na měsíční diskontní míru)
mesicni_diskont = (1 + diskontni_mira)**(1/12) - 1
npv_vysledek = npf.npv(mesicni_diskont, cash_flows_mesicni)

# --- ZOBRAZENÍ VÝSLEDKŮ ---
col1, col2, col3 = st.columns(3)
col1.metric("Celková investice", f"{celkova_investice:,.0f} Kč")
col2.metric("NPV (Čistá současná hodnota)", f"{npv_vysledek:,.0f} Kč",
            help="Pokud je NPV > 0, projekt je ekonomicky přijatelný.")
col3.metric("Doba návratnosti (nominální)", f"{next((i for i, v in enumerate(akumulovany_cf) if v >= 0), 'Nedohledno')} měsíců")

# --- GRAF ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(range(mesicu + 1), akumulovany_cf, color='dodgerblue', lw=2.5, label="Kumulativní Cash Flow")
ax.axhline(0, color='red', linestyle='--', alpha=0.6)
ax.fill_between(range(mesicu + 1), akumulovany_cf, 0, where=(np.array(akumulovany_cf) >= 0), color='green', alpha=0.2)
ax.fill_between(range(mesicu + 1), akumulovany_cf, 0, where=(np.array(akumulovany_cf) < 0), color='red', alpha=0.2)
ax.set_title("Průběh kumulativního Cash Flow v čase")
ax.set_ylabel("CZK")
ax.set_xlabel("Měsíce")
st.pyplot(fig)
