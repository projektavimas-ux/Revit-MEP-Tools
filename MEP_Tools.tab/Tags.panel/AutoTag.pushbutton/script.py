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
    if not selected_cat_names: return
    categories = [cat_map[name] for name in selected_cat_names]
    
    # --- 0.1 TAGŲ TIPŲ PASIRINKIMAS ---
    tag_cat_map = {
        DB.BuiltInCategory.OST_PipeCurves: DB.BuiltInCategory.OST_PipeTags,
        DB.BuiltInCategory.OST_DuctCurves: DB.BuiltInCategory.OST_DuctTags,
        DB.BuiltInCategory.OST_CableTray: DB.BuiltInCategory.OST_CableTrayTags,
        DB.BuiltInCategory.OST_MechanicalEquipment: DB.BuiltInCategory.OST_MechanicalEquipmentTags
    }
    
    tag_types_to_use = {} # elem_category_int -> tag_type_id
    for cat_name in selected_cat_names:
        cat_enum = cat_map[cat_name]
        tag_enum = tag_cat_map.get(cat_enum)
        if not tag_enum: continue
        
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
    
    # Paverčiame Python sąrašą į .NET C# List, kurio reikalauja Revit API
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
                elif isinstance(loc, DB.LocationPoint):
                    # Įrenginiams priskiriame prioritetą, tiesiog imame pirmą
                    if max_len < 0:
                        longest_elem = e
                        max_len = 0
            if longest_elem:
                smart_elements.append(longest_elem)
        elements_to_process = smart_elements

    tag_orient_enum = DB.TagOrientation.Horizontal
    offset_dist = 200 / 304.8 
    
    tagged_count = 0

    with revit.Transaction("Išmanus MEP Taginimas"):
        for elem in elements_to_process:
            try:
                location = elem.Location
                curve = None
                direction = None
                
                if isinstance(location, DB.LocationCurve):
                    curve = location.Curve
                    midpoint = curve.Evaluate(0.5, True)
                    direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
                elif isinstance(location, DB.LocationPoint):
                    midpoint = location.Point
                    # Įrenginių atveju bandome gauti jų pasukimo kryptį (FacingOrientation)
                    if hasattr(elem, "FacingOrientation"):
                        direction = elem.FacingOrientation
                    else:
                        direction = DB.XYZ.BasisX
                else:
                    continue # Jei neturi nei kreivės nei taško, praleidžiame
                    
                tag_point = midpoint
                if offset_choice == "Atitraukti į šoną (Offset)" and direction:
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
                
                # Pakeičiame Tago tipą į vartotojo pasirinktą
                if elem.Category:
                    cat_int = elem.Category.Id.IntegerValue
                    if cat_int in tag_types_to_use:
                        try:
                            tag.ChangeTypeId(tag_types_to_use[cat_int])
                        except:
                            pass
                
                if orientation == "Lygiagrečiai vamzdžiui/ortakiui" and direction:
                    try:
                        # Pasukimo kampo skaičiavimas
                        angle = math.atan2(direction.Y, direction.X)
                        if angle > math.pi / 2:
                            angle -= math.pi
                        elif angle < -math.pi / 2:
                            angle += math.pi
                            
                        # Metodas 1: Priverstinai bandome nustatyti TagOrientation į Model (Enum reikšmė 2 Revit 2022+)
                        import System
                        try:
                            tag.TagOrientation = System.Enum.ToObject(DB.TagOrientation, 2)
                        except:
                            pass
                            
                        # Metodas 2: Jei versija labai nauja ir tag.Rotation veikia
                        if hasattr(tag, 'Rotation'):
                            try:
                                tag.Rotation = angle
                            except:
                                pass
                                
                        # Metodas 3: Fiziškai pasukame visą Tag elementą su ElementTransformUtils
                        try:
                            axis = DB.Line.CreateBound(tag_point, tag_point + DB.XYZ.BasisZ)
                            DB.ElementTransformUtils.RotateElement(doc, tag.Id, axis, angle)
                        except:
                            pass
                    except:
                        pass 
                        
                tagged_count += 1
            except Exception as e:
                pass

    forms.alert("Sužymėta trasų/elementų: {}".format(tagged_count))

if __name__ == '__main__':
    auto_tag_mep()