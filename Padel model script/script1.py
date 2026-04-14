import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Přepne na interaktivní okno
import matplotlib.pyplot as plt

# --- 1. VSTUPNÍ PARAMETRY (Změň podle potřeby) ---
pocet_kurtu = 3
cena_hodina = 250
obsazenost_hod_den = 4
sezona_mesicu = 7
investice_celkem = 3000000  # Příklad: 600k za kurt
podil_vlastniho_kapitalu = 1
urokova_mira_pa = 0.06
doba_splaceni_let = 10
rocni_opex = 100000

# --- 2. POMOCNÉ VÝPOČTY ---
mesicu_celkem = 120  # 5 let
vlastni_kapital = investice_celkem * podil_vlastniho_kapitalu
vyse_uveru = investice_celkem - vlastni_kapital

# Výpočet anuitní splátky (vzorec pro měsíční splátku)
r = urokova_mira_pa / 12
n = doba_splaceni_let * 12
mesicni_splatka = vyse_uveru * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

mesicni_vynos_sezona = pocet_kurtu * cena_hodina * obsazenost_hod_den * 30.42
mesicni_opex = rocni_opex / 12

# --- 3. SIMULACE V ČASE ---
osy_x = np.arange(0, mesicu_celkem + 1)
akumulovane_vynosy = [0]
akumulovane_naklady = [vlastni_kapital]

aktualni_vynosy = 0
aktualni_naklady = vlastni_kapital

for m in range(1, mesicu_celkem + 1):
    # Výnosy (pouze v sezóně 1-7, 13-19, atd.)
    if 1 <= (m % 12) <= sezona_mesicu:
        aktualni_vynosy += mesicni_vynos_sezona

    # Náklady (OPEX + Splátka úvěru pokud ještě není splacen)
    aktualni_naklady += mesicni_opex
    if m <= n:
        aktualni_naklady += mesicni_splatka

    akumulovane_vynosy.append(aktualni_vynosy)
    akumulovane_naklady.append(aktualni_naklady)

# --- 4. VIZUALIZACE ---
plt.figure(figsize=(12, 7))
plt.plot(osy_x, akumulovane_vynosy, label='Kumulativní výnosy', color='green', lw=2)
plt.plot(osy_x, akumulovane_naklady, label='Kumulativní náklady (vč. úvěru)', color='red', lw=2)

# Hledání bodu zvratu
idx_zvratu = np.where(np.array(akumulovane_vynosy) >= np.array(akumulovane_naklady))[0]
if len(idx_zvratu) > 0:
    mesic_zvratu = idx_zvratu[0]
    plt.scatter(mesic_zvratu, akumulovane_vynosy[mesic_zvratu], color='black', zorder=5)
    plt.annotate(f'BOD ZVRATU: {mesic_zvratu}. měsíc',
                 xy=(mesic_zvratu, akumulovane_vynosy[mesic_zvratu]),
                 xytext=(mesic_zvratu - 10, akumulovane_vynosy[mesic_zvratu] + 500000),
                 arrowprops=dict(facecolor='black', shrink=0.05))

plt.title('Finanční model: Analýza bodu zvratu (Break-even Analysis)', fontsize=14)
plt.xlabel('Měsíce od zahájení projektu', fontsize=12)
plt.ylabel('Částka v CZK', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()