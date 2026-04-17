# -*- coding: utf-8 -*-
"""Išmanus MEP elementų žymėjimas (AutoTag) su opcijomis."""
from pyrevit import revit, DB, UI, forms

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
        # Palaikymas Revit 2022+
        if hasattr(tag, 'GetTaggedLocalElementIds'):
            for el_id in tag.GetTaggedLocalElementIds():
                tagged_ids.add(el_id.IntegerValue)
        elif hasattr(tag, 'TaggedLocalElementId'):
            tagged_ids.add(tag.TaggedLocalElementId.IntegerValue)
    return tagged_ids

def auto_tag_mep():
    selected_ids = uidoc.Selection.GetElementIds()
    
    # --- 1. APIMTIS (Scope) ---
    scope_options = ["Visus matomus vaizde", "Tik dabar pažymėtus"]
    if selected_ids:
        scope = forms.CommandSwitchWindow.show(scope_options, message="Ką žymėsime? (Yra pažymėtų elementų: {})".format(len(selected_ids)))
    else:
        # Jei niekas nepažymėta, iškart siūlome visus
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

    # Surenkame elementus
    from System.Collections.Generic import List
    
    categories = [
        DB.BuiltInCategory.OST_PipeCurves,
        DB.BuiltInCategory.OST_DuctCurves,
        DB.BuiltInCategory.OST_CableTray
    ]
    
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
    
    # Bandoma naudoti 'Model' (lygiagrečiai) jeigu Revit versija tai palaiko, kitaip 'Horizontal'/'Vertical'
    if orientation == "Lygiagrečiai vamzdžiui/ortakiui":
        if hasattr(DB.TagOrientation, 'Model'):
            tag_orient_enum = DB.TagOrientation.Model
        else:
            tag_orient_enum = DB.TagOrientation.Horizontal  # Senesnėse versijose fallback'as
    else:
        tag_orient_enum = DB.TagOrientation.Horizontal
    offset_dist = 200 / 304.8 # 200mm atitraukimas (konvertuota į pėdas)
    
    tagged_count = 0
    skipped_count = 0

    with revit.Transaction("Išmanus MEP Taginimas"):
        for elem in elements:
            if elem.Id.IntegerValue in tagged_ids:
                skipped_count += 1
                continue

            try:
                location_curve = elem.Location
                if isinstance(location_curve, DB.LocationCurve):
                    curve = location_curve.Curve
                    midpoint = curve.Evaluate(0.5, True)
                    
                    tag_point = midpoint
                    if offset_choice == "Atitraukti į šoną (Offset)":
                        # Apskaičiuojame statmeną vektorių poslinkiui
                        direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
                        up_vector = DB.XYZ.BasisZ
                        normal = direction.CrossProduct(up_vector).Normalize()
                        tag_point = midpoint + normal * offset_dist

                    # Sukurti Tagą (Revit 2022+ logika)
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
                    tagged_count += 1
            except Exception as e:
                print("Klaida žymint {}: {}".format(elem.Id, str(e)))

    forms.alert("Sužymėta elementų: {}\nPraleista (jau turėjo tagą): {}".format(tagged_count, skipped_count))

if __name__ == '__main__':
    auto_tag_mep()
