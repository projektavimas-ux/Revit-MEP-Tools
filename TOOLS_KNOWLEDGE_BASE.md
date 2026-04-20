# PRB Tools Knowledge Base (Long-Term)

_Paskirtis:_ ilgalaikė įrankių atmintis, kad nereikėtų kaskart iš naujo aptarinėti tų pačių funkcijų.

## Struktūra

- **PRB_Core.extension** → bendriniai įrankiai (CORE.tab)
- **PRB_MEP.extension** → MEP specifika (MEP_Tools.tab)
- **PRB_ARCH.extension** → ARCH specifika (ARCH_Tools.tab)

## Core (CORE.tab)

### Nustatymai.panel
- **Atnaujinti**: paketo atsinaujinimas / reload logika.
- **Pagalba**: funkcijų aprašų peržiūra.

### Sheets.panel
- **AutoSheet (v1)**:
  - kuria views/sheets pagal aukštus/sistemas/zonas,
  - taiko view template,
  - automatinė sheet numeracija ir viewport padėjimas.
- **BatchRename**:
  - masinis sheet pavadinimų/pervadinimo scenarijus.

### Views.panel
- **AutoSection**:
  - sekcijų kūrimo automatizavimo paruoštukas (toliau plėsti).

### Dimensions.panel
- **AutoDim**:
  - matmenų automatizavimo paruoštukas (toliau plėsti).

### Export.panel
- **SmartExport**:
  - centralizuotas eksporto scenarijų mygtukas (toliau plėsti pagal įmonės workflow).

## MEP (MEP_Tools.tab)

### Tags.panel
- **AutoTag**:
  - kategorijų/tag tipų parinkimas,
  - anti-overlap,
  - conditional tagging,
  - multi-leader bandymas,
  - System->Tag taisyklių panaudojimas.
- **AlignTags**:
  - pažymėtų tagų lygiavimas horizontaliai/vertikaliai.
- **TagRules**:
  - System->Tag taisyklių valdymas (pridėti/trinti/ON-OFF/peržiūra).
- **system_tag_rules.json**:
  - taisyklių failas AutoTag logikai.

### NSIK.panel
- **AutoCoder**: NSIK kodavimo taikymas pagal mapping.
- **LearnRules**: NSIK taisyklių mokymasis iš modelio.
- **ParameterTransformer (v2)**:
  - Export CSV/XLSX,
  - Import CSV/XLSX su preview,
  - Rollback iš log.

## ARCH (ARCH_Tools.tab)

### Info.panel
- **ArchRoadmap**:
  - laikinas informacinis mygtukas,
  - vieta būsimam ARCH funkcionalui.

## Priimti architektūriniai sprendimai

1. UI atskyrimas pagal disciplinas:
   - Core = bendriniai mygtukai,
   - MEP = MEP specifika,
   - ARCH = ARCH specifika.
2. Bendras branduolys (`prb_core`) skirtas pernaudojimui ir vieningam atnaujinimui.
3. Instaliacija daroma 3 extension katalogais vienu metu.

## Instaliavimo paketo taisyklė

ZIP turi po išarchyvavimo į `C:\` sukurti tiesiogiai:
- `C:\PRB_Core.extension`
- `C:\PRB_MEP.extension`
- `C:\PRB_ARCH.extension`

Be papildomų wrapper katalogų.

## Mainų srities failų taisyklė (kritinė)

Visi vartotojui perduodami failai privalo būti kopijuojami į:
- `C:\OpenClawShare\Mainu_sritis\...`

Ubuntu keliai naudotojui nėra pirminis perdavimo kanalas.

## Tolimesni darbai (prioritetai)

1. AutoSheet v2: realūs sisteminiai filtrai (ne tik naming).
2. ARCH disciplinos mygtukų įdiegimas (View/Sheet, QA, Parameter Transformer ARCH).
3. Core updateris su aiškiu version manifest.
4. Vieningas changelog ir release šablonas.
