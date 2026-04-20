# SUPPORT PLAYBOOK (Long-term)

Tikslas: užtikrinti stabilų PRB Tools vystymą mėnesiais/metais, net kai klaidos pasirodo tik po ilgo naudojimo.

## 1) Klaidos registravimo minimumas
Kiekvienai klaidai fiksuoti:
- Data/laikas
- Revit versija
- Aktyvus paketas (Core/MEP/ARCH)
- Mygtukas/funkcija
- Veiksmai iki klaidos (1-2-3)
- Klaidos tekstas / screenshot
- Ar pavyksta pakartoti (taip/ne)

## 2) Prioritetai
- P0: stabdo darbą / prarandami duomenys
- P1: kritiškai lėtina darbą
- P2: apeinama kliūtis
- P3: UX patobulinimas

## 3) Pataisymo procesas
1. Atkurti klaidą testinėje byloje.
2. Įtraukti pataisą su minimaliu rizikos plotu.
3. Pridėti trumpą regresijos testą (manual checklist).
4. Atnaujinti TOOLS_KNOWLEDGE_BASE.md.
5. Išleisti naują paketą ir trumpą changelog.

## 4) Release disciplina
- Vieninga versija visiems 3 paketams (Core/MEP/ARCH).
- Kiekvienas release turi:
  - ZIP failą
  - instaliavimo instrukciją
  - funkcijų aprašų dokumentą
  - CHANGELOG įrašą

## 5) Rollback strategija
- Visada laikyti paskutinį stabilų ZIP.
- Jei nauja versija lūžta, grįžti į paskutinį stabilų paketą.
- ParameterTransformer rollback log naudoti duomenų atstatymui.
