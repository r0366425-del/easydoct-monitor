#!/usr/bin/env python3
"""
SCRIPT DE DIAGNOSTIC v3 — EasyDoct
Utilise JavaScript pour déclencher la réactivité Vue.js
"""

from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://www.easydoct.com/rdv/imagerie-57-thionville-Terville-Hayange"

def screenshot(page, nom):
    page.screenshot(path=f"/tmp/{nom}.png", full_page=True)
    print(f"📸 {nom}.png")

def set_vue_select(page, selector, value):
    """Force la sélection dans un select Vue.js en déclenchant les bons événements."""
    page.evaluate(f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (!el) {{ return 'element not found'; }}
            
            // Trouver l'option correspondante
            var options = el.options;
            var found = false;
            for (var i = 0; i < options.length; i++) {{
                if (options[i].text.includes('{value}') || options[i].value.includes('{value}')) {{
                    el.selectedIndex = i;
                    found = true;
                    break;
                }}
            }}
            
            if (!found) {{ return 'option not found: {value}'; }}
            
            // Déclencher tous les événements nécessaires pour Vue.js
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            return 'ok: ' + el.options[el.selectedIndex].text;
        }})()
    """)

def diagnostic():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            # 1. Charger la page
            print("\n[1] Chargement...")
            page.goto(URL, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)
            screenshot(page, "01_page_chargee")

            # 2. Lister tous les selects et leurs options
            print("\n[2] Analyse des selects...")
            result = page.evaluate("""
                Array.from(document.querySelectorAll('select')).map((sel, i) => ({
                    index: i,
                    name: sel.name,
                    id: sel.id,
                    class: sel.className,
                    options: Array.from(sel.options).map(o => o.text.trim())
                }))
            """)
            for s in result:
                print(f"  Select #{s['index']} id='{s['id']}' name='{s['name']}' class='{s['class']}'")
                print(f"    Options: {s['options']}")

            # 3. Sélectionner SCANNER SANS INJECTION via JavaScript
            print("\n[3] Sélection type d'examen via JS...")
            res = page.evaluate("""
                (function() {
                    var selects = document.querySelectorAll('select');
                    for (var sel of selects) {
                        for (var opt of sel.options) {
                            if (opt.text.includes('SCANNER SANS INJECTION')) {
                                sel.value = opt.value;
                                sel.dispatchEvent(new Event('change', {bubbles: true}));
                                sel.dispatchEvent(new Event('input', {bubbles: true}));
                                return 'ok: ' + opt.text + ' (value=' + opt.value + ')';
                            }
                        }
                    }
                    return 'not found';
                })()
            """)
            print(f"  Résultat JS: {res}")
            
            # Attendre le rechargement AJAX du 2e select
            page.wait_for_timeout(4000)
            screenshot(page, "03_apres_type_examen")

            # 4. Lister à nouveau les selects pour voir si Examen est chargé
            print("\n[4] Selects après sélection type...")
            result2 = page.evaluate("""
                Array.from(document.querySelectorAll('select')).map((sel, i) => ({
                    index: i,
                    name: sel.name,
                    id: sel.id,
                    options: Array.from(sel.options).map(o => o.text.trim())
                }))
            """)
            for s in result2:
                print(f"  Select #{s['index']} id='{s['id']}' name='{s['name']}'")
                print(f"    Options: {s['options']}")

            # 5. Sélectionner Scanner Crâne Sans inj
            print("\n[5] Sélection examen Scanner Crâne...")
            res2 = page.evaluate("""
                (function() {
                    var selects = document.querySelectorAll('select');
                    for (var sel of selects) {
                        for (var opt of sel.options) {
                            if (opt.text.toLowerCase().includes('cr') && 
                                opt.text.toLowerCase().includes('inj')) {
                                sel.value = opt.value;
                                sel.dispatchEvent(new Event('change', {bubbles: true}));
                                sel.dispatchEvent(new Event('input', {bubbles: true}));
                                return 'ok: ' + opt.text;
                            }
                        }
                    }
                    return 'not found';
                })()
            """)
            print(f"  Résultat JS: {res2}")
            page.wait_for_timeout(2000)
            screenshot(page, "05_examen_selectionne")

            # 6. Cliquer Rechercher
            print("\n[6] Clic Rechercher...")
            page.get_by_text("Rechercher un rendez-vous").click(timeout=5000)
            page.wait_for_timeout(5000)
            screenshot(page, "06_resultats")
            
            texte = page.inner_text("body")
            print(f"\n📄 Résultat: {texte[:400]}")

        except Exception as e:
            print(f"💥 Erreur: {e}")
            screenshot(page, "erreur")
        finally:
            browser.close()
            print("\n✅ Terminé !")

if __name__ == "__main__":
    print(f"🔍 Diagnostic v3 — {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}")
    diagnostic()
