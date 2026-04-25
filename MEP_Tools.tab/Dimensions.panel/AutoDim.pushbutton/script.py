# -*- coding: utf-8 -*-
"""Automatinis matmenų dėjimas pagal discipliną ir grandinėlės tipą."""
from pyrevit import revit, DB, forms
import System


doc = revit.doc
view = doc.ActiveView


def mm_to_ft(mm):
    return float(mm) / 304.8


def _safe_get_bic(name):
    return getattr(DB.BuiltInCategory, name, None)


DISCIPLINE_CATEGORIES = {
    "MEP": [
        _safe_get_bic("OST_DuctCurves"),
        _safe_get_bic("OST_PipeCurves"),
        _safe_get_bic("OST_CableTray"),
        _safe_get_bic("OST_Conduit"),
        _safe_get_bic("OST_DuctFitting"),
        _safe_get_bic("OST_PipeFitting"),
        _safe_get_bic("OST_DuctTerminal"),
        _safe_get_bic("OST_MechanicalEquipment"),
        _safe_get_bic("OST_PlumbingFixtures"),
        _safe_get_bic("OST_ElectricalEquipment"),
    ],
    "ARCH": [
        _safe_get_bic("OST_Walls"),
        _safe_get_bic("OST_Doors"),
        _safe_get_bic("OST_Windows"),
        _safe_get_bic("OST_Columns"),
        _safe_get_bic("OST_StructuralColumns"),
        _safe_get_bic("OST_Floors"),
        _safe_get_bic("OST_Roofs"),
        _safe_get_bic("OST_GenericModel"),
        _safe_get_bic("OST_CurtainWallPanels"),
        _safe_get_bic("OST_CurtainWallMullions"),
        _safe_get_bic("OST_Stairs"),
        _safe_get_bic("OST_Ramps"),
        _safe_get_bic("OST_Parking"),
        _safe_get_bic("OST_Casework"),
        _safe_get_bic("OST_Furniture"),
        _safe_get_bic("OST_SpecialityEquipment"),
    ],
    "STR": [
        _safe_get_bic("OST_StructuralColumns"),
        _safe_get_bic("OST_StructuralFraming"),
        _safe_get_bic("OST_StructuralFoundation"),
        _safe_get_bic("OST_StructuralConnections"),
        _safe_get_bic("OST_Walls"),
    ]
}


DISCIPLINE_OFFSET_MM = {
    "MEP": 1200,
    "ARCH": 900,
    "STR": 1000,
}


def pick_discipline():
    return forms.CommandSwitchWindow.show(
        ["MEP", "ARCH", "STR"],
        message="Pasirink discipliną"
    )


def pick_axis_mode():
    return forms.CommandSwitchWindow.show(
        ["X", "Y", "X + Y"],
        message="Pasirink matavimo kryptį"
    )


def pick_chain_mode():
    return forms.CommandSwitchWindow.show(
        ["Grandinėlė", "Kraštiniai", "Grandinėlė + Kraštiniai"],
        message="Pasirink grandinėlės tipą"
    )


def pick_grid_anchor_mode():
    return forms.CommandSwitchWindow.show(
        ["Be ašių", "Su artimiausiomis ašimis (Grid)"],
        message="Ar inkaruoti grandinėlę į ašis (Grid)?"
    )


def get_linear_dimension_types():
    result = []
    collector = DB.FilteredElementCollector(doc).OfClass(DB.DimensionType)
    for dt in collector:
        try:
            if dt and dt.StyleType == DB.DimensionStyleType.Linear:
                result.append(dt)
        except Exception:
            # Kai kuriose Revit versijose StyleType gali mesti klaidą
            try:
                if dt:
                    result.append(dt)
            except Exception:
                pass

    # Unikalūs + surikiuoti
    unique = {}
    for dt in result:
        try:
            key = dt.Id.IntegerValue
            unique[key] = dt
        except Exception:
            pass

    dtypes = list(unique.values())
    dtypes.sort(key=lambda x: x.Name if hasattr(x, "Name") else "")
    return dtypes


def pick_dimension_type():
    dtypes = get_linear_dimension_types()
    if not dtypes:
        return None

    labels = []
    mapping = {}
    for dt in dtypes:
        try:
            label = u"{} (id:{})".format(dt.Name, dt.Id.IntegerValue)
        except Exception:
            label = u"Nežinomas stilius"
        labels.append(label)
        mapping[label] = dt

    picked = forms.SelectFromList.show(
        labels,
        title="Pasirink matmens stilių",
        multiselect=False
    )
    if not picked:
        return None
    return mapping.get(picked)


