import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Padel Business Model", layout="wide")
st.title("🎾 Finanční model padelových kurtů")

# --- BOČNÍ PANEL - VSTUPNÍ POLE ---
st.sidebar.header("🎛 Nastavení modelu")

with st.sidebar.expander("🏗 Investice a financování", expanded=True):
    n_kurtu = st.number_input("Počet kurtů", min_value=1, value=3, step=1)
    investice_kurt = st.number_input("Cena za 1 kurt (Kč)", min_value=0, value=800000, step=10000)
    vlastni_kapital_proc = st.number_input("% vlastního kapitálu", min_value=0, max_value=100, value=20) / 100
    urok_uveru_pa = st.number_input("Úroková sazba úvěru (% p.a.)", value=6.0, step=0.1) / 100
    doba_uveru_let = st.number_input("Doba splácení úvěru (roky)", min_value=1, value=5)
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
vlastni_kapital_czk = celkova_investice * vlastni_kapital_proc
vyska_uveru = celkova_investice - vlastni_kapital_czk

# Výpočet měsíční anuitní splátky
if vyska_uveru > 0:
    r_mesicni = urok_uveru_pa / 12
    n_splatek = doba_uveru_let * 12
    # Vzorec pro anuitu
    mesicni_splatka = vyska_uveru * (r_mesicni * (1 + r_mesicni) ** n_splatek) / ((1 + r_mesicni) ** n_splatek - 1)
else:
    mesicni_splatka = 0

mesicni_vynos = n_kurtu * cena_hod * obsazenost * 30.42

# Inicializace časových řad
cash_flows_mesicni = [-vlastni_kapital_czk]
akumulovany_cf = [-vlastni_kapital_czk]

for m in range(1, mesicu + 1):
    # Výnosy pouze v sezóně
    vynos = mesicni_vynos if 1 <= (m % 12) <= sezona else 0

    # Splátka úvěru běží jen po dobu splatnosti
    aktualni_splatka = mesicni_splatka if m <= (doba_uveru_let * 12) else 0

    # Čistý měsíční tok
    cisty_tok = vynos - opex_mesic - aktualni_splatka

    cash_flows_mesicni.append(cisty_tok)
    akumulovany_cf.append(akumulovany_cf[-1] + cisty_tok)

# Výpočet NPV
mesicni_diskont = (1 + diskontni_mira) ** (1 / 12) - 1
npv_vysledek = npf.npv(mesicni_diskont, cash_flows_mesicni)

# --- ZOBRAZENÍ VÝSLEDKŮ ---
st.header("📊 Výsledky analýzy")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Investice (vlastní)", f"{vlastni_kapital_czk:,.0f} Kč")
c2.metric("Výše úvěru", f"{vyska_uveru:,.0f} Kč")
c3.metric("Měsíční splátka", f"{mesicni_splatka:,.0f} Kč")
c4.metric("NPV projektu", f"{npv_vysledek:,.0f} Kč")

# --- GRAF ---
fig, ax = plt.subplots(figsize=(12, 6))
mesice_osa = range(mesicu + 1)
ax.plot(mesice_osa, akumulovany_cf, color='dodgerblue', lw=3, label="Kumulativní Cash Flow")
ax.axhline(0, color='black', lw=1)

# Svislá čára pro konec splácení úvěru
if vyska_uveru > 0:
    ax.axvline(doba_uveru_let * 12, color='orange', linestyle='--', label="Úvěr splacen")

# Vybarvení zisku a ztráty
ax.fill_between(mesice_osa, akumulovany_cf, 0, where=(np.array(akumulovany_cf) >= 0), color='green', alpha=0.2)
ax.fill_between(mesice_osa, akumulovany_cf, 0, where=(np.array(akumulovany_cf) < 0), color='red', alpha=0.2)

ax.set_title("Ekonomický vývoj v čase (včetně financování)", fontsize=14)
ax.set_ylabel("Zůstatek (CZK)")
ax.set_xlabel("Měsíce")
ax.legend()
ax.grid(True, alpha=0.2)

st.pyplot(fig)