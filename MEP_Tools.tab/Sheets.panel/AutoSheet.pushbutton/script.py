# -*- coding: utf-8 -*-
"""
AutoSheet/AutoView MEP (v1)
Automatiškai kuria View + Sheet paketus pagal aukštus, sistemas ir zonas.
"""

from pyrevit import revit, DB, forms


doc = revit.doc


def safe_text(v):
    try:
        return unicode(v)
    except Exception:
        try:
            return str(v)
        except Exception:
            return u""


def collect_plan_view_types():
    out = []
    types = DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType).ToElements()
    for t in types:
        try:
            if t.ViewFamily in [DB.ViewFamily.MechanicalPlan, DB.ViewFamily.FloorPlan, DB.ViewFamily.CeilingPlan]:
                out.append(t)
        except Exception:
            pass
    return out


def collect_levels():
    levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
    levels = sorted(levels, key=lambda x: x.Elevation)
    return levels


def collect_scope_boxes():
    boxes = DB.FilteredElementCollector(doc) \
        .OfCategory(DB.BuiltInCategory.OST_VolumeOfInterest) \
        .WhereElementIsNotElementType() \
        .ToElements()
    return sorted(boxes, key=lambda x: safe_text(x.Name))


def collect_system_names():
    cats = [
        DB.BuiltInCategory.OST_PipeCurves,
        DB.BuiltInCategory.OST_DuctCurves,
        DB.BuiltInCategory.OST_PipeAccessory,
        DB.BuiltInCategory.OST_DuctAccessory,
        DB.BuiltInCategory.OST_PipeFitting,
        DB.BuiltInCategory.OST_DuctFitting,
        DB.BuiltInCategory.OST_MechanicalEquipment,
        DB.BuiltInCategory.OST_DuctTerminal
    ]
    filt = DB.ElementMulticategoryFilter(cats)
    els = DB.FilteredElementCollector(doc).WherePasses(filt).WhereElementIsNotElementType().ToElements()

    names = set()
    for e in els:
        try:
            p = e.get_Parameter(DB.BuiltInParameter.RBS_SYSTEM_NAME_PARAM)
            if p and p.HasValue:
                n = safe_text(p.AsString() or p.AsValueString()).strip()
                if n:
                    names.add(n)
        except Exception:
            pass

    return sorted(list(names))


def collect_view_templates():
    views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
    out = []
    for v in views:
        try:
            if v.IsTemplate and isinstance(v, DB.ViewPlan):
                out.append(v)
        except Exception:
            pass
    return sorted(out, key=lambda x: safe_text(x.Name))


def collect_titleblocks():
    syms = DB.FilteredElementCollector(doc) \
        .OfCategory(DB.BuiltInCategory.OST_TitleBlocks) \
        .WhereElementIsElementType() \
        .ToElements()
    return syms


def make_unique_name(desired_name, existing_names):
    if desired_name not in existing_names:
        existing_names.add(desired_name)
        return desired_name

    i = 2
    while True:
        candidate = u"{} ({})".format(desired_name, i)
        if candidate not in existing_names:
            existing_names.add(candidate)
            return candidate
        i += 1


def build_view_name(prefix, level_name, system_name, zone_name):
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append(level_name)
    if system_name:
        parts.append(system_name)
    if zone_name:
        parts.append(zone_name)
    return u" - ".join(parts)


def build_sheet_number(prefix, seq, existing_numbers):
    while True:
        num = u"{}-{:03d}".format(prefix, seq)
        if num not in existing_numbers:
            existing_numbers.add(num)
            return num, seq + 1
        seq += 1


