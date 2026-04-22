# AutoDim research ir patobulinimo santrauka (2026-04-22)

## Tikslas
Išplėsti AutoDim iš „placeholder“ į realų įrankį su disciplinos pasirinkimu ir skirtingais matmenų grandinėlių režimais.

## Peržiūrėti analogai ir API šaltiniai

1. Revit API Docs – `Document.Create.NewDimension(View, Line, ReferenceArray)`
   - https://www.revitapidocs.com/2023/47b3977d-da93-e1a4-8bfa-f23a29e5c4c1.htm
   - Esminė išvada: reikia geometrinių `Reference` objektų; neteisingi reference sukelia `ArgumentException`.

2. Autodesk Revit API Developer Guide – Dimensions and Constraints
   - https://help.autodesk.com/cloudhelp/2024/ITA/Revit-API/files/Revit_API_Developers_Guide/Revit_Geometric_Elements/Annotation_Elements/Revit_API_Revit_API_Developers_Guide_Revit_Geometric_Elements_Annotation_Elements_Dimensions_and_Constraints_html.html
   - Esminė išvada: `NewDimension` kuria linear dimensijas; dimensijos yra view-specific; `OST_Dimensions` kategorija.

3. The Building Coder – grid/rebar dimensioning reference gavimas
   - https://jeremytammik.github.io/tbc/a/1684_rebar_dimension.html
   - Esminė išvada: reference gavimui kritiška `Options.ComputeReferences=True`, `IncludeNonVisibleObjects=True`, ir `Options.View=ActiveView`.

4. The Building Coder – How to Retrieve Dimensioning References
   - https://jeremytammik.github.io/tbc/a/1316_dim_ref_hints.htm
   - Esminė išvada: būtina naudoti view-kontekstinę geometriją; reference dažnai reikia papildomai filtruoti/identifikuoti.

5. ArchitectCoding – Auto dimension grids (pyRevit pavyzdys)
   - https://architectcoding.wordpress.com/2019/07/14/auto-dimension-grids/
   - Esminė išvada: `ReferenceArray` + grupavimas pagal kryptį yra geras „chain dimension“ pagrindas.

6. Dimensioning best practices (chain/string dimensijos principas)
   - https://novedge.com/blogs/design-news/revit-tip-best-practices-for-dimensioning-in-revit-for-accurate-design-communication
   - Esminė išvada: lygiagretiems elementams geriausia naudoti chain/string dimensijas vietoje daug atskirų matmenų.

## Įrankio pakeitimai

Failas:
- `MEP_Tools.tab/Dimensions.panel/AutoDim.pushbutton/script.py`

Įdiegta:
- Disciplina: **MEP / ARCH / STR**
- Kryptis: **X / Y / X+Y**
- Grandinėlės tipas: **Grandinėlė / Kraštiniai / Grandinėlė + Kraštiniai**
- Grid inkaravimas: **Be ašių / Su artimiausiomis ašimis (Grid)**
- Matmens stiliaus pasirinkimas iš `DimensionType`
- Reference paėmimas kelių lygių fallback principu:
  1) `FamilyInstance` reference planes (`CenterLeftRight`, `CenterFrontBack`, ...)
  2) `LocationCurve.Curve.Reference`
  3) fallback `Reference(element)`
- Rezultato suvestinė su sukurtų/nesukurtų matmenų skaičiumi ir pastabomis.

Papildomai atnaujintas pagalbos tekstas:
- `MEP_Tools.tab/Nustatymai.panel/Pagalba.pushbutton/script.py` (AutoDim aprašas)

## Pastabos
- Revit API reference kokybė priklauso nuo elementų tipo ir vaizdo konteksto.
- Dėl to įrankyje paliktas saugus fallback mechanizmas ir aiški rezultatų ataskaita naudotojui.
