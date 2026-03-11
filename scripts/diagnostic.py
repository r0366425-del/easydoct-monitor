#!/usr/bin/env python3
"""
SCRIPT DE DIAGNOSTIC v2 — EasyDoct
Corrige le problème de sélection de l'examen (chargement AJAX).
"""

from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

URL = "https://www.easydoct.com/rdv/imagerie-57-thionville-Terville-Hayange"

def screenshot(page, nom):
    path = f"/tmp/{nom}.png"
    page.screenshot(path=path, full_page=True)
    print(f"📸 {nom}.png")

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

            # 2. Sélectionner SCANNER SANS INJECTION
            print("\n[2] Sélection type d'examen...")
            selects = page.query_selector_all("select")
            print(f"  {len(selects)} select(s) trouvé(s) au départ")

            type_selectionne = False
            for sel in selects:
                opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]
                print(f"  Options: {opts}")
                if any("INJECTION" in o.upper() for o in opts):
                    sel.select_option(label="SCANNER SANS INJECTION")
                    print("  ✅ SCANNER SANS INJECTION sélectionné")
                    type_selectionne = True
                    break

            if not type_selectionne:
                print("  ❌ Type d'examen introuvable !")
                screenshot(page, "02_erreur_type")

            # 3. Attendre que le 2e select (Examen) se peuple via AJAX
            print("\n[3] Attente chargement des examens (AJAX)...")
            page.wait_for_timeout(3000)
            screenshot(page, "03_apres_attente")

            # Lister les selects après le chargement AJAX
            selects = page.query_selector_all("select")
            print(f"  {len(selects)} select(s) après AJAX")
            for i, sel in enumerate(selects):
                opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]
                print(f"  Select #{i+1}: {opts}")

            # 4. Chercher et sélectionner Scanner Crâne
            print("\n[4] Sélection de l'examen...")
            examen_selectionne = False
            for sel in page.query_selector_all("select"):
                opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]
                # Chercher une option contenant "cr" (crâne)
                for opt in opts:
                    if "cr" in opt.lower() and ("inj" in opt.lower() or "sans" in opt.lower()):
                        print(f"  → Option trouvée : '{opt}'")
                        sel.select_option(label=opt)
                        examen_selectionne = True
                        page.wait_for_timeout(1500)
                        break
                if examen_selectionne:
                    break

            screenshot(page, "04_examen_selectionne")

            if not examen_selectionne:
                print("  ❌ Examen introuvable — vérification dropdown custom...")
                # Peut-être un dropdown custom (select2, vue-select...)
                # Chercher tous les éléments cliquables avec "Examen"
                dropdowns = page.query_selector_all("[class*='select'], [class*='dropdown'], [class*='chosen']")
                print(f"  {len(dropdowns)} dropdown(s) custom trouvé(s)")
                for d in dropdowns[:5]:
                    print(f"  Dropdown: class='{d.get_attribute('class')}' text='{d.inner_text()[:50]}'")

            # 5. Cliquer Rechercher
            print("\n[5] Clic Rechercher...")
            page.get_by_text("Rechercher un rendez-vous").click(timeout=5000)
            page.wait_for_timeout(5000)
            screenshot(page, "05_resultats")

            # Texte résultat
            texte = page.inner_text("body")
            print(f"\n📄 Résultat (300 chars): {texte[:300]}")

        except Exception as e:
            print(f"💥 Erreur: {e}")
            screenshot(page, "erreur")
        finally:
            browser.close()
            print("\n✅ Diagnostic terminé !")

if __name__ == "__main__":
    print(f"🔍 Diagnostic v2 — {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}")
    diagnostic()
