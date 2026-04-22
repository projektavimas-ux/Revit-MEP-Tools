# -*- coding: utf-8 -*-
"""Atidaro MEP Tools pagalbos aprašymus."""
from pyrevit import forms


HELP_DOCS = {
    u"AutoTag": u"""
AutoTag
- Paskirtis: automatiškai sužymėti MEP elementus aktyviame projekte.
- Ką gali:
  • žymėti kelias kategorijas (pipes, ducts, cable trays, equipment)
  • pasirinkti tag tipą kiekvienai kategorijai
  • žymėti pagal scope (pažymėti elementai arba visi vaizde)
  • orientacija + offset + dublikatų valdymas
  • anti-overlap (tagų susikirtimų prevencija)
  • sąlyginis žymėjimas pagal sistemą / debitą
  • grupinis režimas (multi-leader bandymas, kai palaikoma)
- Kada naudoti: kai reikia greitai sužymėti daug elementų su vieninga logika.
""",

    u"AlignTags": u"""
AlignTags
- Paskirtis: sulygiuoti jau esamus, pažymėtus tagus.
- Kaip veikia:
  1) pažymi bent 2 tagus
  2) pasirenki Horizontaliai arba Vertikaliai
  3) pasirenki lygiavimo bazę: pagal pirmą pažymėtą arba pagal vidurkį
- Kada naudoti: kai vaizde tagai išsibarstę po rankinių pataisymų.
""",

    u"TagRules": u"""
TagRules
- Paskirtis: valdyti System -> Tag taisykles AutoTag įrankiui.
- Ką gali:
  • Peržiūrėti taisykles
  • Pridėti naują taisyklę (kategorija + sistemos tekstas + tag tipas + prioritetas)
  • Ištrinti taisyklę
  • Įjungti/išjungti taisyklę (ON/OFF)
- Kada naudoti: kai skirtingoms sistemoms reikia skirtingų tag tipų.
""",

    u"AutoSheet": u"""
AutoSheet / AutoView MEP (v1)
- Paskirtis: generuoti view + sheet paketus pagal aukštus/sistemas/zonas.
- Ką daro:
  • kuria plan views pagal pasirinktą ViewFamilyType
  • optional: skirsto pagal sistemas ir Scope Boxes (zonas)
  • optional: pritaiko View Template
  • optional: kuria sheets, numeruoja, deda view ant lapo
- Pastaba: v1 sistemų skirstymas orientuotas į paketų/naming kūrimą;
  automatiniai per-view MEP filtrai pagal sistemą bus v2.
""",

    u"ParameterTransformer": u"""
ParameterTransformer MEP (v2)
- Paskirtis: masinis parametrų redagavimas su Excel roundtrip.
- Režimai:
  • Export -> CSV/XLSX
  • Import <- CSV/XLSX
  • Rollback <- LOG
- Workflow:
  1) pasirenki kategorijas + filtrus
  2) eksportuoji parametrus į lentelę
  3) redaguoji Excel'e
  4) importuoji atgal (su preview)
  5) jei reikia, atstatai pakeitimus iš rollback JSON log.
- Kada naudoti: standartizavimui, numeracijai, dideliems parametrų pakeitimams.
""",

    u"BatchRename": u"""
BatchRename
- Paskirtis: masiškai pervadinti sheets.
- Ką daro: randa tekstą pavadinimuose ir pakeičia nauju.
- Kada naudoti: kai keičiasi projekto naming taisyklės.
""",

    u"AutoCoder": u"""
AutoCoder (NSIK)
- Paskirtis: automatinis NSIK kodų priskyrimas pagal mapping taisykles.
- Šaltinis: mapping.json taisyklės (kategorija/šeima -> kodai).
- Kada naudoti: kai reikia vienodo klasifikavimo per visą modelį.
""",

    u"LearnRules": u"""
LearnRules (NSIK)
- Paskirtis: „išmokti“ NSIK taisykles iš esamo modelio ir atnaujinti mapping.
- Ką daro: nuskaito elementus su NSIK reikšmėmis ir papildo AutoCoder mapping.
- Kada naudoti: kai modelyje jau turi gerų pavyzdžių ir nori juos paversti taisyklėmis.
""",

    u"Atnaujinti": u"""
Atnaujinti
- Paskirtis: atsinaujinti MEP Tools paketą iš repozitorijos.
- Kada naudoti: po naujų funkcijų ar klaidų pataisymų.
""",

    u"SmartExport": u"""
SmartExport
- Paskirtis: centralizuotas modelio/duomenų eksportas pagal įmonės workflow.
- Pastaba: priklauso nuo konkrečios projekto konfigūracijos ir eksporto scenarijų.
""",

    u"AutoSection": u"""
AutoSection
- Paskirtis: greitesnis sekcijų kūrimas pagal pasirinktą logiką.
- Naudojimas: kai reikia serijiniu būdu kurti daug pjūvių.
""",

    u"AutoDim": u"""
AutoDim
- Paskirtis: automatinis matmenų dėjimas pagal discipliną ir grandinėlės tipą.
- Paleidimo metu leidžia pasirinkti:
  • discipliną (MEP / ARCH / STR)
  • kryptį (X / Y / X+Y)
  • grandinėlės tipą (Grandinėlė / Kraštiniai / Grandinėlė + Kraštiniai)
  • ar inkaruoti grandinėlę į artimiausias ašis (Grid)
  • matmens stilių (DimensionType)
- Kada naudoti: kai skirtingoms disciplinoms reikia skirtingos matmenavimo logikos,
  bet vieno bendro AutoDim įrankio.
"""
}


def show_all_docs():
    lines = [u"MEP Tools pagalba", u"=" * 22, u""]
    for key in sorted(HELP_DOCS.keys()):
        lines.append(HELP_DOCS[key].strip())
        lines.append(u"\n" + u"-" * 40 + u"\n")
    forms.alert(u"\n".join(lines))


def main():
    options = [u"Rodyti viską"] + sorted(HELP_DOCS.keys())
    pick = forms.SelectFromList.show(
        options,
        title=u"MEP Tools pagalba",
        multiselect=False
    )
    if not pick:
        return

    if pick == u"Rodyti viską":
        show_all_docs()
    else:
        forms.alert(HELP_DOCS.get(pick, u"Aprašymas nerastas."))


if __name__ == '__main__':
    main()
