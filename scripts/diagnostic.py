#!/usr/bin/env python3
"""
SCRIPT DE DIAGNOSTIC — EasyDoct
Prend une capture d'écran à chaque étape pour voir exactement
ce que le navigateur voit et corriger les sélecteurs.
"""

import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://www.easydoct.com/rdv/imagerie-57-thionville-Terville-Hayange"

def screenshot(page, nom):
    path = f"/tmp/{nom}.png"
    page.screenshot(path=path, full_page=True)
    print(f"📸 Capture : {nom}.png")
    return path

def diagnostic():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            # ── ÉTAPE 1 : Chargement de la page ──────────────────────────
            print("\n[1/6] Chargement de la page...")
            page.goto(URL, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)
            screenshot(page, "01_page_chargee")
            print("✅ Page chargée")

            # ── ÉTAPE 2 : Lister tous les éléments select ─────────────────
            print("\n[2/6] Analyse des champs select...")
            selects = page.query_selector_all("select")
            print(f"  → {len(selects)} champ(s) select trouvé(s)")
            for i, sel in enumerate(selects):
                opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]
                print(f"  Select #{i+1} : {opts[:5]}{'...' if len(opts)>5 else ''}")

            # ── ÉTAPE 3 : Lister tous les boutons radio (lieux) ───────────
            print("\n[3/6] Analyse des boutons de lieu...")
            radios = page.query_selector_all("input[type='radio']")
            print(f"  → {len(radios)} bouton(s) radio trouvé(s)")
            for r in radios:
                val = r.get_attribute("value") or ""
                label = page.query_selector(f"label[for='{r.get_attribute('id')}']")
                label_text = label.inner_text().strip() if label else "?"
                print(f"  Radio : value='{val}' label='{label_text}'")

            # ── ÉTAPE 4 : Sélectionner SCANNER SANS INJECTION ─────────────
            print("\n[4/6] Sélection type d'examen...")
            try:
                for sel in page.query_selector_all("select"):
                    opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]
                    if any("INJECTION" in o.upper() for o in opts):
                        sel.select_option(label="SCANNER SANS INJECTION")
                        page.wait_for_timeout(2000)
                        screenshot(page, "04_type_examen_selectionne")
                        print("✅ Type d'examen sélectionné")
                        break
            except Exception as e:
                print(f"❌ Erreur : {e}")
                screenshot(page, "04_erreur_type_examen")

            # ── ÉTAPE 5 : Sélectionner Scanner Crâne Sans inj ────────────
            print("\n[5/6] Sélection de l'examen...")
            try:
                for sel in page.query_selector_all("select"):
                    opts = [o.inner_text().strip() for o in sel.query_selector_all("option")]
                    if any("Cr" in o for o in opts):
                        print(f"  Options disponibles : {opts}")
                        # Chercher la bonne option
                        for opt in opts:
                            if "cr" in opt.lower() and "inj" in opt.lower():
                                sel.select_option(label=opt)
                                print(f"✅ Examen sélectionné : '{opt}'")
                                break
                        page.wait_for_timeout(2000)
                        screenshot(page, "05_examen_selectionne")
                        break
            except Exception as e:
                print(f"❌ Erreur : {e}")
                screenshot(page, "05_erreur_examen")

            # ── ÉTAPE 6 : Cliquer Rechercher ──────────────────────────────
            print("\n[6/6] Clic sur Rechercher...")
            try:
                # Lister tous les boutons
                boutons = page.query_selector_all("button, input[type='submit']")
                print(f"  → {len(boutons)} bouton(s) trouvé(s)")
                for b in boutons:
                    print(f"  Bouton : '{b.inner_text().strip()}'")

                page.get_by_text("Rechercher un rendez-vous").click(timeout=5000)
                page.wait_for_timeout(5000)
                screenshot(page, "06_resultats")
                print("✅ Recherche effectuée")

                # Afficher le texte final de la page
                contenu = page.inner_text("body")
                print(f"\n📄 Texte de la page (500 premiers caractères) :\n{contenu[:500]}")

            except Exception as e:
                print(f"❌ Erreur : {e}")
                screenshot(page, "06_erreur_recherche")

        except Exception as e:
            print(f"💥 Erreur générale : {e}")
            screenshot(page, "erreur_generale")
        finally:
            browser.close()
            print("\n✅ Diagnostic terminé — vérifiez les artefacts pour les captures !")

if __name__ == "__main__":
    print(f"🔍 Diagnostic EasyDoct — {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}")
    diagnostic()
