# -*- coding: utf-8 -*-
"""Sulygiuoja pažymėtus tagus į vieną horizontalią arba vertikalią liniją."""
from pyrevit import revit, DB, forms


doc = revit.doc
uidoc = revit.uidoc


def get_selected_tags():
    tags = []
    sel_ids = uidoc.Selection.GetElementIds()
    for eid in sel_ids:
        el = doc.GetElement(eid)
        if isinstance(el, DB.IndependentTag):
            tags.append(el)
    return tags


def align_tags(tags, mode, anchor_mode):
    pts = []
    for tag in tags:
        try:
            if hasattr(tag, 'TagHeadPosition'):
                pts.append((tag, tag.TagHeadPosition))
        except Exception:
            pass

    if len(pts) < 2:
        return 0, len(tags) - len(pts)

    if mode == "Horizontaliai":
        if anchor_mode == "Pagal pirmą pažymėtą":
            target_y = pts[0][1].Y
        else:
            target_y = sum([p[1].Y for p in pts]) / float(len(pts))

        moved = 0
        failed = 0
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(p.X, target_y, p.Z)
                moved += 1
            except Exception:
                failed += 1
        return moved, failed

    if mode == "Vertikaliai":
        if anchor_mode == "Pagal pirmą pažymėtą":
            target_x = pts[0][1].X
        else:
            target_x = sum([p[1].X for p in pts]) / float(len(pts))

        moved = 0
        failed = 0
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(target_x, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1
        return moved, failed

    return 0, 0


def main():
    tags = get_selected_tags()
    if len(tags) < 2:
        forms.alert("Pažymėk bent 2 tagus, kuriuos nori sulygiuoti.")
        return

    mode = forms.CommandSwitchWindow.show(
        ["Horizontaliai", "Vertikaliai"],
        message="Kaip sulygiuoti pažymėtus tagus?"
    )
    if not mode:
        return

    anchor_mode = forms.CommandSwitchWindow.show(
        ["Pagal pirmą pažymėtą", "Pagal vidurkį"],
        message="Pagal kokią liniją lygiuoti?"
    )
    if not anchor_mode:
        return

    with revit.Transaction("Sulygiuoti pažymėtus tagus"):
        moved, failed = align_tags(tags, mode, anchor_mode)

    forms.alert("Sulygiuota tagų: {}. Nepavyko: {}.".format(moved, failed))


if __name__ == '__main__':
    main()
