# 🕹️ Finałowa Weryfikacja: Gry Flash w Kolekcji (315 plików)

Po dokładnej deasemblacji kodu bajtowego ActionScript, drzew tagów oraz zmiennych we wszystkich 154 plikach SWF, weryfikacja wykazała:

## 🏆 Jedyna autentyczna, grywalna gra Flash:
### **Snake Arena 1.0 by TALEE**
- **Plik:** `20030408_snakearena.swf` (74.3 KB)
- **Data archiwalna:** 8 kwietnia 2003 r.
- **Autor:** TALEE (`talee@mat.uni.torun.pl`, Wydział Matematyki i Informatyki UMK w Toruniu)
- **Pochodzenie:** `http://a1t2.republika.pl/flashki/snakearena[1].swf`
- **Tryby gry:**
  - **Single Player:** klasyczny wąż z naliczaniem punktów (`normalScore`, `impressiveScore`, `excellentScore`).
  - **Multiplayer na 1 klawiaturze:** rywalizacja dwóch węży jednocześnie (`snake1` vs `snake2`, wykrywanie kolizji, wygrana gracza 1 lub 2).
  - **Efekty:** Sample i animacje wzorowane na Quake/Unreal (`Impressive!`, `Excellent!`).

---

## ❌ Pliki błędnie sklasyfikowane wcześniej (FAŁSZYWE ALARMY):
1. **`20041222_akwariumjacka.swf`** – to **animowany preloader / intro** (124 klatki animacji), a nie gra interaktywna.
2. **`20041025_gra.swf`** (4.4 KB) – mimo nazwy „gra”, to stary plik Flash 3 zawierający 47 klatek wektorowej pętli bez linijki kodu ActionScript (DoAction: 0).
3. **`20041128_adam3,1.swf`** – to menu portfolio wczytujące podstrony (`druki.swf`, `kontakt.swf`), a nie gra typu point & click.
4. **`20030818_index.swf`** – strona powitalna (splash screen) ładująca sondę (`sonda.swf`), a nie gra lochowa.
