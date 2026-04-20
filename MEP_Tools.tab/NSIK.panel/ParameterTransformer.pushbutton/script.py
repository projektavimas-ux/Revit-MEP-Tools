# -*- coding: utf-8 -*-
"""
Parameter Transformer MEP (v1)
- Eksportuoja filtruotus MEP elementų parametrus į CSV (Excel roundtrip)
- Importuoja pakeitimus iš CSV ir masiškai pritaiko Revit modelyje
"""

from pyrevit import revit, DB, forms
import os
import csv
import codecs


doc = revit.doc


CATEGORY_MAP = {
    u"Pipes": DB.BuiltInCategory.OST_PipeCurves,
    u"Ducts": DB.BuiltInCategory.OST_DuctCurves,
    u"Pipe Fittings": DB.BuiltInCategory.OST_PipeFitting,
    u"Duct Fittings": DB.BuiltInCategory.OST_DuctFitting,
    u"Pipe Accessories": DB.BuiltInCategory.OST_PipeAccessory,
    u"Duct Accessories": DB.BuiltInCategory.OST_DuctAccessory,
    u"Cable Trays": DB.BuiltInCategory.OST_CableTray,
    u"Mechanical Equipment": DB.BuiltInCategory.OST_MechanicalEquipment,
    u"Plumbing Fixtures": DB.BuiltInCategory.OST_PlumbingFixtures,
    u"Duct Terminals": DB.BuiltInCategory.OST_DuctTerminal,
    u"Conduits": DB.BuiltInCategory.OST_Conduit,
    u"Conduit Fittings": DB.BuiltInCategory.OST_ConduitFitting,
}


def safe_text(val):
    if val is None:
        return u""
    try:
        return unicode(val)
    except Exception:
        try:
            return str(val).decode('utf-8', 'ignore')
        except Exception:
            try:
                return str(val)
            except Exception:
                return u""


def default_csv_path(filename):
    home = os.path.expanduser("~")
    return os.path.join(home, filename)


def get_level_name(elem):
    try:
        p = elem.get_Parameter(DB.BuiltInParameter.FAMILY_LEVEL_PARAM)
        if p and p.HasValue:
            return safe_text(p.AsValueString() or p.AsString())
    except Exception:
        pass

    try:
        p = elem.get_Parameter(DB.BuiltInParameter.RBS_START_LEVEL_PARAM)
        if p and p.HasValue:
            return safe_text(p.AsValueString() or p.AsString())
    except Exception:
        pass

    return u""


def get_system_name(elem):
    try:
        p = elem.get_Parameter(DB.BuiltInParameter.RBS_SYSTEM_NAME_PARAM)
        if p and p.HasValue:
            return safe_text(p.AsString() or p.AsValueString())
    except Exception:
        pass
    return u""


def get_family_type(elem):
    fam = u""
    typ = u""
    try:
        et = doc.GetElement(elem.GetTypeId())
        if et:
            if hasattr(et, 'FamilyName') and et.FamilyName:
                fam = safe_text(et.FamilyName)
            if hasattr(et, 'Name') and et.Name:
                typ = safe_text(et.Name)
    except Exception:
        pass
    return fam, typ


def collect_elements(selected_category_names, system_filter_text, level_filter_text):
    bics = [CATEGORY_MAP[n] for n in selected_category_names]
    filter_cats = DB.ElementMulticategoryFilter(bics)
    elements = DB.FilteredElementCollector(doc).WherePasses(filter_cats).WhereElementIsNotElementType().ToElements()

    out = []
    for e in elements:
        sys_name = get_system_name(e)
        lvl_name = get_level_name(e)

        if system_filter_text and system_filter_text.lower() not in sys_name.lower():
            continue
        if level_filter_text and level_filter_text.lower() not in lvl_name.lower():
            continue

        out.append(e)

    return out


