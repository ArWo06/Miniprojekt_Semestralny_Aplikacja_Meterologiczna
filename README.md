## Miniprojekt_Semestralny_Aplikacja_Meterologiczna
Repozytorium zawierające miniprojekt semestralny aplikacji pogodowej z graficznym interfejsem użytkownika pobierająca dane w czasie rzeczywistym z publicznego API IMGW napisana w Python.


## Opis projektu
  Aplikacja umożliwia pobieranie, przeglądanie i analizowanie danych meteorologicznych ze stacji synoptycznych w Polsce. Dane są pobierane z API IMGW i przechowywane lokalnie w pliku JSON, dzięki czemu aplikacja działa również offline (na wcześniej pobranych danych). Projekt napisany jest za pomocą programowania obiektowego z podziałem na trzy klasy odpowiadające za osobne warstwy aplikacji.

## Funkcje:
- Pobieranie aktualnych danych pogodowych z API IMGW (dane synoptyczne)
- Lokalny zapis historii pomiarów w pliku `pogoda_historia.json` bez duplikatów
- Wyświetlanie danych w czytelnej tabeli z 10 kolumnami (ID, stacja, data, godzina, temperatura, wiatr, kierunek, wilgotność, opad, ciśnienie)
- Filtrowanie danych po:
  - nazwie stacji (wyszukiwanie tekstowe)
  - temperaturze (dokładna wartość, zakres np. `5-20`, lub operatory `>10`, `<0`)
  - dacie (format `YYYY-MM-DD`)
  - dniu tygodnia (np. `poniedziałek`)
- Podsumowanie statystyczne dla wyfiltrowanych danych: liczba stacji, średnia temperatura, najcieplejsza i najzimniejsza stacja
- Okno statystyk regionalnych — suma opadów i średnie ciśnienie pogrupowane według województw

Źródło danych meterologicznych: https://danepubliczne.imgw.pl/api/data/synop
