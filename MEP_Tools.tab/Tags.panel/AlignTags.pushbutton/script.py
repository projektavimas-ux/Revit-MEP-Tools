# -*- coding: utf-8 -*-
"""Interaktyvus tagų lygiavimas pagal pažymėjimą (selection)."""
from pyrevit import revit, DB, forms
from Autodesk.Revit.UI import Selection as UISelection


doc = revit.doc
uidoc = revit.uidoc


def pick_tags_interactively():
    try:
        picked = uidoc.Selection.PickObjects(
            UISelection.ObjectType.Element,
            "Pažymėk bent 2 tagus lygiavimui ir spausk Finish"
        )
    except Exception:
        return []

    tags = []
    for r in picked:
        el = doc.GetElement(r.ElementId)
        if isinstance(el, DB.IndependentTag):
            tags.append(el)
    return tags


def align_tags(tags, mode):
    pts = []
    for tag in tags:
        try:
            if hasattr(tag, 'TagHeadPosition'):
                pts.append((tag, tag.TagHeadPosition))
        except Exception:
            pass

    if len(pts) < 2:
        return 0, len(tags) - len(pts)

    moved = 0
    failed = 0

    if mode == "Horizontaliai":
        target_y = sum([p[1].Y for p in pts]) / float(len(pts))
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(p.X, target_y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    elif mode == "Vertikaliai":
        target_x = sum([p[1].X for p in pts]) / float(len(pts))
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(target_x, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    elif mode == "Prie kairės":
        target_x = min([p[1].X for p in pts])
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(target_x, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    elif mode == "Prie dešinės":
        target_x = max([p[1].X for p in pts])
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(target_x, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    return moved, failed


def main():
    mode = forms.CommandSwitchWindow.show(
        ["Horizontaliai", "Vertikaliai", "Prie kairės", "Prie dešinės"],
        message="Pasirink lygiavimo režimą"
    )
    if not mode:
        return

    tags = pick_tags_interactively()
    if len(tags) < 2:
        forms.alert("Pažymėk bent 2 tagus.")
        return

    with revit.Transaction("Sulygiuoti pažymėtus tagus"):
        moved, failed = align_tags(tags, mode)

    forms.alert("Sulygiuota tagų: {}. Nepavyko: {}.".format(moved, failed))


if __name__ == '__main__':
    main()