def get_editable_param_names(elements):
    names = set()
    for e in elements:
        try:
            for p in e.Parameters:
                try:
                    if p and p.Definition and p.Definition.Name and (not p.IsReadOnly):
                        names.add(safe_text(p.Definition.Name))
                except Exception:
                    pass
        except Exception:
            pass

    # kad UI būtų stabilesnis, apribojam iki 150 dažniausiai matomų pagal abėcėlę
    names = sorted(list(names))
    if len(names) > 150:
        names = names[:150]
    return names


def get_param_display_value(elem, param_name):
    p = elem.LookupParameter(param_name)
    if not p:
        return u""

    try:
        st = p.StorageType
        if st == DB.StorageType.String:
            return safe_text(p.AsString() or u"")
        if st == DB.StorageType.Double:
            return safe_text(p.AsValueString() or u"")
        if st == DB.StorageType.Integer:
            return safe_text(p.AsInteger())
        if st == DB.StorageType.ElementId:
            eid = p.AsElementId()
            if eid:
                return safe_text(eid.IntegerValue)
            return u""
    except Exception:
        pass

    try:
        return safe_text(p.AsValueString() or p.AsString() or u"")
    except Exception:
        return u""


def set_param_from_text(elem, param_name, new_text):
    p = elem.LookupParameter(param_name)
    if (not p) or p.IsReadOnly:
        return False, u"Parametras nerastas arba read-only"

    txt = safe_text(new_text).strip()

    try:
        st = p.StorageType

        if st == DB.StorageType.String:
            p.Set(txt)
            return True, u""

        if st == DB.StorageType.Double:
            # geriausias kelias pagal projekto vienetus
            try:
                ok = p.SetValueString(txt)
                if ok:
                    return True, u""
            except Exception:
                pass

            # fallback į raw float
            try:
                val = float(txt.replace(',', '.'))
                p.Set(val)
                return True, u""
            except Exception:
                return False, u"Neteisinga skaitinė reikšmė"

        if st == DB.StorageType.Integer:
            try:
                p.Set(int(float(txt.replace(',', '.'))))
                return True, u""
            except Exception:
                return False, u"Neteisinga sveiko skaičiaus reikšmė"

        if st == DB.StorageType.ElementId:
            try:
                p.Set(DB.ElementId(int(float(txt.replace(',', '.')))))
                return True, u""
            except Exception:
                return False, u"Neteisingas ElementId"

        return False, u"Nepalaikomas parametro tipas"

    except Exception as ex:
        return False, safe_text(ex)


