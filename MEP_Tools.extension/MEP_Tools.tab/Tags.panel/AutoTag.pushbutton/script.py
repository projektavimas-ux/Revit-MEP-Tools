# -*- coding: utf-8 -*-
"""Auto-tag MEP elements in the active view."""
from pyrevit import revit, DB, UI
from pyrevit import forms

doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView

def auto_tag_mep():
    # Example categories for MEP
    categories = [
        DB.BuiltInCategory.OST_PipeCurves,
        DB.BuiltInCategory.OST_DuctCurves,
        DB.BuiltInCategory.OST_CableTray
    ]
    
    # Filter elements in active view
    filter_categories = DB.ElementMulticategoryFilter(categories)
    elements = DB.FilteredElementCollector(doc, active_view.Id) \
                 .WherePasses(filter_categories) \
                 .WhereElementIsNotElementType() \
                 .ToElements()

    if not elements:
        forms.alert("Nerasta jokių MEP elementų (vamzdžių, ortakių, latakų) aktyviame vaizde.")
        return

    tagged_count = 0
    
    with revit.Transaction("Auto Tag MEP Elements"):
        for elem in elements:
            # Here we would add logic to check if the element is already tagged
            # and determine the correct tag location (e.g., midpoint)
            
            # Simplified tag creation (requires default tag loaded)
            try:
                # Find the midpoint of the curve for tag placement
                location_curve = elem.Location
                if isinstance(location_curve, DB.LocationCurve):
                    curve = location_curve.Curve
                    midpoint = curve.Evaluate(0.5, True)
                    
                    # Create the tag (Revit 2022+ API)
                    ref = DB.Reference(elem)
                    tag = DB.IndependentTag.Create(
                        doc, 
                        active_view.Id, 
                        ref, 
                        False, 
                        DB.TagMode.TM_ADDBY_CATEGORY, 
                        DB.TagOrientation.Horizontal, 
                        midpoint
                    )
                    tagged_count += 1
            except Exception as e:
                print("Klaida žymint elementą {}: {}".format(elem.Id, str(e)))

    forms.alert("Sėkmingai sužymėta {} MEP elementų.".format(tagged_count))

if __name__ == '__main__':
    auto_tag_mep()
