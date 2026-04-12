import streamlit as st
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

#V této verzi je upravený vizuál grafu aby byl propracovanější a uživatelsky příjemnější


# --- POMOCNÉ FUNKCE ---
def format_czk(hodnota):
    """Naformátuje číslo do české podoby s mezerami jako oddělovači tisíců."""
    return f"{hodnota:,.0f}".replace(",", " ")


# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Padel Business Model Pro", layout="wide")
st.title("🎾 Profesionální finanční model padelových kurtů")

# --- BOČNÍ PANEL - VSTUPNÍ POLE ---
st.sidebar.header("🎛 Nastavení modelu")

with st.sidebar.expander("🏗 Investice a financování", expanded=True):
    n_kurtu = st.number_input("Počet kurtů", min_value=1, value=3, step=1)
    investice_kurt = st.number_input("Cena za 1 kurt (Kč)", min_value=0, value=1000000, step=10000)
    vlastni_kapital_proc = st.number_input("% vlastního kapitálu", min_value=0, max_value=100, value=100) / 100
    urok_uveru_pa = st.number_input("Úroková sazba úvěru (% p.a.)", value=6.0, step=0.1) / 100
    doba_uveru_let = st.number_input("Doba splácení úvěru (roky)", min_value=1, value=5)
    diskontni_mira = st.number_input("Požadovaný výnos vl. kapitálu / Diskont (%)", min_value=0.0, value=10.0,
                                     step=0.5) / 100

with st.sidebar.expander("💰 Cenotvorba a Kapacita", expanded=True):
    # Dynamická otevírací doba
    oteviracka_na_kurt = st.number_input("Denní otevírací doba 1 kurtu (h)", min_value=1, max_value=24, value=14)
    kapacita_arealu_celkem = n_kurtu * oteviracka_na_kurt

    st.info(f"Celková denní kapacita areálu: **{kapacita_arealu_celkem} hodin**")


    st.subheader("Špička (Prime Time)")
    # Zadávání špičky na JEDEN kurt - systém si zbytek dopočítá
    hodin_spicka_kurt = st.number_input(
        "Počet hodin špičky na 1 kurt/den",
        min_value=0,
        max_value=int(oteviracka_na_kurt),
        value=min(4, int(oteviracka_na_kurt))
    )

    hodin_spicka_total = hodin_spicka_kurt * n_kurtu
    cena_spicka = st.number_input("Cena ve špičce (Kč/h)", value=300)
    obsazenost_spicka = st.number_input("% obsazenost ve špičce", value=80) / 100

    st.subheader("Mimo špičku (Off-Peak)")
    hodin_mimo_total = kapacita_arealu_celkem - hodin_spicka_total
    st.write(f"Mimo špičku zbývá v celém areálu: **{hodin_mimo_total} hodin/den**")

    cena_mimo = st.number_input("Cena mimo špičku (Kč/h)", value=200)
    obsazenost_mimo = st.number_input("% obsazenost mimo špičku", value=30) / 100

with st.sidebar.expander("📈 Dynamický pricing a inflace", expanded=True):
    narust_ceny_rok = st.number_input("Roční navýšení ceny nájmu (%)", value=3.0) / 100
    narust_opex_rok = st.number_input("Roční nárůst nákladů/inflace (%)", value=2.0) / 100

with st.sidebar.expander("⏳ Horizont a provoz", expanded=True):
    # Realističtější výchozí OPEX
    opex_mesic_start = st.number_input("Počáteční fixní měsíční OPEX (Kč)", value=30000, step=5000)
    sezona = st.number_input("Délka sezóny (měsíce v roce)", min_value=1, max_value=12, value=7)
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

# Výpočet počáteční denní tržby (pro informační tabulku)
pocatecni_denni_trzba_spicka = hodin_spicka_total * obsazenost_spicka * cena_spicka
pocatecni_denni_trzba_mimo = hodin_mimo_total * obsazenost_mimo * cena_mimo
pocatecni_denni_trzba_celkem = pocatecni_denni_trzba_spicka + pocatecni_denni_trzba_mimo

# Inicializace časových řad
cash_flows_mesicni = [-vlastni_kapital_czk]
akumulovany_cf = [-vlastni_kapital_czk]