def export_to_csv(path, elements, selected_params):
    headers = [
        u"UniqueId", u"ElementId", u"Category", u"Family", u"Type", u"Level", u"System"
    ] + selected_params

    with codecs.open(path, 'w', 'utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for e in elements:
            fam, typ = get_family_type(e)
            row = [
                safe_text(e.UniqueId),
                safe_text(e.Id.IntegerValue),
                safe_text(e.Category.Name if e.Category else u""),
                fam,
                typ,
                get_level_name(e),
                get_system_name(e)
            ]

            for pn in selected_params:
                row.append(get_param_display_value(e, pn))

            writer.writerow([safe_text(x) for x in row])


def read_csv(path):
    with codecs.open(path, 'r', 'utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]
        headers = reader.fieldnames or []
    return headers, rows


def import_from_csv(path):
    headers, rows = read_csv(path)

    base_cols = [u"UniqueId", u"ElementId", u"Category", u"Family", u"Type", u"Level", u"System"]
    editable_cols = [h for h in headers if h not in base_cols]

    if u"UniqueId" not in headers:
        forms.alert(u"CSV faile trūksta 'UniqueId' stulpelio.")
        return

    changes_preview = []
    change_plan = []

    for r in rows:
        uid = safe_text(r.get(u"UniqueId", u"")).strip()
        if not uid:
            continue

        elem = doc.GetElement(uid)
        if not elem:
            continue

        for pn in editable_cols:
            if pn is None:
                continue
            new_val = safe_text(r.get(pn, u""))
            old_val = get_param_display_value(elem, pn)

            # tuščia reikšmė nereiškia automatinio trynimo, nebent sena irgi netuščia ir user aiškiai pakeitė
            if new_val == old_val:
                continue

            # registruojam pakeitimą
            change_plan.append((elem, pn, new_val, old_val))
            if len(changes_preview) < 30:
                changes_preview.append(u"{} | {}: '{}' -> '{}'".format(elem.Id.IntegerValue, pn, old_val, new_val))

    if not change_plan:
        forms.alert(u"CSV nerasta jokių pakeitimų pritaikymui.")
        return

    msg = u"Rasti pakeitimai: {}\n\nPeržiūra (iki 30):\n{}\n\nTaikyti pakeitimus?".format(
        len(change_plan),
        u"\n".join(changes_preview)
    )

    decision = forms.CommandSwitchWindow.show([u"Taikyti", u"Atšaukti"], message=msg)
    if decision != u"Taikyti":
        forms.alert(u"Importas atšauktas.")
        return

    ok_count = 0
    fail_count = 0
    fail_msgs = []

    with revit.Transaction(u"Parameter Transformer MEP - Import"):
        for elem, pn, new_val, old_val in change_plan:
            ok, err = set_param_from_text(elem, pn, new_val)
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                if len(fail_msgs) < 20:
                    fail_msgs.append(u"{} | {} -> {}".format(elem.Id.IntegerValue, pn, err))

    result = [u"Pritaikyta: {}".format(ok_count), u"Nepavyko: {}".format(fail_count)]
    if fail_msgs:
        result.append(u"\nKlaidų pavyzdžiai:\n" + u"\n".join(fail_msgs))

    forms.alert(u"\n".join(result))


def export_flow():
    selected_cats = forms.SelectFromList.show(
        sorted(CATEGORY_MAP.keys()),
        title=u"Pasirink kategorijas eksportui",
        multiselect=True
    )
    if not selected_cats:
        return

    system_filter = forms.ask_for_string(
        default=u"",
        prompt=u"Sistemos filtras (contains). Tuščia = visi:",
        title=u"Filtras pagal sistemą"
    ) or u""

    level_filter = forms.ask_for_string(
        default=u"",
        prompt=u"Level filtras (contains). Tuščia = visi:",
        title=u"Filtras pagal level"
    ) or u""

    elements = collect_elements(selected_cats, system_filter, level_filter)
    if not elements:
        forms.alert(u"Pagal pasirinktus filtrus elementų nerasta.")
        return

    param_names = get_editable_param_names(elements)
    selected_params = forms.SelectFromList.show(
        param_names,
        title=u"Pasirink parametrus eksportui (Excel redagavimui)",
        multiselect=True
    )
    if not selected_params:
        forms.alert(u"Nepasirinkta parametrų eksportui.")
        return

    default_path = default_csv_path('mep_parameter_transformer_export.csv')
    path = forms.ask_for_string(
        default=default_path,
        prompt=u"CSV failo kelias eksportui:",
        title=u"Export CSV"
    )
    if not path:
        return

    try:
        export_to_csv(path, elements, selected_params)
        forms.alert(u"Eksportuota elementų: {}\nFailas: {}".format(len(elements), path))
    except Exception as ex:
        forms.alert(u"Eksportas nepavyko:\n{}".format(safe_text(ex)))


def import_flow():
    default_path = default_csv_path('mep_parameter_transformer_export.csv')
    path = forms.ask_for_string(
        default=default_path,
        prompt=u"CSV failo kelias importui:",
        title=u"Import CSV"
    )
    if not path:
        return

    if not os.path.exists(path):
        forms.alert(u"Failas nerastas:\n{}".format(path))
        return

    try:
        import_from_csv(path)
    except Exception as ex:
        forms.alert(u"Importas nepavyko:\n{}".format(safe_text(ex)))


def main():
    action = forms.CommandSwitchWindow.show(
        [u"Export -> CSV", u"Import <- CSV"],
        message=u"Parameter Transformer MEP"
    )

    if action == u"Export -> CSV":
        export_flow()
    elif action == u"Import <- CSV":
        import_flow()


if __name__ == '__main__':
    main()