def apply_scope_box(view, scope_box_id):
    if not scope_box_id:
        return
    try:
        p = view.get_Parameter(DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
        if p and (not p.IsReadOnly):
            p.Set(scope_box_id)
    except Exception:
        pass


def create_package():
    # 1) View type
    view_types = collect_plan_view_types()
    if not view_types:
        forms.alert(u"Nerasta tinkamų Plan View tipų (Mechanical/Floor/Ceiling).")
        return

    vt_map = {}
    for vt in view_types:
        label = u"{} | {}".format(safe_text(vt.ViewFamily), safe_text(vt.Name))
        vt_map[label] = vt

    vt_label = forms.SelectFromList.show(
        sorted(vt_map.keys()),
        title=u"1) Pasirink View tipą kūrimui",
        multiselect=False
    )
    if not vt_label:
        return
    selected_view_type = vt_map[vt_label]

    # 2) Levels
    levels = collect_levels()
    if not levels:
        forms.alert(u"Nerasta Levels.")
        return

    lvl_map = {safe_text(l.Name): l for l in levels}
    sel_lvl_names = forms.SelectFromList.show(
        sorted(lvl_map.keys()),
        title=u"2) Pasirink aukštus (Levels)",
        multiselect=True
    )
    if not sel_lvl_names:
        return
    selected_levels = [lvl_map[n] for n in sel_lvl_names]

    # 3) Systems (optional)
    systems = collect_system_names()
    use_systems = forms.CommandSwitchWindow.show([u"Taip", u"Ne"], message=u"3) Skirstyti pagal sistemas?")
    if not use_systems:
        return

    selected_systems = [None]
    if use_systems == u"Taip":
        if systems:
            sel = forms.SelectFromList.show(systems, title=u"Pasirink sistemas", multiselect=True)
            if sel:
                selected_systems = sel
        if selected_systems == [None]:
            # jei user pasirinko "Taip", bet nieko nepasirinko
            selected_systems = [u"System"]

    # 4) Zones / Scope boxes (optional)
    use_zones = forms.CommandSwitchWindow.show([u"Taip", u"Ne"], message=u"4) Skirstyti pagal zonas (Scope Boxes)?")
    if not use_zones:
        return

    selected_zones = [(None, None)]
    if use_zones == u"Taip":
        boxes = collect_scope_boxes()
        if boxes:
            box_map = {safe_text(b.Name): b for b in boxes}
            sel_box_names = forms.SelectFromList.show(
                sorted(box_map.keys()),
                title=u"Pasirink Scope Boxes",
                multiselect=True
            )
            if sel_box_names:
                selected_zones = [(n, box_map[n].Id) for n in sel_box_names]
        if selected_zones == [(None, None)]:
            selected_zones = [(u"Zone", None)]

    # 5) View template (optional)
    templates = collect_view_templates()
    template_id = None
    if templates:
        t_map = {safe_text(t.Name): t for t in templates}
        t_choices = [u"Nenaudoti"] + sorted(t_map.keys())
        t_pick = forms.SelectFromList.show(t_choices, title=u"5) View Template (nebūtina)", multiselect=False)
        if t_pick and t_pick != u"Nenaudoti":
            template_id = t_map[t_pick].Id

    # 6) Sheets?
    create_sheets_choice = forms.CommandSwitchWindow.show([u"Kurti Sheets", u"Tik Views"], message=u"6) Kurti sheets kartu?")
    if not create_sheets_choice:
        return
    create_sheets = create_sheets_choice == u"Kurti Sheets"

    titleblock_id = DB.ElementId.InvalidElementId
    sheet_prefix = u"MEP"
    seq_start = 1

    if create_sheets:
        titleblocks = collect_titleblocks()
        if not titleblocks:
            forms.alert(u"Nerasta TitleBlock tipų, todėl sheets nebus kuriami.")
            create_sheets = False
        else:
            tb_map = {}
            for tb in titleblocks:
                try:
                    fam = safe_text(tb.FamilyName) if hasattr(tb, 'FamilyName') else u"TitleBlock"
                    nm = safe_text(tb.Name)
                    tb_map[u"{} - {}".format(fam, nm)] = tb
                except Exception:
                    pass

            tb_pick = forms.SelectFromList.show(sorted(tb_map.keys()), title=u"Pasirink TitleBlock", multiselect=False)
            if not tb_pick:
                return
            titleblock_id = tb_map[tb_pick].Id

            prefix_in = forms.ask_for_string(default=u"MEP", prompt=u"Sheet numerio prefiksas (pvz. MEP):", title=u"Sheet numeracija")
            if prefix_in:
                sheet_prefix = prefix_in.strip() or u"MEP"

            start_in = forms.ask_for_string(default=u"1", prompt=u"Pradinis numeris:", title=u"Sheet numeracija")
            try:
                seq_start = int(float((start_in or u"1").replace(',', '.')))
            except Exception:
                seq_start = 1

    # 7) Naming prefix
    view_prefix = forms.ask_for_string(
        default=u"MEP",
        prompt=u"View pavadinimo prefiksas (pvz. MEP):",
        title=u"View naming"
    ) or u"MEP"

    # Kombinacijos
    combos = []
    for lvl in selected_levels:
        for sys in selected_systems:
            for zone_name, zone_id in selected_zones:
                combos.append((lvl, sys, zone_name, zone_id))

    if not combos:
        forms.alert(u"Nėra kombinacijų kūrimui.")
        return

    existing_view_names = set([safe_text(v.Name) for v in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()])
    existing_sheet_numbers = set([safe_text(s.SheetNumber) for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements()])

    created_views = 0
    created_sheets = 0
    warnings = []
    seq = seq_start

    with revit.Transaction(u"AutoSheet/AutoView MEP v1"):
        for lvl, sys_name, zone_name, zone_id in combos:
            try:
                view = DB.ViewPlan.Create(doc, selected_view_type.Id, lvl.Id)

                if template_id:
                    try:
                        view.ViewTemplateId = template_id
                    except Exception:
                        warnings.append(u"Template nepritaikytas view: {}".format(safe_text(lvl.Name)))

                apply_scope_box(view, zone_id)

                view_name = build_view_name(
                    view_prefix,
                    safe_text(lvl.Name),
                    safe_text(sys_name) if sys_name else None,
                    safe_text(zone_name) if zone_name else None
                )
                view.Name = make_unique_name(view_name, existing_view_names)
                created_views += 1

                if create_sheets:
                    try:
                        sheet = DB.ViewSheet.Create(doc, titleblock_id)
                        sheet_num, seq = build_sheet_number(sheet_prefix, seq, existing_sheet_numbers)
                        sheet.SheetNumber = sheet_num
                        sheet.Name = view.Name

                        # paprastas patalpinimas lapo centre-ish
                        DB.Viewport.Create(doc, sheet.Id, view.Id, DB.XYZ(1.0, 1.0, 0))
                        created_sheets += 1
                    except Exception as ex_sheet:
                        warnings.append(u"Sheet nepavyko '{}' -> {}".format(view.Name, safe_text(ex_sheet)))

            except Exception as ex:
                warnings.append(u"View nepavyko ({}): {}".format(safe_text(lvl.Name), safe_text(ex)))

    result = [
        u"Sukurta Views: {}".format(created_views),
        u"Sukurta Sheets: {}".format(created_sheets),
        u"Kombinacijų: {}".format(len(combos))
    ]

    if warnings:
        result.append(u"\nĮspėjimai (iki 20):")
        result.extend(warnings[:20])

    result.append(
        u"\nPastaba: v1 sistemos skirstymas šiuo metu veikia per naming struktūrą. "
        u"Kitas žingsnis būtų automatinis per-view MEP filtrų pritaikymas pagal sistemą."
    )

    forms.alert(u"\n".join(result))


if __name__ == '__main__':
    create_package()
