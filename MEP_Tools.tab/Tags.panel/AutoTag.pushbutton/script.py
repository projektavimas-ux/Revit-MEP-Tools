# -*- coding: utf-8 -*-
"""Išmanus MEP elementų žymėjimas (AutoTag) su išplėstinėmis opcijomis."""
from pyrevit import revit, DB, forms
import math
import re


doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView


def get_existing_tagged_ids():
    """Surenka visų šiame vaizde jau sužymėtų elementų ID."""
    existing_tags = DB.FilteredElementCollector(doc, active_view.Id) \
                      .OfClass(DB.IndependentTag) \
                      .ToElements()
    tagged_ids = set()
    for tag in existing_tags:
        try:
            if hasattr(tag, 'GetTaggedLocalElementIds'):
                for el_id in tag.GetTaggedLocalElementIds():
                    tagged_ids.add(el_id.IntegerValue)
            elif hasattr(tag, 'TaggedLocalElementId'):
                tagged_ids.add(tag.TaggedLocalElementId.IntegerValue)
        except Exception:
            pass
    return tagged_ids


def get_existing_tag_head_points():
    """Surenka esamų tagų galvučių pozicijas susikirtimų prevencijai."""
    pts = []
    tags = DB.FilteredElementCollector(doc, active_view.Id).OfClass(DB.IndependentTag).ToElements()
    for tag in tags:
        try:
            if hasattr(tag, 'TagHeadPosition'):
                p = tag.TagHeadPosition
                if p:
                    pts.append(p)
        except Exception:
            pass
    return pts


def point_distance_xy(p1, p2):
    dx = p1.X - p2.X
    dy = p1.Y - p2.Y
    return math.sqrt(dx * dx + dy * dy)


