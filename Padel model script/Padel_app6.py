import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Padel Business Model Pro", layout="wide")
st.title("🎾 Profesionální finanční model padelových kurtů")

# --- BOČNÍ PANEL - VSTUPNÍ POLE ---
st.sidebar.header("🎛 Nastavení modelu")

with st.sidebar.expander("🏗 Investice a financování", expanded=True):
    n_kurtu = st.number_input("Počet kurtů", min_value=1, value=3, step=1)
    investice_kurt = st.number_input("Cena za 1 kurt (Kč)", min_value=0, value=1000000, step=10000)
    vlastni_kapital_proc = st.number_input("% vlastního kapitálu", min_value=0, max_value=100, value=80) / 100
    urok_uveru_pa = st.number_input("Úroková sazba úvěru (% p.a.)", value=6.0, step=0.1) / 100
    doba_uveru_let = st.number_input("Doba splácení úvěru (roky)", min_value=1, value=5)
    diskontni_mira = st.number_input("Roční diskontní míra (%)", min_value=0.0, value=8.0, step=0.5) / 100

with st.sidebar.expander("💰 Cenotvorba (Celková kapacita)", expanded=True):
    # Pevně ukotvená otevírací doba 14h na každý kurt
    oteviracka_na_kurt = 14
    kapacita_arealu_celkem = n_kurtu * oteviracka_na_kurt

    st.info(f"Celková denní kapacita areálu: {kapacita_arealu_celkem} hodin")

    st.subheader("Špička (Prime Time)")
    # OPRAVA: Upper limit nastaven na kapacita_arealu_celkem
    hodin_spicka_total = st.number_input(
        "Celkový počet hodin špičky v areálu/den",
        min_value=0,
        max_value=kapacita_arealu_celkem,
        value=min(12, kapacita_arealu_celkem)
    )
    cena_spicka = st.number_input("Cena ve špičce (Kč/h)", value=600)
    obsazenost_spicka = st.number_input("% obsazenost ve špičce", value=90) / 100

    st.subheader("Mimo špičku (Off-Peak)")
    # Automatický dopočet zbytku kapacity
    hodin_mimo_total = kapacita_arealu_celkem - hodin_spicka_total
    st.write(f"Mimo špičku zbývá: **{hodin_mimo_total} hodin/den**")

    cena_mimo = st.number_input("Cena mimo špičku (Kč/h)", value=350)
    obsazenost_mimo = st.number_input("% obsazenost mimo špičku", value=40) / 100

with st.sidebar.expander("📈 Dynamický pricing a inflace", expanded=True):
    narust_ceny_rok = st.number_input("Roční navýšení ceny nájmu (%)", value=3.0) / 100
    narust_opex_rok = st.number_input("Roční nárůst nákladů/inflace (%)", value=2.0) / 100

with st.sidebar.expander("⏳ Horizont a provoz", expanded=True):
    opex_mesic_start = st.number_input("Počáteční fixní měsíční náklady (Kč)", value=30000)
    sezona = st.number_input("Délka sezóny (měsíce)", min_value=1, max_value=12, value=7)
    horizont_let = st.number_input("Doba sledování (roky)", min_value=1, max_value=30, value=10)

# --- VÝPOČTY ---
mesicu = horizont_let * 12
celkova_investice = n_kurtu * investice_kurt
vlastni_kapital_czk = celkova_investice * vlastni_kapital_proc
vyska_uveru = celkova_investice - vlastni_kapital_czk

# Měsíční splátka úvěru
if vyska_uveru > 0:
    r_mesicni = urok_uveru_pa / 12
    n_splatek = doba_uveru_let * 12
    mesicni_splatka = vyska_uveru * (r_mesicni * (1 + r_mesicni) ** n_splatek) / ((1 + r_mesicni) ** n_splatek - 1)
else:
    mesicni_splatka = 0

# Inicializace časových řad
cash_flows_mesicni = [-vlastni_kapital_czk]
akumulovany_cf = [-vlastni_kapital_czk]