def collect_elements_for_discipline(discipline):
    categories = [c for c in DISCIPLINE_CATEGORIES.get(discipline, []) if c is not None]
    elements = {}

    for cat in categories:
        try:
            coll = (DB.FilteredElementCollector(doc, view.Id)
                    .OfCategory(cat)
                    .WhereElementIsNotElementType()
                    .ToElements())
            for el in coll:
                try:
                    if el and el.Id.IntegerValue > 0:
                        elements[el.Id.IntegerValue] = el
                except Exception:
                    pass
        except Exception:
            pass

    # ARCH naudotojai dažnai paleidžia įrankį vaizduose, kur nėra tipinių sienų/langų,
    # bet yra kitų architektūrinių modelių. Jei po kategorijų filtro nieko nerasta,
    # dar bandome surinkti FamilyInstance pagal kategorijas, kurios kai kuriose Revit
    # versijose / šeimose grįžta ne per OfCategory kelią taip patikimai.
    if discipline == "ARCH" and not elements:
        try:
            fams = (DB.FilteredElementCollector(doc, view.Id)
                    .OfClass(DB.FamilyInstance)
                    .WhereElementIsNotElementType()
                    .ToElements())
            allowed = set([c for c in categories if c is not None])
            for el in fams:
                try:
                    cat = el.Category
                    if cat is None:
                        continue
                    bic = System.Enum.ToObject(DB.BuiltInCategory, cat.Id.IntegerValue)
                    if bic in allowed and el.Id.IntegerValue > 0:
                        elements[el.Id.IntegerValue] = el
                except Exception:
                    pass
        except Exception:
            pass

    return list(elements.values())


def collect_elements_any_discipline(exclude=None):
    merged = {}
    for disc_name in ["MEP", "ARCH", "STR"]:
        if exclude and disc_name == exclude:
            continue
        for el in collect_elements_for_discipline(disc_name):
            try:
                if el and el.Id.IntegerValue > 0:
                    merged[el.Id.IntegerValue] = el
            except Exception:
                pass
    return list(merged.values())


def get_element_point(el):
    try:
        loc = el.Location
        if isinstance(loc, DB.LocationPoint):
            return loc.Point
        if isinstance(loc, DB.LocationCurve):
            try:
                return loc.Curve.Evaluate(0.5, True)
            except Exception:
                c = loc.Curve
                return DB.XYZ(
                    (c.GetEndPoint(0).X + c.GetEndPoint(1).X) * 0.5,
                    (c.GetEndPoint(0).Y + c.GetEndPoint(1).Y) * 0.5,
                    (c.GetEndPoint(0).Z + c.GetEndPoint(1).Z) * 0.5,
                )
    except Exception:
        pass

    try:
        bb = el.get_BoundingBox(view) or el.get_BoundingBox(None)
        if bb:
            return DB.XYZ(
                (bb.Min.X + bb.Max.X) * 0.5,
                (bb.Min.Y + bb.Max.Y) * 0.5,
                (bb.Min.Z + bb.Max.Z) * 0.5,
            )
    except Exception:
        pass

    return None


def _get_family_refs(fi, axis):
    """Bando paimti šeimos centro/šonų reference pagal matavimo ašį."""
    enum_map = []
    if axis == "X":
        enum_map = [
            "CenterLeftRight",
            "Left",
            "Right",
        ]
    else:
        enum_map = [
            "CenterFrontBack",
            "Front",
            "Back",
        ]

    for enum_name in enum_map:
        try:
            enum_value = getattr(DB.FamilyInstanceReferenceType, enum_name, None)
            if enum_value is None:
                continue
            refs = fi.GetReferences(enum_value)
            if refs and refs.Count > 0:
                for r in refs:
                    if r is not None:
                        return r
        except Exception:
            continue
    return None


def _get_curve_reference(el):
    try:
        loc = el.Location
        if isinstance(loc, DB.LocationCurve):
            curve = loc.Curve
            try:
                if curve and curve.Reference:
                    return curve.Reference
            except Exception:
                pass
    except Exception:
        pass
    return None


def _fallback_element_reference(el):
    try:
        return DB.Reference(el)
    except Exception:
        return None


def extract_target(el):
    pt = get_element_point(el)
    if pt is None:
        return None

    rx = None
    ry = None

    # 1) FamilyInstance special references (patikimiausia centrinėms grandinėlėms)
    if isinstance(el, DB.FamilyInstance):
        rx = _get_family_refs(el, "X")
        ry = _get_family_refs(el, "Y")

    # 2) Curve reference (vamzdžiai, ortakiai, sienos, etc.)
    cref = _get_curve_reference(el)
    if cref is not None:
        if rx is None:
            rx = cref
        if ry is None:
            ry = cref

    # 3) Fallback
    eref = _fallback_element_reference(el)
    if eref is not None:
        if rx is None:
            rx = eref
        if ry is None:
            ry = eref

    if rx is None and ry is None:
        return None

    return {
        "element": el,
        "point": pt,
        "ref_x": rx,
        "ref_y": ry,
    }


