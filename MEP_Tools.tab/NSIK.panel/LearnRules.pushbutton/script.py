# -*- coding: utf-8 -*-
"""Nuskaito NSIK taisykles iš esamo modelio ir išsaugo į mapping.json"""
from pyrevit import revit, DB, forms
import json
import os

doc = revit.doc

def get_param_value(elem, param_name):
    """Pagalbinė funkcija parametro reikšmei gauti."""
    param = elem.LookupParameter(param_name)
    if param and param.HasValue:
        return param.AsString() or param.AsValueString()
    return ""

def learn_nsik_rules():
    # Surenkame pagrindines MEP kategorijas
    categories = [
        DB.BuiltInCategory.OST_PipeCurves,
        DB.BuiltInCategory.OST_DuctCurves,
        DB.BuiltInCategory.OST_CableTray,
        DB.BuiltInCategory.OST_MechanicalEquipment,
        DB.BuiltInCategory.OST_PlumbingFixtures,
        DB.BuiltInCategory.OST_PipeFitting,
        DB.BuiltInCategory.OST_DuctFitting,
        DB.BuiltInCategory.OST_PipeAccessory,
        DB.BuiltInCategory.OST_DuctAccessory,
        DB.BuiltInCategory.OST_DuctTerminal
    ]
    
    filter_cats = DB.ElementMulticategoryFilter(categories)
    elements = DB.FilteredElementCollector(doc).WherePasses(filter_cats).WhereElementIsNotElementType().ToElements()
    
    mapping = {}
    learned_count = 0
    
    for elem in elements:
        # Ieškome ar elementas turi užpildytą NSIK kodą
        nsik_code = get_param_value(elem, "NSIKcodeLK")
        if not nsik_code:
            continue # Nėra kodo, ignoruojame
            
        nsik_term = get_param_value(elem, "NSIKtermLK")
        nsik_type_code = get_param_value(elem, "NcodeLKtID")
        nsik_type_term = get_param_value(elem, "NtermLKtID")
        
        # Gauname kategorijos sistemos pavadinimą
        if not elem.Category:
            continue
        cat_name = elem.Category.BuiltInCategory.ToString()
        
        # Gauname šeimos pavadinimą (Family name)
        elem_type = doc.GetElement(elem.GetTypeId())
        family_name = "default"
        if elem_type and hasattr(elem_type, 'FamilyName') and elem_type.FamilyName:
            family_name = elem_type.FamilyName
            
        if cat_name not in mapping:
            mapping[cat_name] = {}
            
        # Jei tokia taisyklė šeimai dar neįrašyta
        if family_name not in mapping[cat_name]:
            mapping[cat_name][family_name] = {
                "NSIKcodeLK": nsik_code,
                "NSIKtermLK": nsik_term,
                "NcodeLKtID": nsik_type_code,
                "NtermLKtID": nsik_type_term
            }
            learned_count += 1
    
    if learned_count == 0:
        forms.alert("Modelyje nerasta jokių MEP elementų su užpildytu 'NSIKcodeLK' parametru.\nŠablonas nebuvo atnaujintas.")
        return
        
    # Išsaugome į AutoCoder aplanką, kurį naudoja AutoCoder skriptas
    current_dir = os.path.dirname(__file__)
    panel_dir = os.path.dirname(current_dir)
    autocoder_dir = os.path.join(panel_dir, "AutoCoder.pushbutton")
    
    if not os.path.exists(autocoder_dir):
        os.makedirs(autocoder_dir)
        
    mapping_file = os.path.join(autocoder_dir, 'mapping.json')
    
    # Nuskaitome esamas taisykles, kad jų neištrintume
    existing_mapping = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                existing_mapping = json.load(f)
        except Exception:
            pass
            
    # Apjungiame: naujos taisyklės perrašo arba papildo senas
    for cat, rules in mapping.items():
        if cat not in existing_mapping:
            existing_mapping[cat] = {}
        for fam, data in rules.items():
            existing_mapping[cat][fam] = data
            
    # Įrašome atgal į failą
    try:
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(existing_mapping, f, indent=2, ensure_ascii=False)
        forms.alert("Mokymasis sėkmingai baigtas!\nSukurta / atnaujinta taisyklių: {}".format(learned_count))
    except Exception as e:
        forms.alert("Nepavyko išsaugoti failo:\n{}".format(str(e)))

if __name__ == '__main__':
    learn_nsik_rules()
