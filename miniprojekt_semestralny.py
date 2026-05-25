import tkinter as tk
from tkinter import ttk
import requests
import json
from tkinter import messagebox
from datetime import datetime


REGIONY = {
    "dolnośląskie":        ["Wrocław", "Jelenia Góra", "Legnica", "Kłodzko", "Śnieżka"],
    "kujawsko-pomorskie":  ["Bydgoszcz", "Toruń", "Włocławek"],
    "lubelskie":           ["Lublin-Radawiec", "Terespol", "Włodawa", "Zamość"],
    "lubuskie":            ["Gorzów Wielkopolski", "Zielona Góra", "Słubice"],
    "łódzkie":             ["Łódź", "Sulejów", "Wieluń"],
    "małopolskie":         ["Kraków", "Zakopane", "Tarnów", "Nowy Sącz", "Kasprowy Wierch"],
    "mazowieckie":         ["Warszawa", "Płock", "Siedlce", "Kozienice", "Mława", "Ostrołęka"],
    "opolskie":            ["Opole"],
    "podkarpackie":        ["Rzeszów-Jasionka", "Krosno", "Lesko", "Przemyśl"],
    "podlaskie":           ["Białystok", "Suwałki"],
    "pomorskie":           ["Gdańsk", "Gdynia", "Hel", "Łeba", "Chojnice", "Lębork", "Ustka"],
    "śląskie":             ["Katowice", "Częstochowa", "Bielsko-Biała", "Racibórz"],
    "świętokrzyskie":      ["Kielce", "Sandomierz"],
    "warmińsko-mazurskie": ["Olsztyn", "Elbląg", "Mikołajki", "Kętrzyn"],
    "wielkopolskie":       ["Poznań", "Kalisz", "Koło", "Leszno", "Piła"],
    "zachodniopomorskie":  ["Szczecin", "Koszalin", "Świnoujście", "Resko", "Szczecinek"],
}


# =====================================================================================
#  KLASA 1 — # Funkcje obsługujące komunikację z API, lokalny zapis oraz odczyt danych 
# =====================================================================================
class DaneMeteo:
    imgw_url = "https://danepubliczne.imgw.pl/api/data/synop"

    def odczywywanie_danych_offline(self):
        try:
            with open("pogoda_historia.json", "r") as file:
                plik_json_lokalny = json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Błąd tabeli", "Tabela nie istnieje, tworze nową")
            plik_json_lokalny = []
        return plik_json_lokalny

    def zapisywanie_danych_do_json(self, dane):
        with open("pogoda_historia.json", "w", encoding="utf-8") as file:
            json.dump(dane, file)

    def reset_danych(self):
        messagebox.showinfo("Status", "Pobieram dane...")
        try:
            odpowiedz = requests.get(self.imgw_url, timeout=5)
            if odpowiedz.status_code == 200:
                messagebox.showinfo("Status", "Poprawnie pobrano dane")
                return odpowiedz.json()
            else:
                messagebox.showerror("Status", f"Błąd serwera: {odpowiedz.status_code}")
        except requests.exceptions.RequestException as error:
            messagebox.showerror("Status", f"Błąd połączenia: {error}")
        return None

    def aktualizuj_dane(self):
        lokalne_dane = self.odczywywanie_danych_offline()
        nowe_dane = self.reset_danych()
        if nowe_dane is None:
            return
        dodane_rekordy = 0
        istniejace_identyfikatory = set()
        for x in lokalne_dane:
            identyfikator = f"{x['id_stacji'],x['stacja'],x['data_pomiaru'],x['godzina_pomiaru']}"
            istniejace_identyfikatory.add(identyfikator)
        for y in nowe_dane:
            nowy_identyfikator = f"{y['id_stacji'],y['stacja'],y['data_pomiaru'],y['godzina_pomiaru']}"
            if nowy_identyfikator in istniejace_identyfikatory:
                continue
            else:
                lokalne_dane.append(y)
                istniejace_identyfikatory.add(nowy_identyfikator)
                dodane_rekordy += 1
        self.zapisywanie_danych_do_json(lokalne_dane)
        if dodane_rekordy > 0:
            messagebox.showinfo("Status", "Dodano nowe rekordy poprawnie!")
        else:
            messagebox.showinfo("Status", "Baza danych jest aktualna")


