# PRB Revit Tools – Pilnas funkcijų katalogas (FINAL)

Atnaujinimo principas: šis katalogas yra „single source of truth“ failas. Toliau jis bus tik perrašomas ant viršaus nauja versija, išlaikant tą patį pavadinimą.

## 1. Produkto apžvalga

PRB Revit Tools paketas skirtas pagreitinti kasdienius BIM/MEP darbus:
- automatinis žymėjimas ir tagų valdymas,
- sheet/view generavimas,
- parametrų ir NSIK kodavimo automatizavimas,
- eksporto ir atnaujinimo workflow.

## 2. Struktūra pagal panelius

- **Tags.panel**: AutoTag, AlignTags, TagRules
- **Sheets.panel**: AutoSheet, BatchRename
- **Views.panel**: AutoSection
- **Dimensions.panel**: AutoDim
- **Export.panel**: SmartExport
- **NSIK.panel**: AutoCoder, LearnRules, ParameterTransformer
- **Nustatymai.panel**: Atnaujinti, Pagalba

---

## 3. Įrankių funkcijos su integruotomis ikonomis

### 3.1 AutoTag (Tags.panel)
![AutoTag](../icon_redesign_preview_2026-04-22/AutoTag_icon_v2.png){ width=0.9in }
- Paskirtis: automatiškai sužymėti MEP elementus aktyviame projekte.
- Ką gali:
  - žymėti kelias kategorijas (pipes, ducts, cable trays, equipment),
  - pasirinkti tag tipą kiekvienai kategorijai,
  - žymėti pagal scope (pažymėti elementai arba visi vaizde),
  - taikyti orientaciją, offset ir dublikatų valdymą,
  - naudoti anti-overlap (tagų susikirtimų prevencija),
  - naudoti sąlyginį žymėjimą pagal sistemą/debitą,
  - naudoti grupinį režimą (multi-leader bandymas, kai palaikoma).
- Kada naudoti: kai reikia greitai sužymėti daug elementų su vieninga logika.

### 3.2 AlignTags (Tags.panel)
![AlignTags](../icon_redesign_preview_2026-04-22/AlignTags_icon_v2.png){ width=0.9in }
- Paskirtis: sulygiuoti jau esamus pažymėtus tagus.
- Workflow:
  1) pažymi bent 2 tagus,
  2) pasirenki Horizontalų arba Vertikalų lygiavimą,
  3) pasirenki bazę: pagal pirmą pažymėtą arba pagal vidurkį.
- Kada naudoti: kai vaizde tagai išsibarstę po rankinių pataisymų.

### 3.3 TagRules (Tags.panel)
![TagRules](../icon_redesign_preview_2026-04-22/TagRules_icon_v2.png){ width=0.9in }
- Paskirtis: valdyti System -> Tag taisykles AutoTag įrankiui.
- Ką gali:
  - peržiūrėti taisykles,
  - pridėti naują taisyklę (kategorija + sistemos tekstas + tag tipas + prioritetas),
  - ištrinti taisyklę,
  - įjungti/išjungti taisyklę (ON/OFF).
- Kada naudoti: kai skirtingoms sistemoms reikia skirtingų tag tipų.

### 3.4 AutoSheet (Sheets.panel)
![AutoSheet](../icon_redesign_preview_2026-04-22/AutoSheet_icon_v2.png){ width=0.9in }
- Paskirtis: generuoti view + sheet paketus pagal aukštus/sistemas/zonas.
- Ką daro:
  - kuria plan views pagal pasirinktą ViewFamilyType,
  - optional: skirsto pagal sistemas ir Scope Boxes (zonas),
  - optional: pritaiko View Template,
  - optional: kuria sheets, numeruoja, deda view ant lapo.
- Pastaba: v1 sistemų skirstymas orientuotas į naming/paketų kūrimą; detalūs per-view MEP filtrai planuojami v2.

### 3.5 BatchRename (Sheets.panel)
![BatchRename](../icon_redesign_preview_2026-04-22/BatchRename_icon_v2.png){ width=0.9in }
- Paskirtis: masiškai pervadinti sheets.
- Ką daro: randa tekstą pavadinimuose ir pakeičia nauju.
- Kada naudoti: kai keičiasi projekto naming taisyklės.

