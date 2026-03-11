#!/usr/bin/env python3
"""
Moniteur RDV EasyDoct — Scanner Crâne Sans injection
Logique : cherche D'ABORD les créneaux (boutons verts), 
puis vérifie le message "complètes" seulement si aucun créneau trouvé.
"""

import os, smtplib, sys, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from playwright.sync_api import sync_playwright

URL        = "https://www.easydoct.com/rdv/imagerie-57-thionville-Terville-Hayange"
EMAIL_DEST = os.environ["EMAIL_DEST"].split(",")
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_PASS = os.environ["EMAIL_PASS"]

def verifier_disponibilite():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            print("🌐 Chargement de la page...")
            page.goto(URL, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # 1. Sélectionner SCANNER SANS INJECTION
            res1 = page.evaluate("""
                (function() {
                    var selects = document.querySelectorAll('select');
                    for (var sel of selects) {
                        for (var opt of sel.options) {
                            if (opt.text.includes('SCANNER SANS INJECTION')) {
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
            print(f"  Type examen: {res1}")
            page.wait_for_timeout(4000)

            # 2. Sélectionner Scanner Crâne Sans inj
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
            print(f"  Examen: {res2}")
            page.wait_for_timeout(2000)

            # 3. Cliquer Rechercher
            page.get_by_text("Rechercher un rendez-vous").click(timeout=5000)
            page.wait_for_timeout(5000)

            # 4. Chercher les boutons de créneaux VISIBLES (boutons verts avec heures)
            #    On cherche les éléments visibles contenant des horaires type "10:00"
            creneaux = page.evaluate("""
                (function() {
                    var results = [];
                    // Chercher tous les éléments avec du texte heure visible
                    var all = document.querySelectorAll('*');
                    for (var el of all) {
                        // Vérifier que l'élément est visible et contient une heure
                        if (el.children.length === 0) {  // Élément feuille (pas de children)
                            var text = el.textContent.trim();
                            if (/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(text)) {
                                var style = window.getComputedStyle(el);
                                if (style.display !== 'none' && style.visibility !== 'hidden') {
                                    if (!results.includes(text)) {
                                        results.push(text);
                                    }
                                }
                            }
                        }
                    }
                    return results;
                })()
            """)

            if creneaux:
                print(f"✅ Créneaux VISIBLES trouvés : {creneaux}")
                browser.close()
                return True, creneaux

            # 5. Seulement si aucun créneau visible → vérifier le message
            texte_visible = page.inner_text("body").lower()
            if "toutes nos plages horaires sont actuellement complètes" in texte_visible:
                print("❌ Message confirmé : plages complètes.")
            else:
                print("⏳ Aucun créneau détecté.")

            browser.close()
            return False, []

        except Exception as e:
            print(f"⚠️  Erreur: {e}")
            browser.close()
            sys.exit(1)

def envoyer_alerte(creneaux):
    heure = datetime.now().strftime("%d/%m/%Y à %H:%M UTC")
    liste = "<ul>" + "".join(f"<li><strong>{c}</strong></li>" for c in creneaux) + "</ul>"

    corps_html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
    <div style="max-width:520px;margin:auto;background:white;border-radius:12px;
                padding:30px;border-top:6px solid #2ecc40;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
      <h2 style="color:#2ecc40;margin-top:0">✅ Créneau disponible !</h2>
      <p style="color:#555">Un rendez-vous vient de se libérer sur EasyDoct.</p>
      <table style="width:100%;border-collapse:collapse;margin:15px 0;font-size:14px">
        <tr style="background:#f9f9f9">
          <td style="padding:10px;border:1px solid #eee"><strong>📅 Détecté le</strong></td>
          <td style="padding:10px;border:1px solid #eee">{heure}</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #eee"><strong>🏥 Site</strong></td>
          <td style="padding:10px;border:1px solid #eee">Clinique Ambroise Paré — Thionville</td>
        </tr>
        <tr style="background:#f9f9f9">
          <td style="padding:10px;border:1px solid #eee"><strong>🩻 Examen</strong></td>
          <td style="padding:10px;border:1px solid #eee">Scanner Crâne Sans injection</td>
        </tr>
      </table>
      <p><strong>Créneaux disponibles :</strong></p>
      {liste}
      <div style="text-align:center;margin-top:25px">
        <a href="{URL}" style="background:#2ecc40;color:white;padding:16px 32px;
           border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold">
          🗓️ Réserver maintenant</a>
      </div>
      <p style="color:#bbb;font-size:11px;margin-top:20px;text-align:center">
        Alerte automatique — GitHub Actions • Vérification toutes les 5 min
      </p>
    </div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚨 RDV Scanner Crâne — Créneau disponible !"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = ", ".join(EMAIL_DEST)
    msg.attach(MIMEText(corps_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_FROM, EMAIL_PASS)
            s.sendmail(EMAIL_FROM, EMAIL_DEST, msg.as_string())
        print(f"📧 Email envoyé à : {', '.join(EMAIL_DEST)}")
    except Exception as e:
        print(f"❌ Erreur email : {e}")
        sys.exit(1)

if __name__ == "__main__":
    print(f"🔍 Vérification EasyDoct — {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}")
    disponible, creneaux = verifier_disponibilite()
    if disponible:
        envoyer_alerte(creneaux)
        print("✅ ALERTE EMAIL ENVOYÉE !")
    else:
        print("😴 Pas de créneau — prochaine vérification dans 5 min")
