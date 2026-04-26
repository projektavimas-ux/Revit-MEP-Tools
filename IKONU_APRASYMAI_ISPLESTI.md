# Revit Tools ikonų rinkinys – išplėstas aprašymas

> Integruota v2 ikonų versija peržiūrai prieš galutinį įdiegimą į programą.

## 1) Bendras rinkinio vaizdas

![Visų ikonų peržiūra](icon_redesign_preview_2026-04-22/all_icons_preview.png)

## 2) Dizaino kryptis

- Vieningas vizualinis stilius visiems mygtukams (gradientinė kortelė + balti simboliai).
- Aiškūs, greitai atpažįstami simboliai 96x96 mastelyje.
- Skirtingoms funkcijų grupėms parinktos atskiros spalvų nuotaikos:
  - Tags: violetinė
  - NSIK/parametrai: mėlyna–turkio
  - Nustatymai: mėlynai pilka
  - Sheets: žalia
  - Views/Dimensions/Export: oranžinė, raudona, žydra

## 3) Ikonos pagal įrankį (išplėstiniai aprašai)

### AutoTag
![AutoTag](icon_redesign_preview_2026-04-22/AutoTag_icon_v2.png)
- Funkcija: automatinis MEP elementų taginimas pagal pasirinktas taisykles.
- Ikonos logika: tag forma + automatikos akcentas (žvaigždutė/„spark“).
- UX tikslas: greitai suprasti, kad tai masinis, automatizuotas žymėjimas.

### AlignTags
![AlignTags](icon_redesign_preview_2026-04-22/AlignTags_icon_v2.png)
- Funkcija: pažymėtų tagų lygiavimas horizontal/vertical.
- Ikonos logika: dvi tag kortelės ir aiški lygiavimo ašis.
- UX tikslas: vizualiai parodyti „sulygiuoti“ veiksmą vienu žvilgsniu.

### TagRules
![TagRules](icon_redesign_preview_2026-04-22/TagRules_icon_v2.png)
- Funkcija: System -> Tag taisyklių kūrimas/valdymas.
- Ikonos logika: check-list tipo taisyklių vaizdavimas.
- UX tikslas: iškart atskirti nuo AutoTag (vykdymo) funkcijos.

### AutoSection
![AutoSection](icon_redesign_preview_2026-04-22/AutoSection_icon_v2.png)
- Funkcija: sekcijų kūrimas pagal parinktą logiką.
- Ikonos logika: pjūvio kryptis ir sekcijos geometrijos užuomina.
- UX tikslas: suteikti aiškų ryšį su pjūviais/section įrankiu.

### AutoDim
![AutoDim](icon_redesign_preview_2026-04-22/AutoDim_icon_v2.png)
- Funkcija: automatizuotas matmenų dėjimas.
- Ikonos logika: klasikinė dimensijos rodyklių schema.
- UX tikslas: išlaikyti CAD/BIM vartotojams pažįstamą simboliką.

### SmartExport
![SmartExport](icon_redesign_preview_2026-04-22/SmartExport_icon_v2.png)
- Funkcija: centralizuotas eksporto paleidimas.
- Ikonos logika: dokumentas/duomenys + kryptinė „output“ rodyklė.
- UX tikslas: aiškiai komunikuoti „išvežimo“/eksporto veiksmą.

### AutoSheet
![AutoSheet](icon_redesign_preview_2026-04-22/AutoSheet_icon_v2.png)
- Funkcija: sheet/view kūrimas su automatika.
- Ikonos logika: lapas ir automatizavimo akcentas.
- UX tikslas: aiškiai atpažįstamas sheet kūrimo mygtukas.

### BatchRename
![BatchRename](icon_redesign_preview_2026-04-22/BatchRename_icon_v2.png)
- Funkcija: masinis pervadinimas.
- Ikonos logika: A/B kortelės su pervadinimo kryptimi.
- UX tikslas: parodyti, kad keitimas vyksta „iš vieno į kitą“ masiškai.

### AutoCoder
![AutoCoder](icon_redesign_preview_2026-04-22/AutoCoder_icon_v2.png)
- Funkcija: NSIK kodų priskyrimas pagal mapping.
- Ikonos logika: „code“ simbolika su klasifikavimo ženklu.
- UX tikslas: iškart matomas ryšys su kodavimu ir taisyklėmis.

### LearnRules
![LearnRules](icon_redesign_preview_2026-04-22/LearnRules_icon_v2.png)
- Funkcija: taisyklių mokymasis iš modelio duomenų.
- Ikonos logika: lemputė (mokymasis/įžvalga) + taisyklių linijos.
- UX tikslas: atskirti nuo AutoCoder kaip „mokymo“ etapą.

### ParameterTransformer
![ParameterTransformer](icon_redesign_preview_2026-04-22/ParameterTransformer_icon_v2.png)
- Funkcija: parametrų transformavimas/import-export/rollback.
- Ikonos logika: transformacijos kryptys + valdymo juosta.
- UX tikslas: signalizuoti duomenų konvertavimo/pakeitimo veiksmą.

### Atnaujinti
![Atnaujinti](icon_redesign_preview_2026-04-22/Atnaujinti_icon_v2.png)
- Funkcija: paketo atnaujinimas/reload.
- Ikonos logika: refresh ciklas su rodykle.
- UX tikslas: klasikinis „update“ atpažinimas be papildomo teksto.

### Pagalba
![Pagalba](icon_redesign_preview_2026-04-22/Pagalba_icon_v2.png)
- Funkcija: įrankių aprašų/pagalbos atidarymas.
- Ikonos logika: klausimo simbolis saugiame apskritimo konteineryje.
- UX tikslas: universali, iškart suprantama help semantika.

## 4) Techninė pastaba

- Visi failai paruošti 96x96 PNG (RGBA), tinkami pyRevit `icon.png` naudojimui.
- Šiame etape tai peržiūros variantas; į aktyvius mygtukus integruosiu po galutinio patvirtinimo.

## 5) Failų lokacijos

- Ikonų katalogas: `projects/Revit_MEP_Tools/icon_redesign_preview_2026-04-22/`
- Išplėstas aprašas: `projects/Revit_MEP_Tools/IKONU_APRASYMAI_ISPLESTI.md`