def collect_grids_by_orientation():
    """
    Vertical grids -> tinka X grandinėlei (matuojam X atstumus).
    Horizontal grids -> tinka Y grandinėlei (matuojam Y atstumus).
    """
    x_grids = []
    y_grids = []

    try:
        grids = (DB.FilteredElementCollector(doc, view.Id)
                 .OfClass(DB.Grid)
                 .WhereElementIsNotElementType()
                 .ToElements())
    except Exception:
        grids = []

    for g in grids:
        try:
            c = g.Curve
            if c is None:
                continue
            p0 = c.GetEndPoint(0)
            p1 = c.GetEndPoint(1)
            d = (p1 - p0).Normalize()

            # Vertical grid line: direction mostly along Y -> coord by X
            if abs(d.X) < abs(d.Y):
                x_grids.append((p0.X, DB.Reference(g)))
            else:
                # Horizontal grid line: direction mostly along X -> coord by Y
                y_grids.append((p0.Y, DB.Reference(g)))
        except Exception:
            continue

    x_grids.sort(key=lambda t: t[0])
    y_grids.sort(key=lambda t: t[0])
    return x_grids, y_grids


def nearest_grid_ref(grid_data, coord):
    if not grid_data:
        return None
    return min(grid_data, key=lambda t: abs(t[0] - coord))[1]


def ref_stable_key(r):
    if r is None:
        return None
    try:
        return r.ConvertToStableRepresentation(doc)
    except Exception:
        try:
            return "{}:{}".format(r.ElementId.IntegerValue, r.LinkedElementId.IntegerValue)
        except Exception:
            try:
                return "{}".format(r.ElementId.IntegerValue)
            except Exception:
                return str(r)


def dedupe_refs(refs):
    seen = set()
    out = []
    for r in refs:
        if r is None:
            continue
        k = ref_stable_key(r)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def build_axis_refs(targets, axis, include_grid_anchors, x_grids, y_grids):
    coord_ref_pairs = []

    for t in targets:
        pt = t["point"]
        if axis == "X":
            ref = t.get("ref_x")
            coord = pt.X
        else:
            ref = t.get("ref_y")
            coord = pt.Y

        if ref is not None:
            coord_ref_pairs.append((coord, ref))

    if len(coord_ref_pairs) < 2:
        return []

    coord_ref_pairs.sort(key=lambda x: x[0])
    refs = [p[1] for p in coord_ref_pairs]

    if include_grid_anchors:
        first_coord = coord_ref_pairs[0][0]
        last_coord = coord_ref_pairs[-1][0]

        if axis == "X":
            first_grid = nearest_grid_ref(x_grids, first_coord)
            last_grid = nearest_grid_ref(x_grids, last_coord)
        else:
            first_grid = nearest_grid_ref(y_grids, first_coord)
            last_grid = nearest_grid_ref(y_grids, last_coord)

        if first_grid is not None:
            refs.insert(0, first_grid)
        if last_grid is not None:
            refs.append(last_grid)

    refs = dedupe_refs(refs)
    return refs