### 3.6 AutoSection (Views.panel)
![AutoSection](../icon_redesign_preview_2026-04-22/AutoSection_icon_v2.png){ width=0.9in }
- Paskirtis: greitesnis sekcijų kūrimas pagal pasirinktą logiką.
- Naudojimas: kai reikia serijiniu būdu kurti daug pjūvių.

### 3.7 AutoDim (Dimensions.panel)
![AutoDim](../icon_redesign_preview_2026-04-22/AutoDim_icon_v2.png){ width=0.9in }
- Paskirtis: automatinis matmenų dėjimas pagal taisykles.
- Naudojimas: kai reikia paspartinti pasikartojančių matmenų žymėjimą.

### 3.8 SmartExport (Export.panel)
![SmartExport](../icon_redesign_preview_2026-04-22/SmartExport_icon_v2.png){ width=0.9in }
- Paskirtis: centralizuotas modelio/duomenų eksportas pagal įmonės workflow.
- Pastaba: priklauso nuo projekto konfigūracijos ir eksporto scenarijų.

### 3.9 AutoCoder (NSIK.panel)
![AutoCoder](../icon_redesign_preview_2026-04-22/AutoCoder_icon_v2.png){ width=0.9in }
- Paskirtis: automatinis NSIK kodų priskyrimas pagal mapping taisykles.
- Šaltinis: `mapping.json` taisyklės (kategorija/šeima -> kodai).
- Kada naudoti: kai reikia vienodo klasifikavimo per visą modelį.

### 3.10 LearnRules (NSIK.panel)
![LearnRules](../icon_redesign_preview_2026-04-22/LearnRules_icon_v2.png){ width=0.9in }
- Paskirtis: „išmokti“ NSIK taisykles iš esamo modelio ir atnaujinti mapping.
- Ką daro: nuskaito elementus su NSIK reikšmėmis ir papildo AutoCoder mapping.
- Kada naudoti: kai modelyje jau turi gerų pavyzdžių ir nori juos paversti taisyklėmis.

### 3.11 ParameterTransformer (NSIK.panel)
![ParameterTransformer](../icon_redesign_preview_2026-04-22/ParameterTransformer_icon_v2.png){ width=0.9in }
- Paskirtis: masinis parametrų redagavimas su Excel roundtrip.
- Režimai:
  - Export -> CSV/XLSX,
  - Import <- CSV/XLSX,
  - Rollback <- LOG.
- Workflow:
  1) pasirenki kategorijas + filtrus,
  2) eksportuoji parametrus į lentelę,
  3) redaguoji Excel'e,
  4) importuoji atgal (su preview),
  5) jei reikia, atstatai pakeitimus iš rollback JSON log.
- Kada naudoti: standartizavimui, numeracijai ir dideliems parametrų pakeitimams.

### 3.12 Atnaujinti (Nustatymai.panel)
![Atnaujinti](../icon_redesign_preview_2026-04-22/Atnaujinti_icon_v2.png){ width=0.9in }
- Paskirtis: atsinaujinti visą PRB Tools rinkinį (Core + MEP + ARCH) iš repozitorijos.
- Kada naudoti: po naujų funkcijų ar klaidų pataisymų bet kuriame rinkinio modulyje.

### 3.13 Pagalba (Nustatymai.panel)
![Pagalba](../icon_redesign_preview_2026-04-22/Pagalba_icon_v2.png){ width=0.9in }
- Paskirtis: vienoje vietoje pateikti įrankių aprašus naudotojui.
- Kada naudoti: kai reikia greitos funkcijų atmintinės prieš paleidžiant įrankį.

---

## 4. Techniniai duomenys

- Ikonos: PNG, 96x96, RGBA, pritaikytos pyRevit `icon.png` formatui.
- Katalogo paskirtis: produktinė dokumentacija ir vidinis pardavimo/įdiegimo aprašas.
- Atnaujinimo taisyklė: visada atnaujinti tą patį failą (`PRB_Revit_Tools_Katalogas_FINAL.docx`) perrašant ant viršaus.
