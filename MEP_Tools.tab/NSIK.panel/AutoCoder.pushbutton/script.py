# -*- coding: utf-8 -*-
"""Automatically assign NSIK classification codes to elements."""
from pyrevit import revit, DB, UI
from pyrevit import forms
import json
import os

doc = revit.doc

def load_mapping():
    mapping_file = os.path.join(os.path.dirname(__file__), 'mapping.json')
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def auto_code_nsik():
    mapping = load_mapping()
    if not mapping:
        forms.alert("Nerastas arba tuščias mapping.json failas.")
        return

    # Surenkame visus elementus pagal kategorijas, esančias mapping.json
    updated_count = 0
    
    with revit.Transaction("NSIK Auto-Coding"):
        for category_name, rules in mapping.items():
            try:
                # Gauname BuiltInCategory iš string
                bic = getattr(DB.BuiltInCategory, category_name)
                elements = DB.FilteredElementCollector(doc) \
                             .OfCategory(bic) \
                             .WhereElementIsNotElementType() \
                             .ToElements()
                             
                for elem in elements:
                    # Čia logikoje ateityje atskirsime pagal Šeimos (Family) pavadinimą
                    # Kol kas, demonstravimui, imame "default" arba pirmą taisyklę
                    rule = rules.get("default") or list(rules.values())[0]
                    
                    # Įrašome parametrus (jei tokie sukurti projekte)
                    # pavyzdžiui, elem.LookupParameter("NSIKcodeLK").Set(rule["NSIKcodeLK"])
                    updated_count += 1
            except Exception as e:
                print("Klaida apdorojant kategoriją {}: {}".format(category_name, str(e)))

    forms.alert("Bandomasis NSIK kodavimas baigtas. Apdorota elementų: {}".format(updated_count))

if __name__ == '__main__':
    auto_code_nsik()