def choose_non_overlapping_point(base_point, direction, existing_points, step_ft, min_dist_ft, max_tries):
    """Parenka artimą, bet nesikertančią tag poziciją."""
    candidate = base_point

    if direction:
        up = DB.XYZ.BasisZ
        normal = direction.CrossProduct(up)
        try:
            normal = normal.Normalize()
        except Exception:
            normal = DB.XYZ.BasisY
    else:
        normal = DB.XYZ.BasisY

    if not existing_points:
        return candidate

    for i in range(max_tries):
        conflict = False
        for p in existing_points:
            if point_distance_xy(candidate, p) < min_dist_ft:
                conflict = True
                break

        if not conflict:
            return candidate

        # Zig-zag paieška aplink pradinį tašką
        shift_idx = (i // 2) + 1
        sign = 1 if (i % 2 == 0) else -1
        candidate = base_point + normal * (step_ft * shift_idx * sign)

    return candidate


def parse_float(value):
    if value is None:
        return None
    txt = str(value).strip().replace(',', '.')
    if not txt:
        return None
    try:
        return float(txt)
    except Exception:
        return None


def get_first_number(text):
    if not text:
        return None
    txt = str(text).replace(',', '.')
    m = re.search(r'[-+]?\d*\.?\d+', txt)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def get_element_size(elem):
    """Pabando rasti elemento diametrą ar išmatavimą."""
    for p in elem.Parameters:
        try:
            name = p.Definition.Name
            if name == "Size" or name == "Dydis":
                val = p.AsValueString()
                if val:
                    return val
                val = p.AsString()
                if val:
                    return val
        except Exception:
            pass
    return "UnknownSize"


def get_element_system_name(elem):
    """Pabando rasti elemento sistemos pavadinimą."""
    try:
        sys_param = elem.get_Parameter(DB.BuiltInParameter.RBS_SYSTEM_NAME_PARAM)
        if sys_param:
            val = sys_param.AsString()
            if val:
                return val
    except Exception:
        pass
    return "UnknownSystem"


def get_element_flow_value(elem):
    """Bando gauti debito reikšmę tik pagal rodomus projekto vienetus."""
    # Pirmiausia pagal dažniausius parametrų vardus
    candidate_names = [
        "Flow", "Air Flow", "Srautas", "Debitas", "Flow Rate"
    ]

    for p in elem.Parameters:
        try:
            name = p.Definition.Name
            if name in candidate_names:
                val_str = p.AsValueString()
                num = get_first_number(val_str)
                if num is not None:
                    return num
        except Exception:
            pass

    # Bandymas per BuiltInParameter (jei yra)
    for bip in [
        DB.BuiltInParameter.RBS_PIPE_FLOW_PARAM,
        DB.BuiltInParameter.RBS_DUCT_FLOW_PARAM
    ]:
        try:
            p = elem.get_Parameter(bip)
            if p:
                val_str = p.AsValueString()
                num = get_first_number(val_str)
                if num is not None:
                    return num
        except Exception:
            pass

    return None


def passes_conditional_filters(elem, system_filter_text, min_flow):
    if system_filter_text:
        sys_name = get_element_system_name(elem).lower()
        if system_filter_text.lower() not in sys_name:
            return False

    if min_flow is not None:
        flow = get_element_flow_value(elem)
        if flow is None or flow < min_flow:
            return False

    return True


def try_add_multi_leaders(tag, follower_elements):
    """Bando pridėti multi-leader nuorodas prie vieno tago."""
    if not follower_elements:
        return 0

    added = 0

    for follower in follower_elements:
        ref = None
        try:
            ref = DB.Reference(follower)
        except Exception:
            ref = None

        if ref is None:
            continue

        try:
            if hasattr(tag, 'AddReference'):
                tag.AddReference(ref)
                added += 1
                continue
        except Exception:
            pass

        try:
            if hasattr(tag, 'AddReferences'):
                from System.Collections.Generic import List
                refs = List[DB.Reference]()
                refs.Add(ref)
                tag.AddReferences(refs)
                added += 1
                continue
        except Exception:
            pass

    return added


def set_tag_parallel_rotation(tag, direction, tag_point):
    if not direction:
        return

    try:
        angle = math.atan2(direction.Y, direction.X)
        if angle > math.pi / 2:
            angle -= math.pi
        elif angle < -math.pi / 2:
            angle += math.pi

        # Bandome VIENĄ metodą, kad išvengtume dvigubo pasukimo.
        if hasattr(tag, 'Rotation'):
            try:
                tag.Rotation = angle
                return
            except Exception:
                pass

        try:
            axis = DB.Line.CreateBound(tag_point, tag_point + DB.XYZ.BasisZ)
            DB.ElementTransformUtils.RotateElement(doc, tag.Id, axis, angle)
        except Exception:
            pass

    except Exception:
        pass


def align_tag_heads(tags, align_mode):
    """Sulygiuoja tagų galvučių taškus horizontaliai arba vertikaliai."""
    if not tags or len(tags) < 2:
        return 0

    pts = []
    for tag in tags:
        try:
            if hasattr(tag, 'TagHeadPosition'):
                pts.append((tag, tag.TagHeadPosition))
        except Exception:
            pass

    if len(pts) < 2:
        return 0

    moved = 0

    if align_mode == "Horizontaliai":
        avg_y = sum([p[1].Y for p in pts]) / float(len(pts))
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(p.X, avg_y, p.Z)
                moved += 1
            except Exception:
                pass

    elif align_mode == "Vertikaliai":
        avg_x = sum([p[1].X for p in pts]) / float(len(pts))
        for tag, p in pts:
            try:
                tag.TagHeadPosition = DB.XYZ(avg_x, p.Y, p.Z)
                moved += 1
            except Exception:
                pass

    return moved


def refine_moved_tags_collision(moved_tag_entries, min_dist_ft, step_ft, max_tries=12):
    """Antras susikirtimų prevencijos ciklas tik pajudintiems tagams."""
    if not moved_tag_entries:
        return 0

    all_points = []
    for t, _dir in moved_tag_entries:
        try:
            if hasattr(t, 'TagHeadPosition') and t.TagHeadPosition:
                all_points.append(t.TagHeadPosition)
        except Exception:
            pass

    adjusted = 0
    for tag, direction in moved_tag_entries:
        try:
            if not hasattr(tag, 'TagHeadPosition'):
                continue

            current = tag.TagHeadPosition
            if not current:
                continue

            # Nevertiname savo paties taško kaip kliūties
            other_points = [p for p in all_points if point_distance_xy(p, current) > 1e-6]

            new_point = choose_non_overlapping_point(
                current,
                direction,
                other_points,
                step_ft,
                min_dist_ft,
                max_tries
            )

            if point_distance_xy(new_point, current) > 1e-6:
                tag.TagHeadPosition = new_point
                adjusted += 1
                all_points = [p for p in all_points if point_distance_xy(p, current) > 1e-6]
                all_points.append(new_point)
        except Exception:
            pass

    return adjusted


def auto_tag_mep():
    selected_ids = uidoc.Selection.GetElementIds()

    # --- 0. KATEGORIJŲ PASIRINKIMAS ---
    cat_map = {
        "Vamzdžiai (Pipes)": DB.BuiltInCategory.OST_PipeCurves,
        "Ortakiai (Ducts)": DB.BuiltInCategory.OST_DuctCurves,
        "Kabelių loviai (Cable Trays)": DB.BuiltInCategory.OST_CableTray,
        "Įrenginiai (Mechanical Equipment)": DB.BuiltInCategory.OST_MechanicalEquipment
    }
    selected_cat_names = forms.SelectFromList.show(
        list(cat_map.keys()),
        title="1. Ką norite žymėti? (Pasirinkite vieną ar kelis)",
        multiselect=True
    )
    if not selected_cat_names:
        return
    categories = [cat_map[name] for name in selected_cat_names]

    # --- 0.1 TAGŲ TIPŲ PASIRINKIMAS ---
    tag_cat_map = {
        DB.BuiltInCategory.OST_PipeCurves: DB.BuiltInCategory.OST_PipeTags,
        DB.BuiltInCategory.OST_DuctCurves: DB.BuiltInCategory.OST_DuctTags,
        DB.BuiltInCategory.OST_CableTray: DB.BuiltInCategory.OST_CableTrayTags,
        DB.BuiltInCategory.OST_MechanicalEquipment: DB.BuiltInCategory.OST_MechanicalEquipmentTags
    }

    tag_types_to_use = {}  # elem_category_int -> tag_type_id
    for cat_name in selected_cat_names:
        cat_enum = cat_map[cat_name]
        tag_enum = tag_cat_map.get(cat_enum)
        if not tag_enum:
            continue

        tag_symbols = DB.FilteredElementCollector(doc) \
                        .OfCategory(tag_enum) \
                        .OfClass(DB.FamilySymbol) \
                        .ToElements()

        if tag_symbols:
            options = {}
            for s in tag_symbols:
                try:
                    fam_name = s.FamilyName if hasattr(s, 'FamilyName') and s.FamilyName else "Tag"
                    type_name = s.Name if hasattr(s, 'Name') else "Unknown"
                    options["{} - {}".format(fam_name, type_name)] = s.Id
                except Exception:
                    pass

            chosen_tag_name = forms.SelectFromList.show(
                list(options.keys()),
                title="Pasirinkite Tag tipą: {}".format(cat_name),
                multiselect=False
            )
            if chosen_tag_name:
                tag_types_to_use[int(cat_enum)] = options[chosen_tag_name]

    # --- 0.2 IŠPLĖSTINĖS FUNKCIJOS (4 pasiūlymai) ---
    enhancement_options = [
        "Apsauga nuo tagų susikirtimų",
        "Vienas tagas grupei (multi-leader, jei palaikoma)",
        "Sąlyginis žymėjimas (sistema/debitas)"
    ]
    chosen_enhancements = forms.SelectFromList.show(
        enhancement_options,
        title="Papildomos funkcijos (pasirinkite vieną ar kelias)",
        multiselect=True
    ) or []

    use_collision_avoidance = "Apsauga nuo tagų susikirtimų" in chosen_enhancements
    use_multi_leader_mode = "Vienas tagas grupei (multi-leader, jei palaikoma)" in chosen_enhancements
    use_conditional_filter = "Sąlyginis žymėjimas (sistema/debitas)" in chosen_enhancements

    system_filter_text = ""
    min_flow = None
    if use_conditional_filter:
        system_filter_text = forms.ask_for_string(
            default="",
            prompt="Sistemos filtro tekstas (pvz. CHW, VENT). Tuščia = be filtro:",
            title="Sąlyginis žymėjimas: sistema"
        ) or ""

        min_flow_input = forms.ask_for_string(
            default="",
            prompt="Minimalus debitas (pagal projekto rodomus vienetus). Tuščia = be debito filtro:",
            title="Sąlyginis žymėjimas: debitas"
        )
        if min_flow_input:
            min_flow = parse_float(min_flow_input)
            if min_flow is None:
                forms.alert("Neteisingas minimalaus debito formatas. Debito filtras nebus taikomas.")

    # --- 1. APIMTIS (Scope) ---
    scope_options = ["Visus matomus vaizde", "Tik dabar pažymėtus"]
    if selected_ids:
        scope = forms.CommandSwitchWindow.show(
            scope_options,
            message="Ką žymėsime? (Yra pažymėtų elementų: {})".format(len(selected_ids))
        )
    else:
        scope = "Visus matomus vaizde"
    if not scope:
        return

    # --- 2. LYGIUOTĖ (Orientation) ---
    orientation = forms.CommandSwitchWindow.show(
        ["Lygiagrečiai vamzdžiui/ortakiui", "Horizontaliai lapui"],
        message="Kaip orientuoti tagą?"
    )
    if not orientation:
        return

    # --- 3. POSLINKIS (Offset) ---
    offset_choice = forms.CommandSwitchWindow.show(
        ["Be poslinkio (centre)", "Atitraukti į šoną (Offset)"],
        message="Kur padėti tagą?"
    )
    if not offset_choice:
        return

    # --- 4. DUBLIKATAI ---
    duplicate_choice = forms.CommandSwitchWindow.show(
        ["Praleisti jau turinčius tagą", "Žymėti visus (ir dubliuoti)"],
        message="Ką daryti su elementais, kurie JAU turi tagą šiame vaizde?"
    )
    if not duplicate_choice:
        return

    # --- 5. STRATEGIJA ---
    strategy_choice = forms.CommandSwitchWindow.show(
        ["Išmanus: 1 tagas ištisai trasai", "Paprastas: žymėti visus segmentus"],
        message=(
            "Išmanus rėžimas sugrupuoja tos pačios sistemos ir to paties dydžio "
            "vamzdžius ir uždeda tik 1 tagą ant ilgiausios atkarpos."
        )
    )
    if not strategy_choice:
        return

    # --- 6. ILGIO FILTRAS (Minimum Length) ---
    min_length_input = forms.ask_for_string(
        default="0.5",
        prompt="Įveskite minimalų ilgį metrais (m), nuo kurio žymėti elementus (pvz., 0.5, 1, 2). Trumpesni bus ignoruojami:",
        title="Minimalus ilgis"
    )

    min_length_ft = 0.0
    if min_length_input:
        try:
            min_length_m = float(min_length_input.replace(',', '.'))
            min_length_ft = min_length_m * 1000.0 / 304.8
        except ValueError:
            forms.alert("Neteisingas skaičiaus formatas. Bus žymimi visi ilgiai.")

    # Surenkame elementus
    from System.Collections.Generic import List

    cat_list = List[DB.BuiltInCategory](categories)
    filter_categories = DB.ElementMulticategoryFilter(cat_list)

    elements = []
    if scope == "Tik dabar pažymėtus" and selected_ids:
        cat_ids = [int(c) for c in categories]
        for eid in selected_ids:
            el = doc.GetElement(eid)
            if el and el.Category and el.Category.Id.IntegerValue in cat_ids:
                elements.append(el)
    else:
        elements = DB.FilteredElementCollector(doc, active_view.Id) \
                     .WherePasses(filter_categories) \
                     .WhereElementIsNotElementType() \
                     .ToElements()

    if not elements:
        forms.alert("Nerasta tinkamų MEP elementų žymėjimui.")
        return

    tagged_ids = get_existing_tagged_ids() if duplicate_choice == "Praleisti jau turinčius tagą" else set()

    # Praleidžiame jau pažymėtus
    elements_to_process = [e for e in elements if e.Id.IntegerValue not in tagged_ids]

    # Sąlyginiai filtrai
    if use_conditional_filter:
        filtered = []
        for e in elements_to_process:
            if passes_conditional_filters(e, system_filter_text, min_flow):
                filtered.append(e)
        elements_to_process = filtered

    # Jei pasirinktas Išmanus rėžimas, filtruojame tik ilgiausius pagal Sistema + Dydis
    if "Išmanus" in strategy_choice:
        groups = {}
        for e in elements_to_process:
            sys_name = get_element_system_name(e)
            size_name = get_element_size(e)
            cat_name = str(e.Category.Id.IntegerValue) if e.Category else "None"
            key = "{}_{}_{}".format(sys_name, size_name, cat_name)
            if key not in groups:
                groups[key] = []
            groups[key].append(e)

        smart_elements = []
        for _key, elems in groups.items():
            longest_elem = None
            max_len = -1
            for e in elems:
                loc = e.Location
                if isinstance(loc, DB.LocationCurve):
                    length = loc.Curve.Length
                    if length > max_len:
                        max_len = length
                        longest_elem = e
                elif isinstance(loc, DB.LocationPoint):
                    if max_len < 0:
                        longest_elem = e
                        max_len = 0
            if longest_elem:
                smart_elements.append(longest_elem)
        elements_to_process = smart_elements

    # Multi-leader režimui papildomai sugrupuojame elementus, kad vienam tagui turėti sekėjus
    grouped_units = []
    if use_multi_leader_mode:
        grouped = {}
        for e in elements_to_process:
            sys_name = get_element_system_name(e)
            size_name = get_element_size(e)
            cat_name = str(e.Category.Id.IntegerValue) if e.Category else "None"
            key = "{}_{}_{}".format(sys_name, size_name, cat_name)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(e)

        for _key, elems in grouped.items():
            anchor = None
            max_len = -1
            followers = []

            for e in elems:
                loc = e.Location
                this_len = 0.0
                if isinstance(loc, DB.LocationCurve):
                    this_len = loc.Curve.Length
                if anchor is None or this_len > max_len:
                    if anchor is not None:
                        followers.append(anchor)
                    anchor = e
                    max_len = this_len
                else:
                    followers.append(e)

            if anchor:
                grouped_units.append((anchor, followers))
    else:
        for e in elements_to_process:
            grouped_units.append((e, []))

    tag_orient_enum = DB.TagOrientation.Horizontal
    offset_dist = 200.0 / 304.8

    tagged_count = 0
    skipped_short = 0
    leader_links_added = 0
    warnings = []
    created_tags = []
    moved_collision_tags = []

    existing_tag_points = get_existing_tag_head_points() if use_collision_avoidance else []
    min_collision_dist_ft = 350.0 / 304.8  # ~350 mm
    collision_step_ft = 180.0 / 304.8      # ~180 mm

    with revit.Transaction("Išmanus MEP Taginimas"):
        for anchor_elem, followers in grouped_units:
            try:
                location = anchor_elem.Location
                direction = None

                if isinstance(location, DB.LocationCurve):
                    curve = location.Curve

                    # Filtruojame pagal minimalų ilgį (linijiniams elementams)
                    if curve.Length < min_length_ft:
                        skipped_short += 1
                        continue

                    midpoint = curve.Evaluate(0.5, True)
                    direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
                elif isinstance(location, DB.LocationPoint):
                    midpoint = location.Point
                    if hasattr(anchor_elem, "FacingOrientation"):
                        direction = anchor_elem.FacingOrientation
                    else:
                        direction = DB.XYZ.BasisX
                else:
                    continue

                tag_point = midpoint
                if offset_choice == "Atitraukti į šoną (Offset)" and direction:
                    up_vector = DB.XYZ.BasisZ
                    normal = direction.CrossProduct(up_vector)
                    try:
                        normal = normal.Normalize()
                    except Exception:
                        normal = DB.XYZ.BasisY
                    tag_point = midpoint + normal * offset_dist

                requested_tag_point = tag_point

                if use_collision_avoidance:
                    tag_point = choose_non_overlapping_point(
                        tag_point,
                        direction,
                        existing_tag_points,
                        collision_step_ft,
                        min_collision_dist_ft,
                        12
                    )

                ref = DB.Reference(anchor_elem)
                tag = DB.IndependentTag.Create(
                    doc,
                    active_view.Id,
                    ref,
                    False,
                    DB.TagMode.TM_ADDBY_CATEGORY,
                    tag_orient_enum,
                    tag_point
                )

                # Pakeičiame Tago tipą į vartotojo pasirinktą
                if anchor_elem.Category:
                    cat_int = anchor_elem.Category.Id.IntegerValue
                    if cat_int in tag_types_to_use:
                        try:
                            tag.ChangeTypeId(tag_types_to_use[cat_int])
                        except Exception:
                            pass

                # Lygiagretus pasukimas
                if orientation == "Lygiagrečiai vamzdžiui/ortakiui" and direction:
                    set_tag_parallel_rotation(tag, direction, tag_point)

                # Jei tagas buvo patrauktas dėl susikirtimo, įjungiam Leader
                if use_collision_avoidance and point_distance_xy(tag_point, requested_tag_point) > 1e-6:
                    try:
                        if hasattr(tag, 'HasLeader'):
                            tag.HasLeader = True
                    except Exception:
                        pass
                    moved_collision_tags.append((tag, direction))

                # Bandome multi-leader
                if use_multi_leader_mode and followers:
                    try:
                        if hasattr(tag, 'HasLeader'):
                            tag.HasLeader = True
                    except Exception:
                        pass

                    added = try_add_multi_leaders(tag, followers)
                    leader_links_added += added
                    if added < len(followers):
                        warnings.append(
                            "Nepavyko pridėti visų leader nuorodų grupei ({} iš {}).".format(added, len(followers))
                        )

                tagged_count += 1
                created_tags.append(tag)

                if use_collision_avoidance:
                    try:
                        if hasattr(tag, 'TagHeadPosition'):
                            existing_tag_points.append(tag.TagHeadPosition)
                        else:
                            existing_tag_points.append(tag_point)
                    except Exception:
                        existing_tag_points.append(tag_point)

            except Exception as ex:
                warnings.append("Elemento žymėjimo klaida: {}".format(ex))

        # Antras susikirtimų prevencijos ciklas tik pajudintiems tagams
        collision_refined_count = 0
        if use_collision_avoidance and moved_collision_tags:
            collision_refined_count = refine_moved_tags_collision(
                moved_collision_tags,
                min_collision_dist_ft,
                collision_step_ft,
                12
            )

    summary_lines = [
        "Sužymėta elementų/grupių: {}".format(tagged_count),
        "Praleista dėl minimalaus ilgio: {}".format(skipped_short)
    ]

    if use_multi_leader_mode:
        summary_lines.append("Pridėta multi-leader nuorodų: {}".format(leader_links_added))

    if use_collision_avoidance and moved_collision_tags:
        summary_lines.append(
            "Pajudintiems tagams įjungtas Leader: {} | pakoreguota antru ciklu: {}".format(
                len(moved_collision_tags),
                collision_refined_count
            )
        )

    if warnings:
        summary_lines.append("Įspėjimų: {}".format(len(warnings)))

    if use_multi_leader_mode:
        summary_lines.append(
            "Pastaba: 'Vienas tagas grupei' dažniausiai veikia ortakiams, kabelių loviams ir daliai įrenginių; "
            "vamzdžiams Revit API dažnai nepalaiko pilno AddReference scenarijaus."
        )

    forms.alert("\n".join(summary_lines))


if __name__ == '__main__':
    auto_tag_mep()
