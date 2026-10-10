# Selektor Zdjęć

Program na macOS do szybkiego przeglądania i selekcjonowania zdjęć oraz dodawania daty na zdjęciach.

Repozytorium (kopia zapasowa): https://github.com/thepianosup/SELEKTOR-ZDJEC

## Do czego służy program

Masz duży folder ze zdjęciami i chcesz wybrać tylko najlepsze? Ten program Ci w tym pomoże. Przejrzyj zdjęcie po zdjęciu i zdecyduj jednym przyciskiem, czy zostaje, czy leci do kosza. Dodatkowo możesz włączyć nakładkę z datą wykonania zdjęcia, która zostanie trwale wklejona na wybrane zdjęcia.

## Jak korzystać z programu

### Krok 1: Wybierz foldery

1. Kliknij **„Wybierz folder źródłowy"** – wskaż folder, w którym są Twoje zdjęcia.
2. Kliknij **„Wybierz folder docelowy"** – wskaż folder, do którego mają trafić wybrane zdjęcia.

Program pokazuje zdjęcia posortowane wg daty wykonania. Zdjęcia, które już są w folderze docelowym, są automatycznie pomijane.

### Krok 2: Oglądaj i wybieraj

- **Strzałka w PRAWO** – kopiuj zdjęcie do folderu docelowego i przejdź do następnego.
- **Strzałka w LEWO** – odrzuć zdjęcie i przejdź do następnego.
- **CMD + Z** – cofnij ostatnią decyzję (usunięcie skopiowanego zdjęcia lub przywrócenie odrzuconego).

U góry widzisz licznik: ile zdjęć zostało do wyboru, ile dodano, a ile odrzucono. Żółty pasek ostrzega, że w kolejce są zdjęcia podobne (zrobione w krótkim odstępie czasu).

### Krok 3: Dodawanie daty na zdjęciu (opcjonalnie)

1. Kliknij jedno z czterech pól po lewej stronie (układ 2x2), aby wybrać róg zdjęcia, w którym ma pojawić się data.
2. Data pojawi się jako podgląd na zdjęciu.
3. Możesz ją **przeciągnąć myszką** w dowolne miejsce oraz **powiększyć/pomniejszyć**, ciągnąc za okrągły uchwyt w prawym dolnym rogu ramki.
4. Kliknij ten sam róg ponownie, aby wyłączyć datę.

Data jest odczytywana z metadanych zdjęcia (EXIF). Jeśli zdjęcie nie ma metadanych, program użyje daty ostatniej modyfikacji pliku. Data zostanie wklejona na zdjęcie trwale – dopiero podczas kopiowania (strzałka w prawo).

### Obrót zdjęcia

- **Strzałka w GÓRĘ** – obróć zdjęcie o 90° w prawo.
- **Strzałka w DÓŁ** – obróć zdjęcie o 90° w lewo.

Obrót zapisuje się bezpośrednio w pliku w folderze źródłowym.

### Resetowanie historii

Kliknij **„Resetuj historię"**, aby zacząć od nowa – program zapomni, które zdjęcia już były wybrane lub odrzucone, i pokaże je ponownie.

## Ściągawka – skróty klawiszowe

| Klawisz | Działanie |
|---|---|
| → | Kopiuj zdjęcie do folderu docelowego |
| ← | Odrzuć zdjęcie |
| ↑ | Obróć o 90° w prawo |
| ↓ | Obróć o 90° w lewo |
| CMD + Z | Cofnij ostatnią decyzję |

## Wspierane formaty

JPG, JPEG, PNG oraz HEIC (jeśli system potrafi je otworzyć).

## Ważne informacje o działaniu

- Program zapamiętuje stan pracy w pliku `state.json` (tworzy go w miejscu uruchomienia) – po zamknięciu i ponownym uruchomieniu kontynuujesz od tego samego miejsca.
- Wybrane zdjęcia są **kopiowane**, nie przenoszone – oryginały pozostają w folderze źródłowym.
- Aplikacja działa na macOS.

---

# Część techniczna – odtwarzanie projektu z GitHuba

Ten projekt może zostać usunięty z dysku, a kopią zapasową jest repozytorium na GitHubie. Poniżej opisano, jak w razie potrzeby odtworzyć go od zera i jak zbudować aplikację `.app` oraz instalator `.dmg` (te pliki celowo nie są w repozytorium, bo można je wygenerować w każdej chwili).

## Wymagania

- macOS
- Python 3.13 (testowane na 3.13.5)
- Biblioteki: PyQt6 (testowane 6.11.0), Pillow (testowane 12.2.0)
- Do zbudowania aplikacji: PyInstaller (testowane 6.20.0)

## Krok 1: Pobranie projektu z GitHuba

```bash
git clone https://github.com/thepianosup/SELEKTOR-ZDJEC.git
cd SELEKTOR-ZDJEC
```

## Krok 2: Uruchomienie programu ze źródeł

```bash
python3 -m venv venv
source venv/bin/activate
pip install PyQt6 Pillow
python main.py
```

## Krok 3: Zbudowanie aplikacji .app (opcjonalnie)

```bash
source venv/bin/activate
pip install pyinstaller
pyinstaller --windowed --name "Selektor Zdjec" --icon appIcon.icns main.py
```

Gotowa aplikacja pojawi się w folderze `dist/Selektor Zdjec.app`.

## Krok 4: Zbudowanie instalatora .dmg (opcjonalnie)

```bash
hdiutil create -volname "Selektor Zdjec" -srcfolder "dist/Selektor Zdjec.app" -ov -format UDZO "Selektor_Zdjec.dmg"
```

## Zawartość repozytorium

| Plik | Opis |
|---|---|
| `main.py` | Cały kod programu – to jedyny plik potrzebny do uruchomienia. |
| `appIcon.icns` | Ikona aplikacji, potrzebna do zbudowania `.app`. |
| `.gitignore` | Lista plików wykluczonych z repozytorium. |
| `README.md` | Ten plik – instrukcja obsługi i informacje o projekcie. |
| `patch_script.py`, `patch2.py` | Historyczne skrypty, których użyto podczas tworzenia programu do modyfikacji `main.py`. Nie są potrzebne do uruchomienia – `main.py` zawiera już wszystkie ich poprawki. |

## Czego nie ma w repozytorium (i co przepadnie po usunięciu folderu)

Te pliki są wykluczone przez `.gitignore`, ponieważ można je łatwo odtworzyć:

- `venv/` – wirtualne środowisko (odtworzysz je komendą z kroku 2),
- `Selektor Zdjec.app/` i `*.dmg` – gotowa aplikacja i instalator (odtworzysz je krokami 3 i 4),
- `state.json` – postęp bieżącej sesji selekcji zdjęć (nie jest częścią projektu),
- `.DS_Store` – śmieci systemowe macOS.