for m in range(1, mesicu + 1):
    aktualni_rok = (m - 1) // 12
    # Oprava logiky pro určení měsíce v roce (1 až 12)
    mesic_v_roce = ((m - 1) % 12) + 1

    # Eskalace cen a nákladů
    cena_spicka_akt = cena_spicka * (1 + narust_ceny_rok) ** aktualni_rok
    cena_mimo_akt = cena_mimo * (1 + narust_ceny_rok) ** aktualni_rok
    current_opex_akt = opex_mesic_start * (1 + narust_opex_rok) ** aktualni_rok

    # Denní a měsíční tržba
    denni_trzba_spicka = hodin_spicka_total * obsazenost_spicka * cena_spicka_akt
    denni_trzba_mimo = hodin_mimo_total * obsazenost_mimo * cena_mimo_akt
    mesicni_vynos_total = (denni_trzba_spicka + denni_trzba_mimo) * 30.42

    # Aplikace sezónnosti se správnou logikou
    vynos = mesicni_vynos_total if 1 <= mesic_v_roce <= sezona else 0

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
c1.metric("Vlastní investice", f"{format_czk(vlastni_kapital_czk)} Kč")
c2.metric("Měsíční splátka úvěru", f"{format_czk(mesicni_splatka)} Kč" if vyska_uveru > 0 else "0 Kč")
c3.metric(
    "NPV vlastního kapitálu",
    f"{format_czk(npv_vysledek)} Kč",
    help="Čistá současná hodnota počítaná z peněžních toků po odečtení splátek úvěru. Ukazuje hodnotu přidanou nad rámec požadovaného výnosu."
)
c4.metric(
    "Doba návratnosti",
    f"{mesic_zvratu} m. ({round(mesic_zvratu / 12, 1)} let)" if mesic_zvratu else "Nedohledno",
    help="Bod, kdy kumulativní cash flow protne nulu."
)

# --- INTERAKTIVNÍ GRAF (PLOTLY) ---
# --- VYLEPŠENÝ INTERAKTIVNÍ GRAF (PLOTLY) ---
fig = go.Figure()

# 1. Sloupcový graf pro MĚSÍČNÍ Cash Flow (na pozadí)
# Rozdělíme barvy: zelená pro plusové měsíce, červená pro minusové (investice a ztráty)
barvy_mesicni = ['#2ca02c' if val >= 0 else '#d62728' for val in cash_flows_mesicni]
fig.add_trace(go.Bar(
    x=list(range(mesicu + 1)),
    y=cash_flows_mesicni,
    name='Měsíční Cash Flow',
    marker_color=barvy_mesicni,
    opacity=0.3, # Poloprůhledné, aby to nerušilo hlavní křivku
    hovertemplate='Měsíční CF: %{y:,.0f} Kč<extra></extra>'
))

# 2. Hlavní křivka KUMULATIVNÍHO Cash Flow
fig.add_trace(go.Scatter(
    x=list(range(mesicu + 1)),
    y=akumulovany_cf,
    mode='lines',
    name='Kumulativní Zůstatek',
    line=dict(color='#1f77b4', width=4), # Silnější a výraznější linka
    hovertemplate='Kumulativně: %{y:,.0f} Kč<extra></extra>'
))

# 3. Zvýraznění bodu zvratu s textovou anotací
if mesic_zvratu:
    fig.add_trace(go.Scatter(
        x=[mesic_zvratu],
        y=[0],
        mode='markers+text',
        name='Bod zvratu',
        text=[f'Návratnost: {mesic_zvratu}. měsíc'],
        textposition="top left",
        marker=dict(color='#d62728', size=14, symbol='diamond', line=dict(color='white', width=2)),
        textfont=dict(size=13, color='#d62728')
    ))

# 4. Formátování a úprava layoutu
fig.update_layout(
    title=dict(text="Finanční vývoj projektu v čase", font=dict(size=20)),
    xaxis=dict(title="Měsíce provozu", showgrid=False), # Skrytí vertikální mřížky
    yaxis=dict(title="Hotovost (CZK)", tickformat=",d", showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)'),
    hovermode="x unified",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), # Legenda vodorovně nahoře
    margin=dict(l=20, r=20, t=60, b=20),
    plot_bgcolor='rgba(0,0,0,0)', # Průhledné pozadí grafu pro elegantní splynutí s aplikací
    paper_bgcolor='rgba(0,0,0,0)'
)

# Výraznější nulová linka
fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1, opacity=0.7)

# Parametr theme="streamlit" zajistí, že graf bude respektovat světlý/tmavý režim prohlížeče uživatele
st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# --- INFORMAČNÍ TABULKA ---
with st.expander("🔍 Detail cenotvorby a kapacity (Rok 1 vs. Konec)"):
    st.write(f"Celková denní kapacita areálu: **{kapacita_arealu_celkem} hodin**")
    st.write(f"Počáteční modelovaná denní tržba v sezóně: **{format_czk(pocatecni_denni_trzba_celkem)} Kč**")
    st.write(f"Cena ve špičce v **1. roce**: {format_czk(cena_spicka)} Kč/h")

    cena_spicka_konec = cena_spicka * (1 + narust_ceny_rok) ** (horizont_let - 1)
    st.write(f"Cena ve špičce v **{horizont_let}. roce**: {format_czk(cena_spicka_konec)} Kč/h")