# ===================================
#  KLASA 2 — obliczenia i analizy
# ===================================
class Statystyki:
    def __init__(self, dane_meteo: DaneMeteo):
        self.dane_meteo = dane_meteo

        self.stat_liczba  = None
        self.stat_srednia = None
        self.stat_max     = None
        self.stat_min     = None


    def przypisywanie_regionu(self, nazwa_stacji):
        for region, stacje in REGIONY.items():
            if nazwa_stacji in stacje:
                return region
        return "Nieznane"


    def obliczenia_cisnienia_i_opadow(self):
        wszystkie_dane = self.dane_meteo.odczywywanie_danych_offline()
        if not wszystkie_dane:
            messagebox.showerror("Brak danych", "Pobierz najpierw dane !")
            return {}
        statystyki_opadu_i_cisnienia = {}

        for x in wszystkie_dane:
            stacja   = x.get('stacja', 'nieznana')
            opad     = x.get('suma_opadu')
            cisnienie = x.get('cisnienie')
            region   = self.przypisywanie_regionu(stacja)

            if region not in statystyki_opadu_i_cisnienia:
                statystyki_opadu_i_cisnienia[region] = {
                    "suma_opadow": 0.0,
                    "suma_cisnienia": 0.0,
                    "ile_pomiarow_cisnienia": 0,
                }

            try:
                if opad is not None and opad != '':
                    statystyki_opadu_i_cisnienia[region]['suma_opadow'] += float(opad)
            except (ValueError, TypeError):
                pass

            try:
                if cisnienie is not None and cisnienie != '':
                    statystyki_opadu_i_cisnienia[region]["suma_cisnienia"] += float(cisnienie)
                    statystyki_opadu_i_cisnienia[region]["ile_pomiarow_cisnienia"] += 1
            except (ValueError, TypeError):
                pass

        return statystyki_opadu_i_cisnienia


    def aktualizuj_statystyki_widok(self, dane):
        if not dane or self.stat_liczba is None:
            return
        lista_temperatur = []
        stacja_max_temp = ["--", -999.0]
        stacja_min_temp = ["--",  999.0]

        for x in dane:
            try:
                wartosc_temperatury = x.get('temperatura')
                if wartosc_temperatury is not None and wartosc_temperatury != '':
                    wartosc_temperatury = float(wartosc_temperatury)
                    lista_temperatur.append(wartosc_temperatury)
                    if wartosc_temperatury > stacja_max_temp[1]:
                        stacja_max_temp = [x['stacja'], wartosc_temperatury]
                    if wartosc_temperatury < stacja_min_temp[1]:
                        stacja_min_temp = [x['stacja'], wartosc_temperatury]
            except:
                continue

        self.stat_liczba.set(f"Liczba stacji: {len(dane)}")
        if lista_temperatur:
            srednia = sum(lista_temperatur) / len(lista_temperatur)
            self.stat_srednia.set(f"Średnia temp: {srednia:.2f} °C")
            self.stat_max.set(f"Najcieplej: {stacja_max_temp[0]} ({stacja_max_temp[1]}°C)")
            self.stat_min.set(f"Najzimniej: {stacja_min_temp[0]} ({stacja_min_temp[1]}°C)")
        else:
            self.stat_srednia.set("Średnia temp: --")
            self.stat_max.set("Najcieplej: --")
            self.stat_min.set("Najzimniej: --")


