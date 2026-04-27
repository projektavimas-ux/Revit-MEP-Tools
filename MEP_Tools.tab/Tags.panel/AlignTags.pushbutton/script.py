# -*- coding: utf-8 -*-
"""Interaktyvus tagų lygiavimas pagal pažymėjimą (selection)."""
from pyrevit import revit, DB, forms
from Autodesk.Revit.UI import Selection as UISelection


doc = revit.doc
uidoc = revit.uidoc


class TagOnlySelectionFilter(UISelection.ISelectionFilter):
    def AllowElement(self, element):
        return isinstance(element, DB.IndependentTag)

    def AllowReference(self, reference, point):
        return False


def pick_tags_interactively():
    try:
        picked = uidoc.Selection.PickObjects(
            UISelection.ObjectType.Element,
            TagOnlySelectionFilter(),
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


def _normalize_mode(mode):
    if not mode:
        return ""

    m = mode.strip().lower()
    # Supaprastintas diakritikų suvienodinimas patikimam palyginimui
    m = m.replace("ė", "e").replace("ę", "e").replace("š", "s").replace("ž", "z")
    return m


def _get_bbox_x_bounds(tag):
    # Bandome kelis būdus, nes skirtingose Revit versijose veikia nevienodai
    for view in (doc.ActiveView, None):
        try:
            bb = tag.get_BoundingBox(view)
            if bb:
                return bb.Min.X, bb.Max.X
        except Exception:
            pass

        try:
            bb = tag.BoundingBox[view]
            if bb:
                return bb.Min.X, bb.Max.X
        except Exception:
            pass

    return None, None


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

    first_pt = pts[0][1]
    mode_key = _normalize_mode(mode)

    # Testuotojų semantika: Horizontaliai -> ta pati X, Vertikaliai -> ta pati Y
    if "horiz" in mode_key:
        target_x = first_pt.X
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(target_x, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    elif "vert" in mode_key:
        target_y = first_pt.Y
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(p.X, target_y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    elif "kaire" in mode_key:
        try:
            doc.Regenerate()
        except Exception:
            pass

        bounds = []
        for tag, p in pts:
            min_x, max_x = _get_bbox_x_bounds(tag)
            if min_x is None or max_x is None:
                failed += 1
                continue
            bounds.append((tag, p, min_x, max_x))

        if not bounds:
            return moved, failed

        target_left = min([b[2] for b in bounds])
        for tag, p, min_x, _ in bounds:
            try:
                dx = target_left - min_x
                tag.TagHeadPosition = DB.XYZ(p.X + dx, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    elif "desine" in mode_key:
        try:
            doc.Regenerate()
        except Exception:
            pass

        bounds = []
        for tag, p in pts:
            min_x, max_x = _get_bbox_x_bounds(tag)
            if min_x is None or max_x is None:
                failed += 1
                continue
            bounds.append((tag, p, min_x, max_x))

        if not bounds:
            return moved, failed

        target_right = max([b[3] for b in bounds])
        for tag, p, _, max_x in bounds:
            try:
                dx = target_right - max_x
                tag.TagHeadPosition = DB.XYZ(p.X + dx, p.Y, p.Z)
                moved += 1
            except Exception:
                failed += 1

    else:
        failed = len(pts)

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
