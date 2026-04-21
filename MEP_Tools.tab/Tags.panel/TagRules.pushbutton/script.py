# -*- coding: utf-8 -*-
"""System -> Tag taisyklių valdymas AutoTag įrankiui."""
from pyrevit import DB, forms, revit
import os
import json


doc = revit.doc

AUTO_TAG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'AutoTag.pushbutton'))
RULES_FILE = os.path.join(AUTO_TAG_DIR, 'system_tag_rules.json')

CATEGORY_TO_BIC = {
    u"Vamzdžiai (Pipes)": DB.BuiltInCategory.OST_PipeCurves,
    u"Ortakiai (Ducts)": DB.BuiltInCategory.OST_DuctCurves,
    u"Kabelių loviai (Cable Trays)": DB.BuiltInCategory.OST_CableTray,
    u"Įrenginiai (Mechanical Equipment)": DB.BuiltInCategory.OST_MechanicalEquipment
}

CATEGORY_TO_TAG_BIC = {
    u"Vamzdžiai (Pipes)": DB.BuiltInCategory.OST_PipeTags,
    u"Ortakiai (Ducts)": DB.BuiltInCategory.OST_DuctTags,
    u"Kabelių loviai (Cable Trays)": DB.BuiltInCategory.OST_CableTrayTags,
    u"Įrenginiai (Mechanical Equipment)": DB.BuiltInCategory.OST_MechanicalEquipmentTags
}


def safe_text(v):
    try:
        return unicode(v)
    except Exception:
        try:
            return str(v)
        except Exception:
            return u""


