# -*- coding: utf-8 -*-
"""Masinis vaizdų (Views) arba lapų (Sheets) pervadinimas."""
from pyrevit import revit, DB, UI, forms

doc = revit.doc

def batch_rename():
    # 1. Pasirenkame, ką norime pervadinti
    options = ["Lapus (Sheets)", "Vaizdus (Views)"]
    selected_option = forms.SelectFromList.show(options, title="Ką norite pervadinti?", button_name="Pasirinkti")
    
    if not selected_option:
        return

    # 2. Įvedame paieškos ir pakeitimo tekstą
    find_text = forms.ask_for_string(prompt="Kokį tekstą norite surasti ir pakeisti?", title="Rasti (Find)")
    if not find_text:
        return
        
    replace_text = forms.ask_for_string(prompt="Kuo pakeisti šį tekstą? (Palikite tuščią, jei norite tiesiog ištrinti)", title="Pakeisti (Replace)")
    if replace_text is None: # None means user clicked Cancel. Empty string means delete.
        return

    # 3. Surenkame elementus
    elements_to_rename = []
    if selected_option == "Lapus (Sheets)":
        elements = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
        for e in elements:
            if find_text in e.Name or find_text in e.SheetNumber:
                elements_to_rename.append(e)
    else:
        elements = DB.FilteredElementCollector(doc).OfClass(DB.View).WhereElementIsNotElementType().ToElements()
        for e in elements:
            if not e.IsTemplate and find_text in e.Name:
                elements_to_rename.append(e)

    if not elements_to_rename:
        forms.alert("Nerasta jokių elementų, kurių pavadinime būtų '{}'".format(find_text))
        return

    # 4. Vykdome pakeitimą
    renamed_count = 0
    with revit.Transaction("Masinis pervadinimas: {}".format(selected_option)):
        for elem in elements_to_rename:
            try:
                if selected_option == "Lapus (Sheets)":
                    if find_text in elem.Name:
                        elem.Name = elem.Name.replace(find_text, replace_text)
                    if find_text in elem.SheetNumber:
                        elem.SheetNumber = elem.SheetNumber.replace(find_text, replace_text)
                else:
                    elem.Name = elem.Name.replace(find_text, replace_text)
                renamed_count += 1
            except Exception as e:
                print("Klaida pervadinant {}: {}".format(elem.Id, str(e)))

    forms.alert("Sėkmingai pervadinta elementų: {}".format(renamed_count))

if __name__ == '__main__':
    batch_rename()
