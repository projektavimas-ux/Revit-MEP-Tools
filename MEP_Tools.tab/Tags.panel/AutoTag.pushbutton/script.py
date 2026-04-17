# -*- coding: utf-8 -*-
"""Išmanus MEP elementų žymėjimas (AutoTag) su opcijomis."""
from pyrevit import revit, DB, UI, forms
import math

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
        if hasattr(tag, 'GetTaggedLocalElementIds'):
            for el_id in tag.GetTaggedLocalElementIds():
                tagged_ids.add(el_id.IntegerValue)
        elif hasattr(tag, 'TaggedLocalElementId'):
            tagged_ids.add(tag.TaggedLocalElementId.IntegerValue)
    return tagged_ids

def get_element_size(elem):
    """Pabando rasti elemento diametrą ar išmatavimą."""
    for p in elem.Parameters:
        if p.Definition.Name == "Size" or p.Definition.Name == "Dydis":
            val = p.AsValueString()
            if val: return val
            val = p.AsString()
            if val: return val
    return "UnknownSize"

def get_element_system_name(elem):
    """Pabando rasti elemento sistemos pavadinimą."""
    sys_param = elem.get_Parameter(DB.BuiltInParameter.RBS_SYSTEM_NAME_PARAM)
    if sys_param:
        val = sys_param.AsString()
        if val: return val
    return "UnknownSystem"

def auto_tag_mep():
    selected_ids = uidoc.Selection.GetElementIds()
    
    # --- 1. APIMTIS (Scope) ---
    scope_options = ["Visus matomus vaizde", "Tik dabar pažymėtus"]
    if selected_ids:
        scope = forms.CommandSwitchWindow.show(scope_options, message="Ką žymėsime? (Yra pažymėtų elementų: {})".format(len(selected_ids)))
    else:
        scope = "Visus matomus vaizde"
    if not scope: return

    # --- 2. LYGIUOTĖ (Orientation) ---
    orientation = forms.CommandSwitchWindow.show(
        ["Lygiagrečiai vamzdžiui/ortakiui", "Horizontaliai lapui"],
        message="Kaip orientuoti tagą?"
    )
    if not orientation: return

    # --- 3. POSLINKIS (Offset) ---
    offset_choice = forms.CommandSwitchWindow.show(
        ["Be poslinkio (centre)", "Atitraukti į šoną (Offset)"],
        message="Kur padėti tagą?"
    )
    if not offset_choice: return

    # --- 4. DUBLIKATAI ---
    duplicate_choice = forms.CommandSwitchWindow.show(
        ["Praleisti jau turinčius tagą", "Žymėti visus (ir dubliuoti)"],
        message="Ką daryti su elementais, kurie JAU turi tagą šiame vaizde?"
    )
    if not duplicate_choice: return

    # --- 5. STRATEGIJA ---
    strategy_choice = forms.CommandSwitchWindow.show(
        ["Išmanus: 1 tagas ištisai trasai", "Paprastas: žymėti visus segmentus"],
        message="Išmanus rėžimas sugrupuoja tos pačios sistemos ir to paties dydžio vamzdžius ir uždeda tik 1 tagą ant ilgiausios atkarpos. Taip išvengiama makalynės."
    )
    if not strategy_choice: return

    # Surenkame elementus
    from System.Collections.Generic import List
    categories = [
        DB.BuiltInCategory.OST_PipeCurves,
        DB.BuiltInCategory.OST_DuctCurves,
        DB.BuiltInCategory.OST_CableTray
    ]
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

    # Jei pasirinktas Išmanus rėžimas, filtruojame tik ilgiausius elementus pagal Sistemą + Dydį
    if "Išmanus" in strategy_choice:
        groups = {}
        for e in elements_to_process:
            sys_name = get_element_system_name(e)
            size_name = get_element_size(e)
            key = "{}_{}".format(sys_name, size_name)
            if key not in groups:
                groups[key] = []
            groups[key].append(e)
            
        smart_elements = []
        for key, elems in groups.items():
            longest_elem = None
            max_len = -1
            for e in elems:
                loc = e.Location
                if isinstance(loc, DB.LocationCurve):
                    length = loc.Curve.Length
                    if length > max_len:
                        max_len = length
                        longest_elem = e
            if longest_elem:
                smart_elements.append(longest_elem)
        elements_to_process = smart_elements

    tag_orient_enum = DB.TagOrientation.Horizontal
    offset_dist = 200 / 304.8 
    
    tagged_count = 0

    with revit.Transaction("Išmanus MEP Taginimas"):
        for elem in elements_to_process:
            try:
                location_curve = elem.Location
                if isinstance(location_curve, DB.LocationCurve):
                    curve = location_curve.Curve
                    midpoint = curve.Evaluate(0.5, True)
                    
                    tag_point = midpoint
                    if offset_choice == "Atitraukti į šoną (Offset)":
                        direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
                        up_vector = DB.XYZ.BasisZ
                        normal = direction.CrossProduct(up_vector).Normalize()
                        tag_point = midpoint + normal * offset_dist

                    ref = DB.Reference(elem)
                    tag = DB.IndependentTag.Create(
                        doc, 
                        active_view.Id, 
                        ref, 
                        False, 
                        DB.TagMode.TM_ADDBY_CATEGORY, 
                        tag_orient_enum, 
                        tag_point
                    )
                    
                    if orientation == "Lygiagrečiai vamzdžiui/ortakiui":
                        try:
                            direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
                            angle = math.atan2(direction.Y, direction.X)
                            if angle > math.pi / 2:
                                angle -= math.pi
                            elif angle < -math.pi / 2:
                                angle += math.pi
                            if hasattr(tag, 'Rotation'):
                                tag.Rotation = angle
                        except:
                            pass 
                            
                    tagged_count += 1
            except Exception as e:
                pass

    forms.alert("Sužymėta trasų/elementų: {}".format(tagged_count))

if __name__ == '__main__':
    auto_tag_mep()