def load_rules():
    if not os.path.exists(RULES_FILE):
        return []
    try:
        with open(RULES_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_rules(rules):
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def get_tag_options_for_category(cat_name):
    tag_bic = CATEGORY_TO_TAG_BIC.get(cat_name)
    if not tag_bic:
        return {}

    tag_symbols = DB.FilteredElementCollector(doc) \
        .OfCategory(tag_bic) \
        .OfClass(DB.FamilySymbol) \
        .ToElements()

    opts = {}
    for s in tag_symbols:
        try:
            fam = s.FamilyName if hasattr(s, 'FamilyName') and s.FamilyName else u"Tag"
            nm = s.Name if hasattr(s, 'Name') else u"Unknown"
            opts[u"{} - {}".format(safe_text(fam), safe_text(nm))] = s.Id.IntegerValue
        except Exception:
            pass
    return opts


def rule_label(r):
    en = u"ON" if r.get('enabled', True) else u"OFF"
    return u"[{}] {} | '{}' -> {} (P={})".format(
        en,
        r.get('category', u'?'),
        r.get('system_contains', u'*'),
        r.get('tag_name', u'?'),
        r.get('priority', 0)
    )


def show_rules():
    rules = load_rules()
    if not rules:
        forms.alert(u"Taisyklių dar nėra.")
        return

    lines = [u"System -> Tag taisyklės", u"=" * 28, u""]
    for i, r in enumerate(sorted(rules, key=lambda x: int(x.get('priority', 0)), reverse=True), 1):
        lines.append(u"{}. {}".format(i, rule_label(r)))
    forms.alert(u"\n".join(lines))


def manage_enabled_rules_checklist():
    rules = load_rules()
    if not rules:
        forms.alert(u"Taisyklių nėra.")
        return

    labels = [rule_label(r) for r in rules]

    selected_enabled = forms.SelectFromList.show(
        labels,
        title=u"Pažymėkite taisykles, kurios turi būti ĮJUNGTOS",
        multiselect=True,
        button_name=u"Išsaugoti ON/OFF"
    )
    if selected_enabled is None:
        return

    selected_enabled = set(selected_enabled)
    changed = 0
    for r in rules:
        lbl = rule_label(r)
        new_state = lbl in selected_enabled
        old_state = r.get('enabled', True)
        if bool(old_state) != bool(new_state):
            changed += 1
        r['enabled'] = new_state

    save_rules(rules)
    forms.alert(u"Taisyklių ON/OFF atnaujinta. Pakeista: {}".format(changed))


def add_rule():
    cat_name = forms.SelectFromList.show(
        sorted(CATEGORY_TO_BIC.keys()),
        title=u"Pasirink kategoriją",
        multiselect=False
    )
    if not cat_name:
        return

    tag_opts = get_tag_options_for_category(cat_name)
    if not tag_opts:
        forms.alert(u"Nerasta tag tipų šiai kategorijai. Pirma užkrauk bent vieną tag family tipą projekte.")
        return

    system_contains = forms.ask_for_string(
        default=u"*",
        prompt=u"Sistemos atitikimas (contains). Naudok '*' kaip default:",
        title=u"System match"
    )
    if system_contains is None:
        return

    tag_name = forms.SelectFromList.show(
        sorted(tag_opts.keys()),
        title=u"Pasirink Tag tipą",
        multiselect=False
    )
    if not tag_name:
        return

    pr_txt = forms.ask_for_string(
        default=u"100",
        prompt=u"Prioritetas (didesnis = svarbiau):",
        title=u"Priority"
    )
    if pr_txt is None:
        return
    try:
        priority = int(float((pr_txt or u"0").replace(',', '.')))
    except Exception:
        priority = 0

    enabled = forms.CommandSwitchWindow.show([u"ON", u"OFF"], message=u"Taisyklė aktyvi?")
    if not enabled:
        return

    rules = load_rules()
    rules.append({
        'category': cat_name,
        'system_contains': safe_text(system_contains).strip() or u"*",
        'tag_name': tag_name,
        'priority': priority,
        'enabled': enabled == u"ON"
    })
    save_rules(rules)
    forms.alert(u"Taisyklė pridėta.")


def delete_rule():
    rules = load_rules()
    if not rules:
        forms.alert(u"Nėra ką trinti.")
        return

    labels = [rule_label(r) for r in rules]
    selected = forms.SelectFromList.show(labels, title=u"Pasirink taisyklę trynimui", multiselect=True)
    if not selected:
        return

    remaining = []
    for r in rules:
        if rule_label(r) not in selected:
            remaining.append(r)

    save_rules(remaining)
    forms.alert(u"Ištrinta taisyklių: {}".format(len(rules) - len(remaining)))


def toggle_rule_enabled():
    rules = load_rules()
    if not rules:
        forms.alert(u"Taisyklių nėra.")
        return

    labels = [rule_label(r) for r in rules]
    sel = forms.SelectFromList.show(labels, title=u"Pasirink taisyklę ON/OFF", multiselect=False)
    if not sel:
        return

    for r in rules:
        if rule_label(r) == sel:
            r['enabled'] = not r.get('enabled', True)
            break

    save_rules(rules)
    forms.alert(u"Taisyklė atnaujinta.")


def clear_rules():
    confirm = forms.CommandSwitchWindow.show([u"Taip", u"Ne"], message=u"Išvalyti visas taisykles?")
    if confirm == u"Taip":
        save_rules([])
        forms.alert(u"Visos taisyklės išvalytos.")


def main():
    action = forms.CommandSwitchWindow.show(
        [u"Peržiūrėti", u"Pridėti", u"Ištrinti", u"ON/OFF", u"ON/OFF (varnelės)", u"Išvalyti visas"],
        message=u"Tag Rules valdymas"
    )
    if not action:
        return

    if action == u"Peržiūrėti":
        show_rules()
    elif action == u"Pridėti":
        add_rule()
    elif action == u"Ištrinti":
        delete_rule()
    elif action == u"ON/OFF":
        toggle_rule_enabled()
    elif action == u"ON/OFF (varnelės)":
        manage_enabled_rules_checklist()
    elif action == u"Išvalyti visas":
        clear_rules()


if __name__ == '__main__':
    main()
