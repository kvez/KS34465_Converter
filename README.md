# KS34465_Converter – KS34465 CSV konverter

A KS34465 mérőprogram kimeneti CSV fájljait konvertálja a **HP3458A_Analyzer** által
várt formátumra. A program elsősorban a **DMM_34465A** zajmérési munkafolyamatának
közbülső lépése: lehetővé teszi, hogy a Keysight 34465A multiméterrel rögzített
mérési sorozatok ugyanolyan zajanalízisen essenek át, mint a HP 3458A-val rögzítettek.

## Mérési munkafolyamat

```
DMM_34465A  →  KS34465_Converter  →  HP3458A_Analyzer
 (mérés)        (formátum-átalakítás)   (zajspektrum elemzés)
```

| Lépés | Program | Szerep |
|-------|---------|--------|
| 1. Mérés | **DMM_34465A** | Idősorozat rögzítése KS34465 CSV formátumba |
| 2. Átalakítás | **KS34465_Converter** | CSV konvertálása az Analyzer formátumára |
| 3. Elemzés | **HP3458A_Analyzer** | LPSD / Allan deviáció / drift / SFDR |

## Bemeneti formátum (KS34465, pontosvessző elválasztó, vesszős tizedes)

```
"index";"time";"minutes";"dateTime";"K34465.VoltageDC";"Math.Power"
0;0,075;...;1778918811,434;10,0196568;0
```

## Kimeneti formátum (HP3458A_Analyzer)

```
# HP 3458A NPLC Logger
# Fs: XX.XX SPS
sample_index,voltage_V
0,+1.001956456e+01
```

## Funkciók

- Több fájl kötegelt konvertálása
- Mérési metaadat megadása (tartomány V, NPLC, megjegyzés)
- Kimeneti fájlnév előtag és utótag beállítható
- Automatikus mintavételi frekvencia (Fs) számítás az időoszlopból

## Követelmények

- Python 3.11+
- Nincs külső pip csomag szükséges

## Futtatás

```bat
python ks34465_converter.py
```

## Build (önálló exe)

```bat
build.bat
```

Kimenet: `dist\KS34465_Converter.exe`