for m in range(1, mesicu + 1):
    # Určení aktuálního roku (pro dynamický pricing)
    aktualni_rok = (m - 1) // 12

    # Eskalace cen a nákladů
    cena_spicka_akt = cena_spicka * (1 + narust_ceny_rok) ** aktualni_rok
    cena_mimo_akt = cena_mimo * (1 + narust_ceny_rok) ** aktualni_rok
    current_opex_akt = opex_mesic_start * (1 + narust_opex_rok) ** aktualni_rok

    # Denní tržba založená na celkových hodinách areálu
    denni_trzba_spicka = hodin_spicka_total * obsazenost_spicka * cena_spicka_akt
    denni_trzba_mimo = hodin_mimo_total * obsazenost_mimo * cena_mimo_akt
    mesicni_vynos_total = (denni_trzba_spicka + denni_trzba_mimo) * 30.42

    # Pouze v sezóně
    vynos = mesicni_vynos_total if 1 <= (m % 12) <= sezona else 0

    # Splátka úvěru
    aktualni_splatka = mesicni_splatka if m <= (doba_uveru_let * 12) else 0

    # Čistý měsíční tok
    cisty_tok = vynos - current_opex_akt - aktualni_splatka

    cash_flows_mesicni.append(cisty_tok)
    akumulovany_cf.append(akumulovany_cf[-1] + cisty_tok)

# Výpočet NPV
mesicni_diskont = (1 + diskontni_mira) ** (1 / 12) - 1
npv_vysledek = npf.npv(mesicni_diskont, cash_flows_mesicni)

# Výpočet Bodu zvratu
idx_zvratu = np.where(np.array(akumulovany_cf) >= 0)[0]
mesic_zvratu = idx_zvratu[0] if len(idx_zvratu) > 0 else None

# --- ZOBRAZENÍ VÝSLEDKŮ ---
st.header("📊 Výsledky pokročilé analýzy")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vlastní investice", f"{vlastni_kapital_czk:,.0f} Kč")
c2.metric("Měsíční splátka", f"{mesicni_splatka:,.0f} Kč" if vyska_uveru > 0 else "0 Kč")
c3.metric("NPV projektu", f"{npv_vysledek:,.0f} Kč")
c4.metric("Návratnost", f"{mesic_zvratu} m. ({round(mesic_zvratu / 12, 1)} let)" if mesic_zvratu else "Nedohledno")

# --- GRAF ---
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(range(mesicu + 1), akumulovany_cf, color='dodgerblue', lw=3, label="Kumulativní Cash Flow")
ax.axhline(0, color='black', lw=1.5)

if mesic_zvratu:
    ax.scatter(mesic_zvratu, 0, color='red', s=100, zorder=5)

ax.fill_between(range(mesicu + 1), akumulovany_cf, 0, where=(np.array(akumulovany_cf) >= 0), color='green', alpha=0.15)
ax.fill_between(range(mesicu + 1), akumulovany_cf, 0, where=(np.array(akumulovany_cf) < 0), color='red', alpha=0.15)

ax.set_title("Ekonomický vývoj s dynamickým pricingem", fontsize=14)
ax.set_ylabel("Zůstatek (CZK)")
ax.set_xlabel("Měsíce")
ax.grid(True, alpha=0.2)
st.pyplot(fig)

# --- INFORMAČNÍ TABULKA ---
with st.expander("🔍 Detail cenotvorby a kapacity"):
    st.write(f"Celková denní kapacita areálu: **{kapacita_arealu_celkem} hodin**")
    st.write(f"Počáteční denní tržba v sezóně: {round(denni_trzba_spicka + denni_trzba_mimo, 0):,.0f} Kč")
    st.write(
        f"Cena ve špičce v {horizont_let}. roce: {round(cena_spicka * (1 + narust_ceny_rok) ** (horizont_let - 1), 0):,.0f} Kč")