def make_dim_line(axis, points, offset_ft, margin_ft):
    xs = [p.X for p in points]
    ys = [p.Y for p in points]
    zs = [p.Z for p in points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    z = sum(zs) / float(len(zs))

    tiny = mm_to_ft(10)

    if axis == "X":
        y = min_y - offset_ft
        if abs(max_x - min_x) < tiny:
            max_x = min_x + mm_to_ft(1000)
        return DB.Line.CreateBound(
            DB.XYZ(min_x - margin_ft, y, z),
            DB.XYZ(max_x + margin_ft, y, z)
        )
    else:
        x = min_x - offset_ft
        if abs(max_y - min_y) < tiny:
            max_y = min_y + mm_to_ft(1000)
        return DB.Line.CreateBound(
            DB.XYZ(x, min_y - margin_ft, z),
            DB.XYZ(x, max_y + margin_ft, z)
        )


def offset_dim_line(axis, line, shift_ft):
    p0 = line.GetEndPoint(0)
    p1 = line.GetEndPoint(1)
    if axis == "X":
        v = DB.XYZ(0, -shift_ft, 0)
    else:
        v = DB.XYZ(-shift_ft, 0, 0)
    return DB.Line.CreateBound(p0 + v, p1 + v)


def make_ref_array(refs):
    arr = DB.ReferenceArray()
    for r in refs:
        arr.Append(r)
    return arr


def create_dimension(dim_line, refs, dim_type=None):
    if len(refs) < 2:
        return None

    arr = make_ref_array(refs)

    # Pirmiausia bandome su pasirinktu matmens stiliumi
    if dim_type is not None:
        try:
            return doc.Create.NewDimension(view, dim_line, arr, dim_type)
        except Exception:
            pass

    # Fallback į default stilių
    try:
        return doc.Create.NewDimension(view, dim_line, arr)
    except Exception:
        return None


def parse_axes(axis_mode):
    if axis_mode == "X + Y":
        return ["X", "Y"]
    return [axis_mode]


def main():
    if view is None:
        forms.alert("Nėra aktyvaus vaizdo.")
        return

    discipline = pick_discipline()
    if not discipline:
        return

    axis_mode = pick_axis_mode()
    if not axis_mode:
        return

    chain_mode = pick_chain_mode()
    if not chain_mode:
        return

    grid_mode = pick_grid_anchor_mode()
    if not grid_mode:
        return

    dim_type = pick_dimension_type()

    notes = []
    elements = collect_elements_for_discipline(discipline)
    if not elements:
        fallback = collect_elements_any_discipline(exclude=discipline)
        if fallback:
            use_fallback = forms.alert(
                "Aktyviame vaizde nerasta disciplinos elementų: {}.\n\n"
                "Tačiau rasta kitų disciplinų elementų ({} vnt.).\n"
                "Ar tęsti su jais?".format(discipline, len(fallback)),
                yes=True,
                no=True
            )
            if use_fallback:
                elements = fallback
                notes = [u"Naudoti kitų disciplinų elementai (fallback)."]
            else:
                return
        else:
            forms.alert("Aktyviame vaizde nerasta disciplinos elementų: {}".format(discipline))
            return

    targets = []
    for el in elements:
        t = extract_target(el)
        if t is not None:
            targets.append(t)

    if len(targets) < 2:
        forms.alert("Nepavyko gauti pakankamai tinkamų reference objektų matmenų kūrimui.")
        return

    x_grids, y_grids = collect_grids_by_orientation()
    include_grid_anchors = (grid_mode == "Su artimiausiomis ašimis (Grid)")

    offset_ft = mm_to_ft(DISCIPLINE_OFFSET_MM.get(discipline, 1000))
    margin_ft = mm_to_ft(600)
    overall_shift_ft = mm_to_ft(350)

    do_chain = (chain_mode in ["Grandinėlė", "Grandinėlė + Kraštiniai"])
    do_overall = (chain_mode in ["Kraštiniai", "Grandinėlė + Kraštiniai"])

    axes = parse_axes(axis_mode)

    created = 0
    failed = 0

    with revit.Transaction("AutoDim | {} | {}".format(discipline, chain_mode)):
        for axis in axes:
            axis_refs = build_axis_refs(
                targets,
                axis,
                include_grid_anchors,
                x_grids,
                y_grids
            )

            if len(axis_refs) < 2:
                notes.append(u"Ašis {}: per mažai reference objektų".format(axis))
                continue

            line = make_dim_line(axis, [t["point"] for t in targets], offset_ft, margin_ft)

            if do_chain:
                d = create_dimension(line, axis_refs, dim_type)
                if d:
                    created += 1
                else:
                    failed += 1
                    notes.append(u"Ašis {}: grandinėlės kūrimas nepavyko".format(axis))

            if do_overall and len(axis_refs) >= 2:
                overall_refs = [axis_refs[0], axis_refs[-1]]
                overall_line = offset_dim_line(axis, line, overall_shift_ft if do_chain else 0)
                d2 = create_dimension(overall_line, overall_refs, dim_type)
                if d2:
                    created += 1
                else:
                    failed += 1
                    notes.append(u"Ašis {}: kraštinių matmens kūrimas nepavyko".format(axis))

    summary = [
        u"AutoDim atlikta.",
        u"Disciplina: {}".format(discipline),
        u"Kryptis: {}".format(axis_mode),
        u"Grandinėlė: {}".format(chain_mode),
        u"Ašys (Grid): {}".format(grid_mode),
        u"Sukurta matmenų: {}".format(created),
        u"Nepavyko: {}".format(failed),
    ]

    if notes:
        summary.append(u"\nPastabos:")
        summary.extend([u"- " + n for n in notes[:8]])

    forms.alert("\n".join(summary))


if __name__ == '__main__':
    main()