# ===================================
#  KLASA 3 — cały interfejs graficzny  
# ===================================
class AplikacjaGUI:
    def __init__(self):
        self.dane       = DaneMeteo()
        self.statystyki = Statystyki(self.dane)
        self.funkcja_gui()

    # Tworzenie tabeli 
    def tworzenie_tabeli(self, okno):
        kolumny = (
            "id_stacji", "stacja", "data", "gp", "temp",
            "predkosc_wiatru", "kierunek", "wilgotnosc", "suma_opadu", "cisnienie",
        )
        tabela = ttk.Treeview(okno, columns=kolumny, show="headings")

        tabela.heading("id_stacji", text="ID stacji", anchor="center")
        tabela.heading("stacja",  text="Nazwa stacji",anchor="w")
        tabela.heading("data",  text="Data pomiaru",anchor="center")
        tabela.heading("gp",   text="Godzina", anchor="center")
        tabela.heading("temp",  text="Temp. [°C]",  anchor="center")
        tabela.heading("predkosc_wiatru", text="Wiatr [m/s]", anchor="center")
        tabela.heading("kierunek",   text="Kierunek",  anchor="center")
        tabela.heading("wilgotnosc", text="Wilgotność [%]",anchor="center")
        tabela.heading("suma_opadu", text="Opad [mm]",  anchor="center")
        tabela.heading("cisnienie",  text="Ciśnienie [hPa]", anchor="center")

        tabela.column("id_stacji", width=60,  anchor="center")
        tabela.column("stacja",  width=180, anchor="w")
        tabela.column("data",width=90,  anchor="center")
        tabela.column("gp",width=70,  anchor="center")
        tabela.column("temp",width=80,  anchor="center")
        tabela.column("predkosc_wiatru", width=90,  anchor="center")
        tabela.column("kierunek",width=80,  anchor="center")
        tabela.column("wilgotnosc",width=110, anchor="center")
        tabela.column("suma_opadu",width=80,  anchor="center")
        tabela.column("cisnienie",width=100, anchor="center")

        return tabela

    def wypelnianie_tabeli(self, tabela, dane):
        for i in tabela.get_children():
            tabela.delete(i)
        for rekord in dane:
            tabela.insert("", tk.END, values=(
                rekord.get("id_stacji"),
                rekord.get("stacja"),
                rekord.get("data_pomiaru"),
                rekord.get("godzina_pomiaru"),
                rekord.get("temperatura"),
                rekord.get("predkosc_wiatru"),
                rekord.get("kierunek_wiatru"),
                rekord.get("wilgotnosc_wzgledna"),
                rekord.get("suma_opadu"),
                rekord.get("cisnienie"),
            ))

    def aktualizuj_dane_gui(self, tabela):
        self.dane.aktualizuj_dane()
        dane = self.dane.odczywywanie_danych_offline()
        self.wypelnianie_tabeli(tabela, dane)

    # Filtry 
    def dzialanie_flitrow(self, tryb, zmienna, tabela_pomiarow):
        nazwa = zmienna.get().strip()
        wszystkie_dane = self.dane.odczywywanie_danych_offline()
        przefiltrowane = []
        dni_tygodnia = {
            'poniedziałek': 0, 'wtorek': 1, 'środa': 2, 'czwartek': 3,
            'piatek': 4, 'sobota': 5, 'niedziela': 6,
        }

        if tryb == 1:
            messagebox.showinfo("Status", f"Filtruje po nazwie stacji: {nazwa}")
            for x in wszystkie_dane:
                if nazwa.lower() in x['stacja'].lower():
                    przefiltrowane.append(x)

        elif tryb == 2:
            try:
                if "-" in nazwa[1:]:
                    indeks = nazwa[1:].index("-") + 1
                    min_temp = float(nazwa[:indeks])
                    max_temp = float(nazwa[indeks + 1:])
                    for x in wszystkie_dane:
                        if x['temperatura']:
                            temperatura = float(x['temperatura'])
                            if min_temp <= temperatura <= max_temp:
                                przefiltrowane.append(x)
                elif ">" in nazwa:
                    temperatura = float(nazwa.replace(">", ""))
                    for x in wszystkie_dane:
                        if x['temperatura']:
                            if float(x['temperatura']) > temperatura:
                                przefiltrowane.append(x)
                elif "<" in nazwa:
                    temperatura = float(nazwa.replace("<", ""))
                    for x in wszystkie_dane:
                        if x['temperatura']:
                            if float(x['temperatura']) < temperatura:
                                przefiltrowane.append(x)
                else:
                    temperatura = float(nazwa)
                    for x in wszystkie_dane:
                        if x['temperatura']:
                            if float(x['temperatura']) == temperatura:
                                przefiltrowane.append(x)
            except ValueError:
                messagebox.showerror("Błąd", "Wpisz poprawną wartość liczbową!")

        elif tryb == 3:
            messagebox.showinfo("Status", f"Filtuje po dacie: {nazwa}")
            for x in wszystkie_dane:
                if nazwa in x['data_pomiaru']:
                    przefiltrowane.append(x)

        elif tryb == 4:
            szukany_dzien = nazwa.lower()
            if szukany_dzien not in dni_tygodnia:
                messagebox.showerror("Błąd", f"Nie rozpoznano dnia: '{szukany_dzien}'")
                return
            messagebox.showinfo("Status", f"Filtruję po następującym dniu tygodnia: {szukany_dzien}")
            numer_dnia = dni_tygodnia[szukany_dzien]
            for x in wszystkie_dane:
                try:
                    data = datetime.strptime(x['data_pomiaru'], '%Y-%m-%d')
                    if data.weekday() == numer_dnia:
                        przefiltrowane.append(x)
                except:
                    continue

        elif tryb == 5:
            zmienna.set("")
            przefiltrowane = wszystkie_dane
            messagebox.showwarning("Status", "Wymazano filtry")

        self.wypelnianie_tabeli(tabela_pomiarow, przefiltrowane)
        self.statystyki.laktuaizuj_statystyki_widok(przefiltrowane)

    # Okno statystyk regionalnych 
    def funkcja_okna_statystyk(self):
        obliczone_statystyki = self.statystyki.obliczenia_cisnienia_i_opadow()

        okno_statystyk = tk.Toplevel()
        okno_statystyk.title("Regionalne statystyki opadów i cisnienia")
        okno_statystyk.geometry("600x400")
        okno_statystyk.configure(bg="#f4f4f9")

        kolumny_statystyk = ("region", "suma_opadow", "srednie_cisnienie")
        tabela_statystyk = ttk.Treeview(okno_statystyk, columns=kolumny_statystyk, show="headings")

        tabela_statystyk.heading("region",            text="Region")
        tabela_statystyk.heading("suma_opadow",       text="Suma_opadów [mm]")
        tabela_statystyk.heading("srednie_cisnienie", text="Średnie ciśnienia [hPa]")
        tabela_statystyk.column("region",             anchor="w",      width=200)
        tabela_statystyk.column("suma_opadow",        anchor="center", width=150)
        tabela_statystyk.column("srednie_cisnienie",  anchor="center", width=200)

        tabela_statystyk.pack(expand=True, fill="both", padx=15, pady=15)

        for region, wartosci in obliczone_statystyki.items():
            if region == "Nieznane":
                continue
            suma_opadow   = wartosci["suma_opadow"]
            ile_cisnienia = wartosci["ile_pomiarow_cisnienia"]
            if ile_cisnienia > 0:
                srednie_cisnienie     = wartosci["suma_cisnienia"] / ile_cisnienia
                srednie_cisnienie_str = f"{srednie_cisnienie:.2f}"
            else:
                srednie_cisnienie_str = "Brak danych"

            tabela_statystyk.insert("", tk.END, values=(region, f"{suma_opadow:.2f}", srednie_cisnienie_str))

    # Główne okno aplikacji
    def funkcja_gui(self):
        okno = tk.Tk()
        okno.title("Dane meteorologiczne API")
        okno.geometry("1280x720")
        okno.configure(bg="#f4f4f9")

        # Style
        styl_tla = ttk.Style()
        styl_tla.theme_use('clam')
        styl_tla.configure("Treeview.Heading",
                            font=("Segoe UI", 10, "bold"),
                            background="#2c3e50",
                            foreground="white")
        styl_tla.configure("Treeview", font=("Segoe UI", 9), rowheight=25)
        styl_tla.map("Treeview.Heading", background=[('active', '#34495e')])

        styl_guzikow = ttk.Style()
        styl_guzikow.theme_use('clam')
        styl_guzikow.configure("TButton",
                                font=("Segoe UI", 10),
                                padding=5,
                                background="#E8F5E9")
        styl_guzikow.map("TButton", background=[('active', '#C8E6C9')])



        # Toolbar
        toolbar = tk.Frame(okno, height=60, bg="#ffffff", bd=0,
                           highlightthickness=1, highlightbackground="#d1d1d1")
        toolbar.pack_propagate(False)
        toolbar.pack(side="top", fill="x")

        przycisk_resetu = ttk.Button(toolbar,
                                     text="Aktualizuj dane",
                                     command=lambda: self.aktualizuj_dane_gui(tabela_pomiarow))
        przycisk_resetu.pack(pady=12, padx=20, side="left")

        przycisk_statystyk = ttk.Button(toolbar,
                                        text="Statystyki regionalne",
                                        command=self.funkcja_okna_statystyk)
        przycisk_statystyk.pack(side="right", pady=12, padx=20)



        # Sidebar
        sidebar = tk.Frame(okno, width=240, bg="#ffffff", bd=0,
                           highlightthickness=1, highlightbackground="#d1d1d1")
        sidebar.pack_propagate(False)
        sidebar.pack(side="left", fill="y", padx=(15, 10), pady=15)

        zmienna_nazwy_stacji = tk.StringVar()

        tk.Label(sidebar, text="FILTROWANIE",
                 font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#333").pack(pady=(15, 10))
        tk.Label(sidebar, text="Szukana fraza/wartość:",
                 bg="#ffffff", font=("Segoe UI", 9)).pack(anchor="center", padx=15)

        pole_tekstowe_nazwy_stacji = ttk.Entry(sidebar,
                                               textvariable=zmienna_nazwy_stacji,
                                               font=("Segoe UI", 10))
        pole_tekstowe_nazwy_stacji.pack(fill="x", padx=15, pady=(5, 15))

        przycisk_szukaj = ttk.Button(
            sidebar, text="Szukaj po nazwie",
            command=lambda: self.dzialanie_flitrow(1, zmienna_nazwy_stacji, tabela_pomiarow))
        przycisk_szukaj.pack(fill="x", padx=15, pady=3)

        przycisk_szukania_po_temp = ttk.Button(
            sidebar, text="Szukaj po temperaturze",
            command=lambda: self.dzialanie_flitrow(2, zmienna_nazwy_stacji, tabela_pomiarow))
        przycisk_szukania_po_temp.pack(fill="x", padx=15, pady=3)

        przycisk_szukania_po_dacie = ttk.Button(
            sidebar, text="Szukaj po dacie (rozdziel '-')",
            command=lambda: self.dzialanie_flitrow(3, zmienna_nazwy_stacji, tabela_pomiarow))
        przycisk_szukania_po_dacie.pack(fill="x", padx=15, pady=3)

        przycisk_szukaj_po_dniu = ttk.Button(
            sidebar, text="Szukaj po dniu",
            command=lambda: self.dzialanie_flitrow(4, zmienna_nazwy_stacji, tabela_pomiarow))
        przycisk_szukaj_po_dniu.pack(fill="x", padx=15, pady=3)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15, pady=15)

        przycisk_wyczysc_filtry = ttk.Button(
            sidebar, text="Wyczyść filtry",
            command=lambda: self.dzialanie_flitrow(5, zmienna_nazwy_stacji, tabela_pomiarow))
        przycisk_wyczysc_filtry.pack(fill="x", padx=15, pady=3)

        ramka_statystyk = tk.Frame(okno, bg="#ffffff", bd=0,
                                   highlightthickness=1, highlightbackground="#d1d1d1")
        ramka_statystyk.pack(side="top", fill="x", padx=(0, 15), pady=(15, 10))

        self.statystyki.stat_liczba  = tk.StringVar(value="Liczba stacji: 0")
        self.statystyki.stat_srednia = tk.StringVar(value="Średnia temp: --")
        self.statystyki.stat_max     = tk.StringVar(value="Najcieplej: --")
        self.statystyki.stat_min     = tk.StringVar(value="Najzimniej: --")

        naglowek = tk.Label(ramka_statystyk, text="PODSUMOWANIE",
                            font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#333")
        naglowek.pack(side="left", padx=15, pady=15)

        tk.Label(ramka_statystyk, textvariable=self.statystyki.stat_liczba,
                 font=("Segoe UI", 10), bg="#ffffff").pack(side="left", padx=(10, 20))
        tk.Label(ramka_statystyk, textvariable=self.statystyki.stat_srednia,
                 font=("Segoe UI", 10), bg="#ffffff").pack(side="left", padx=20)
        tk.Label(ramka_statystyk, textvariable=self.statystyki.stat_max,
                 fg="#d9534f", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(side="left", padx=20)
        tk.Label(ramka_statystyk, textvariable=self.statystyki.stat_min,
                 fg="#0275d8", font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(side="left", padx=20)

        ramka_tabeli = tk.Frame(okno, bg="#ffffff", bd=0,
                                highlightthickness=1, highlightbackground="#d1d1d1")
        ramka_tabeli.pack(expand=True, fill="both", padx=(0, 15), pady=(0, 15))

        tabela_pomiarow = self.tworzenie_tabeli(ramka_tabeli)
        tabela_pomiarow.pack(expand=True, fill="both", padx=5, pady=5)

        # Inicjalizacja danych przy starcie
        dane_startowe = self.dane.odczywywanie_danych_offline()
        self.wypelnianie_tabeli(tabela_pomiarow, dane_startowe)
        self.statystyki.aktualizuj_statystyki_widok(dane_startowe)

        okno.mainloop()

if __name__ == "__main__":
    AplikacjaGUI()