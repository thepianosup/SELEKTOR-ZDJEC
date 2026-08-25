# Selektor Zdjęć

Program do szybkiego przeglądania i selekcjonowania zdjęć oraz dodawania daty na zdjęciach.

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

## Wymagania

- Python 3
- Biblioteki: `PyQt6`, `Pillow`

Uruchomienie:

```
pip install PyQt6 Pillow
python main.py
```

## Wspierane formaty

JPG, JPEG, PNG oraz HEIC (jeśli system potrafi je otworzyć).

## Ważne

- Program zapamiętuje stan pracy w pliku `state.json` – po zamknięciu i ponownym uruchomieniu kontynuujesz od tego samego miejsca.
- Wybrane zdjęcia są **kopiowane**, nie przenoszone – oryginały pozostają w folderze źródłowym.
