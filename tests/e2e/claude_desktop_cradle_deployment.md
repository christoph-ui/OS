# Claude Desktop E2E Test: Cradle Client Deployment

**Test ID**: E2E-CRADLE-001
**Datum**: 2026-01-28
**Zweck**: Kompletter Deployment-Flow via Admin Portal (mit Browser-Automatisierung)
**Dauer**: ~25 Minuten (5 min Formular, 20 min Build)

---

## 🎯 Test-Ziel

Als **Platform Admin** über das Admin Portal einen neuen Kunden deployen:
1. Einloggen als Admin
2. Cradle Deployments öffnen
3. Neuen Client erstellen (mit Eaton-Testdaten)
4. Deployment starten
5. Build abwarten
6. Image downloaden
7. Erfolg verifizieren

**Erwartetes Ergebnis**: Neuer Docker-Image `testclient-v1.0.tar.gz` (~1.8GB) erfolgreich erstellt und heruntergeladen.

---

## ✅ Voraussetzungen

### Services müssen laufen:

```bash
# 1. Cradle Services
docker ps | grep cradle
# Erwarte: cradle-embeddings, cradle-vision, cradle-installation-db, cradle-image-builder

# 2. Control Plane API
curl http://localhost:4080/health
# Erwarte: {"status": "healthy"}

# 3. Console Frontend
curl http://localhost:4020
# Erwarte: HTML (200 OK)

# 4. Test-Daten vorbereiten (Eaton-Kopie)
ls -la /tmp/testclient-data/processed/lakehouse
# Muss existieren mit Delta-Tables
```

### Test-Daten vorbereiten:

```bash
# Kopiere Eaton-Daten als Test-Daten
mkdir -p /tmp/testclient-data/processed
cp -r /home/christoph.bertsch/0711/deployments/eaton/lakehouse /tmp/testclient-data/processed/
cp -r /home/christoph.bertsch/0711/deployments/eaton/minio /tmp/testclient-data/processed/

# Verifiziere
du -sh /tmp/testclient-data/processed/lakehouse
# Erwarte: ~300-400MB
```

---

## 🌐 E2E Test Script (für Claude Desktop)

### SCHRITT 1: Browser öffnen und Admin Login

**Action**: Öffne Chrome und navigiere zu:
```
http://localhost:4020/admin/login
```

**Erwarte**:
- Admin Login-Seite mit rotem Shield-Icon
- Titel: "Admin Portal"
- Email/Password Felder sichtbar

**Action**: Fülle Login-Formular aus:
- Email: `admin@0711.io`
- Password: `admin123`

**Action**: Klicke "Login" Button

**Erwarte**:
- Redirect zu: `http://localhost:4020/admin`
- Admin Dashboard sichtbar
- Sidebar mit Navigation

**Verifikation**:
- [ ] URL ist `/admin` (Dashboard)
- [ ] Sidebar zeigt: Dashboard, Customers, **Deployments**, MCPs, Developers, Health
- [ ] Keine Fehlermeldung

**Screenshot**: Save as `01_admin_login_success.png`

---

### SCHRITT 2: Navigate zu Deployments

**Action**: Klicke in Sidebar auf "Deployments"

**Erwarte**:
- URL: `http://localhost:4020/admin/deployments`
- Seiten-Titel: "Cradle Deployments"
- Untertitel: "GPU Processing Central • Client Console Builder"
- Button: "+ Deploy New Client" (rechts oben)

**Erwarte**: Service Status Cards sichtbar
- **Embeddings** - Port 8001 - Status: HEALTHY (grün)
- **Vision** - Port 8002 - Status: HEALTHY (grün)
- **Installation DB** - Port 5433 - Status: HEALTHY (grün)

**Erwarte**: Customer Installations Table
- Header: Customer ID, Company, Target, MCPs, Stats, Deployed, Actions
- Zeile: `eaton` | EATON | on-premise | ctax, law, etim | 52 files, 52 embeddings | [Date] | [Download]

**Verifikation**:
- [ ] 3 Service Cards alle grün
- [ ] Mindestens 1 Installation (EATON) in Tabelle
- [ ] Download-Button sichtbar

**Screenshot**: Save as `02_deployments_page.png`

---

### SCHRITT 3: Deploy Form öffnen

**Action**: Klicke "+ Deploy New Client" Button (rechts oben)

**Erwarte**:
- Modal öffnet sich (overlay mit Formular)
- Titel: "Deploy New Client"
- Close-Button (X) rechts oben

**Erwarte Formular-Felder**:
1. Company Name * (required)
2. Contact Email * (required)
3. Data Sources * (required, comma-separated paths)
4. Deployment Target (dropdown: On-Premise, Cloud, Hybrid)
5. Enabled MCPs (checkboxes: CTAX, LAW, ETIM, TENDER, MARKET, PUBLISH)
6. Submit-Button: "Deploy Customer Console"
7. Info-Text: "Build will run in background (~15-20 minutes)"

**Verifikation**:
- [ ] Modal sichtbar
- [ ] Alle Felder vorhanden
- [ ] CTAX, LAW, ETIM standardmäßig ausgewählt

**Screenshot**: Save as `03_deploy_form_empty.png`

---

### SCHRITT 4: Formular ausfüllen

**Action**: Fülle Formular mit Test-Daten aus:

**Company Name**:
```
Test Client GmbH
```

**Contact Email**:
```
admin@testclient.com
```

**Data Sources** (WICHTIG - exakter Pfad!):
```
/tmp/testclient-data/processed
```

**Deployment Target**:
```
On-Premise (already selected)
```

**Enabled MCPs**:
- [x] CTAX (checked)
- [x] LAW (checked)
- [x] ETIM (checked)
- [ ] TENDER (unchecked)
- [ ] MARKET (unchecked)
- [ ] PUBLISH (unchecked)

**Verifikation**:
- [ ] Alle Felder ausgefüllt
- [ ] Data Sources Pfad existiert (kein Tippfehler!)
- [ ] 3 MCPs ausgewählt

**Screenshot**: Save as `04_deploy_form_filled.png`

---

### SCHRITT 5: Deployment starten

**Action**: Klicke "Deploy Customer Console" Button

**Erwarte während Deployment**:
- Button zeigt: "Deploying..." (disabled)
- Button-Farbe ändert sich zu grau

**Erwarte nach ~5-30 Sekunden**:
- Success-Nachricht erscheint (grüner Kasten):
  ```
  ✓ Deployment Started
  Building in background (~15-20 min)
  ```
- Modal schließt sich nach Success-Message
- ODER: Fehler-Nachricht (roter Kasten) falls Problem

**Mögliche Fehler** (Claude Desktop soll reagieren):
- "Data path not found" → Pfad-Tippfehler, korrigieren
- "Lakehouse directory required" → lakehouse/ fehlt in /tmp/testclient-data/processed/
- "Failed to save config" → Cradle DB nicht erreichbar (port 5433)
- "Build failed" → Siehe Backend-Logs

**Verifikation**:
- [ ] Grüne Success-Nachricht erscheint
- [ ] KEIN roter Fehler
- [ ] Modal schließt automatisch ODER kann geschlossen werden

**Screenshot**: Save as `05_deployment_started.png`

---

### SCHRITT 6: Installations-Tabelle aktualisieren

**Action**: Warte 5 Sekunden, dann klicke "Refresh" Button

**Erwarte**:
- Neue Zeile in Tabelle: `testclient` | Test Client GmbH | on-premise | ctax, law, etim | ...

**ODER** (wenn Build noch läuft):
- Noch keine neue Zeile (Build läuft im Hintergrund)
- Stats zeigen: 0 files, 0 embeddings (noch nicht fertig)

**Action**: Klicke erneut "Refresh" alle 60 Sekunden

**Erwarte nach ~15-20 Minuten**:
- Neue Zeile: `testclient` erscheint
- Stats zeigen: ~52 files, ~52 embeddings (von Eaton-Testdaten übernommen)
- Download-Button aktiv

**Verifikation**:
- [ ] Neue Installation in Tabelle
- [ ] customer_id = "testclient"
- [ ] company_name = "Test Client GmbH"
- [ ] deployment_target = "on-premise"
- [ ] enabled_mcps = "ctax, law, etim"

**Screenshot**: Save as `06_installation_completed.png`

---

### SCHRITT 7: Image downloaden

**Action**: Klicke "Download" Button in der `testclient` Zeile

**Erwarte**:
- Browser startet Download
- Dateiname: `testclient-v1.0.tar.gz`
- Größe: ~1.5-2.0 GB (kann 30-60 Sekunden dauern)

**Erwarte Browser-Download**:
- Download startet automatisch
- Download-Bar unten im Browser
- Datei landet in ~/Downloads/

**Mögliche Fehler**:
- "Image archive not found" → Build hat Image nicht gespeichert
- 404 Error → Image existiert nicht in /docker-images/customer/
- Timeout → Image zu groß, Netzwerk langsam (normal, warten)

**Verifikation**:
- [ ] Download startet
- [ ] Datei: `testclient-v1.0.tar.gz`
- [ ] Größe: >500MB (mindestens)

**Screenshot**: Save as `07_download_started.png`

---

### SCHRITT 8: Download verifizieren

**Action**: Warte bis Download komplett (kann 1-3 Minuten dauern)

**Action**: Öffne Terminal und verifiziere:

```bash
# 1. Prüfe Download
ls -lh ~/Downloads/testclient-v1.0.tar.gz
# Erwarte: 1.5-2.0G

# 2. Prüfe Datei-Integrität
file ~/Downloads/testclient-v1.0.tar.gz
# Erwarte: gzip compressed data

# 3. Test: Image laden (ohne zu starten)
docker load < ~/Downloads/testclient-v1.0.tar.gz
# Erwarte: Loaded image: testclient-intelligence:1.0

# 4. Verifiziere Image
docker images | grep testclient
# Erwarte: testclient-intelligence  1.0  ...  4.2GB  ...
```

**Verifikation**:
- [ ] Datei vollständig heruntergeladen
- [ ] Datei ist gzip-komprimiert
- [ ] Docker kann Image laden
- [ ] Image-Größe: 3-5GB (unkomprimiert)

**Screenshot**: Save as `08_docker_image_loaded.png`

---

### SCHRITT 9: Image-Inhalt verifizieren

**Action**: Starte temporären Container zum Testen:

```bash
# Starte Container (ohne persistent deployment)
docker run --rm -d \
  --name testclient-verify \
  -p 9400:9312 \
  -p 9401:9313 \
  -p 9402:9314 \
  testclient-intelligence:1.0

# Warte auf Startup
sleep 90

# Test Lakehouse
curl http://localhost:9400/health
# Erwarte: {"status":"healthy", ...}

# Test Backend
curl http://localhost:9401/health
# Erwarte: {"status":"healthy", "customer_id":"testclient", ...}

# Test Frontend
curl -I http://localhost:9402
# Erwarte: HTTP/1.1 200 OK

# Prüfe Daten
curl http://localhost:9400/stats
# Erwarte: Lakehouse mit Delta-Tables + Embeddings

# Cleanup
docker stop testclient-verify
```

**Verifikation**:
- [ ] Alle 3 Services starten (Lakehouse, Backend, Frontend)
- [ ] Health-Checks grün
- [ ] Lakehouse hat Daten (von Eaton übernommen)
- [ ] Container läuft fehlerfrei

**Screenshot**: Save as `09_container_running.png`

---

### SCHRITT 10: Cleanup

**Action**: Räume Test-Daten auf:

```bash
# 1. Docker Image entfernen (wenn Test OK)
docker rmi testclient-intelligence:1.0

# 2. Test-Daten entfernen
rm -rf /tmp/testclient-data

# 3. Download entfernen (optional)
rm ~/Downloads/testclient-v1.0.tar.gz

# 4. Cradle DB-Eintrag entfernen (optional)
docker exec cradle-installation-db psql -U cradle -d installation_configs \
  -c "DELETE FROM installation_configs WHERE customer_id='testclient';"
```

**Verifikation**:
- [ ] Test-Daten gelöscht
- [ ] System sauber (keine Test-Reste)

---

## 📋 Claude Desktop Test-Instruktionen

### Vorbereitung (Claude Desktop ausführen):

```bash
# Terminal öffnen und Test-Daten vorbereiten
mkdir -p /tmp/testclient-data/processed
cp -r /home/christoph.bertsch/0711/deployments/eaton/lakehouse /tmp/testclient-data/processed/
cp -r /home/christoph.bertsch/0711/deployments/eaton/minio /tmp/testclient-data/processed/

# Verifiziere
ls -la /tmp/testclient-data/processed/lakehouse
# Muss Delta-Tables enthalten
```

### Browser-Test (Claude Desktop Browser Automation):

**Schritt 1**: Öffne `http://localhost:4020/admin/login`

**Schritt 2**: Login:
- Email-Feld: Tippe `admin@0711.io`
- Password-Feld: Tippe `admin123`
- Klicke "Login" Button
- **Warte 2 Sekunden**

**Schritt 3**: Navigiere zu Deployments:
- Klicke in Sidebar auf "Deployments"
- **Warte 2 Sekunden** (Seite lädt Daten)

**Schritt 4**: Verifiziere Service Status:
- Prüfe: 3 Service Cards sichtbar (Embeddings, Vision, Installation DB)
- Prüfe: Alle zeigen grünes Häkchen (HEALTHY)
- Falls **rot** (UNHEALTHY): Test abbrechen, Services prüfen

**Schritt 5**: Öffne Deploy-Form:
- Klicke "+ Deploy New Client" Button
- **Warte 1 Sekunde**
- Modal erscheint

**Schritt 6**: Fülle Formular aus:
- **Company Name**: Klicke Feld, tippe `Test Client GmbH`
- **Contact Email**: Klicke Feld, tippe `admin@testclient.com`
- **Data Sources**: Klicke Feld, tippe `/tmp/testclient-data/processed`
- **Deployment Target**: Lass auf "On-Premise" (default)
- **Enabled MCPs**: Lass CTAX, LAW, ETIM checked (default)

**Schritt 7**: Submit Deployment:
- Klicke "Deploy Customer Console" Button
- **Warte 10-30 Sekunden** (API-Call)

**Schritt 8**: Prüfe Ergebnis:
- **Falls grüne Success-Box erscheint**: ✅ Weiter zu Schritt 9
- **Falls rote Error-Box erscheint**: ❌ Test fehlgeschlagen
  - Screenshot der Fehlermeldung
  - Test abbrechen

**Schritt 9**: Modal schließen (falls noch offen):
- Klicke X-Button oder klicke außerhalb Modal

**Schritt 10**: Warte auf Build-Completion:
- Klicke "Refresh" Button alle 60 Sekunden
- **Insgesamt 20x wiederholen** (= 20 Minuten)
- Prüfe nach jedem Refresh: Ist `testclient` in Tabelle?

**Schritt 11**: Wenn `testclient` erscheint:
- Klicke "Download" Button in `testclient` Zeile
- **Warte** bis Download komplett (1-3 Minuten)
- Datei landet in ~/Downloads/testclient-v1.0.tar.gz

**Schritt 12**: Verifiziere Download im Terminal:
```bash
ls -lh ~/Downloads/testclient-v1.0.tar.gz
file ~/Downloads/testclient-v1.0.tar.gz
```

**Schritt 13**: Test abschließen:
- Screenshot: `10_test_complete.png`
- Browser schließen

---

## 🤖 Claude Desktop Prompts

### Prompt 1: Test starten

```
Bitte führe den E2E-Test aus:
/home/christoph.bertsch/0711/0711-OS/tests/e2e/claude_desktop_cradle_deployment.md

Verwende Chrome Browser Automation.
Mache Screenshots bei jedem Schritt.
Logge alle Aktionen und Ergebnisse.
Bei Fehlern: Stoppe und berichte Details.
```

### Prompt 2: Bei Fehler

```
Der Test ist bei Schritt X fehlgeschlagen.
Fehler: [Fehlermeldung aus UI]

Bitte:
1. Screenshot des Fehlers machen
2. Browser Console öffnen (F12)
3. JavaScript Fehler prüfen
4. Network Tab prüfen (welcher API-Call failed?)
5. Backend-Logs prüfen:
   docker logs 0711-api 2>&1 | tail -50
6. Berichte alle Findings
```

### Prompt 3: Erfolgreiche Completion

```
E2E-Test erfolgreich abgeschlossen!

Bitte erstelle Test-Report:
1. Alle Screenshots zusammenfassen
2. Dauer messen (Start bis Download komplett)
3. Ergebnisse verifizieren (Image-Größe, etc.)
4. Test-Summary schreiben
```

---

## 📊 Erwartete Ergebnisse

### Timing
- **Login**: <2 Sekunden
- **Navigate**: <2 Sekunden
- **Form Fill**: ~30 Sekunden (manuell) oder ~5 Sekunden (automatisiert)
- **API Submit**: 10-30 Sekunden
- **Build**: 15-20 Minuten (Background)
- **Download**: 1-3 Minuten
- **Total**: ~20-25 Minuten

### Datei-Größen
- Test-Daten Input: ~300-400MB (Eaton lakehouse)
- Docker Image: ~4.2GB (unkomprimiert)
- Archive: ~1.5-2.0GB (komprimiert)

### API Calls (zu loggen)
1. `POST /api/admin/login` → 200 OK
2. `GET /api/admin/cradle/installations` → 200 OK (EATON)
3. `GET /api/admin/cradle/services` → 200 OK (3 services healthy)
4. `POST /api/orchestrator/initialize-customer` → 200 OK (deployment started)
5. `GET /api/admin/cradle/installations` (refresh, 20x) → 200 OK (testclient erscheint)
6. `GET /api/admin/cradle/images/testclient/download` → 200 OK (file download)

---

## ✅ Success Criteria

**Test PASSED wenn**:
- [x] Admin Login erfolgreich
- [x] Deployments-Seite lädt
- [x] Service Status alle grün (healthy)
- [x] EATON Installation sichtbar
- [x] Deploy-Form öffnet
- [x] Form-Submit ohne Fehler
- [x] Success-Message erscheint
- [x] Nach ~20 Minuten: `testclient` in Tabelle
- [x] Download funktioniert
- [x] Datei: testclient-v1.0.tar.gz (~1.8GB)
- [x] Docker kann Image laden
- [x] Container startet erfolgreich

**Test FAILED wenn**:
- [ ] Login scheitert
- [ ] Service Status rot
- [ ] Deploy-Form Fehler
- [ ] API-Call gibt 500/400 Error
- [ ] Build schlägt fehl
- [ ] Keine neue Installation nach 30 Minuten
- [ ] Download fehlschlägt
- [ ] Image ist korrupt

---

## 🐛 Troubleshooting Guide (für Claude Desktop)

### Problem: Services nicht erreichbar

**Symptom**: Rote Service-Status-Cards

**Fix**:
```bash
# Prüfe Cradle Services
cd /home/christoph.bertsch/0711/0711-cradle
docker compose -f docker-compose.cradle.yml ps

# Falls down: Starte neu
docker compose -f docker-compose.cradle.yml up -d

# Warte 60 Sekunden, dann Refresh im Browser
```

### Problem: "Data path not found"

**Symptom**: Rote Fehlermeldung beim Submit

**Fix**:
```bash
# Prüfe ob Pfad existiert
ls -la /tmp/testclient-data/processed/lakehouse

# Falls nicht: Erstelle Test-Daten
cp -r /home/christoph.bertsch/0711/deployments/eaton/lakehouse /tmp/testclient-data/processed/
```

### Problem: Build läuft ewig (>30 min)

**Symptom**: Keine neue Installation nach 30 Minuten

**Fix**:
```bash
# Prüfe Backend-Logs
docker logs 0711-api 2>&1 | grep -i "testclient"

# Prüfe ob Build läuft
docker ps | grep testclient

# Prüfe Build-Directory
ls -la /tmp/testclient-build

# Manuell prüfen was passiert ist
```

### Problem: Download startet nicht

**Symptom**: Klick auf Download-Button tut nichts

**Fix**:
```bash
# Prüfe ob Image existiert
ls -la /home/christoph.bertsch/0711/docker-images/customer/testclient-v1.0.tar.gz

# Falls nicht: Build hat Export übersprungen
# Manuell exportieren:
docker save testclient-intelligence:1.0 | gzip > ~/testclient-v1.0.tar.gz
```

---

## 📸 Screenshot-Checkliste

Claude Desktop soll diese Screenshots machen:

- [ ] `01_admin_login_success.png` - Nach Login, Dashboard sichtbar
- [ ] `02_deployments_page.png` - Deployments-Seite mit EATON
- [ ] `03_deploy_form_empty.png` - Leeres Deploy-Formular
- [ ] `04_deploy_form_filled.png` - Ausgefülltes Formular
- [ ] `05_deployment_started.png` - Success-Nachricht
- [ ] `06_installation_completed.png` - testclient in Tabelle
- [ ] `07_download_started.png` - Browser-Download aktiv
- [ ] `08_docker_image_loaded.png` - Terminal: docker images
- [ ] `09_container_running.png` - Container health checks
- [ ] `10_test_complete.png` - Final Summary

**Speichere in**: `/home/christoph.bertsch/0711/0711-OS/tests/e2e/screenshots/cradle-deployment-YYYYMMDD/`

---

## 📊 Test Report Template

Nach Test-Completion soll Claude Desktop diesen Report erstellen:

```markdown
# E2E Test Report: Cradle Client Deployment

**Test ID**: E2E-CRADLE-001
**Datum**: 2026-01-28
**Tester**: Claude Desktop (Browser Automation)
**Dauer**: XX Minuten
**Status**: ✅ PASSED / ❌ FAILED

## Test-Ablauf

### Schritt 1: Admin Login
- Dauer: X Sekunden
- Status: ✅ SUCCESS
- Screenshot: 01_admin_login_success.png

### Schritt 2: Navigate zu Deployments
- Dauer: X Sekunden
- Status: ✅ SUCCESS
- Installations gefunden: 1 (EATON)
- Services healthy: 3/3
- Screenshot: 02_deployments_page.png

### Schritt 3-5: Deploy Form
- Dauer: X Sekunden
- Status: ✅ SUCCESS
- Daten: Test Client GmbH, /tmp/testclient-data/processed
- Screenshots: 03-05

### Schritt 6: Build Monitoring
- Dauer: X Minuten
- Status: ✅ SUCCESS
- Refresh-Zyklen: X (alle 60s)
- Installation erschien nach: X Minuten
- Screenshot: 06

### Schritt 7-8: Download
- Dauer: X Minuten
- Status: ✅ SUCCESS
- Datei-Größe: X.XGB
- Screenshot: 07-08

### Schritt 9: Verifikation
- Status: ✅ SUCCESS
- Image geladen: ✅
- Container gestartet: ✅
- Services healthy: ✅
- Screenshot: 09

## Ergebnisse

- Docker Image: testclient-intelligence:1.0 (X.XGB)
- Archive: testclient-v1.0.tar.gz (X.XGB)
- Build-Zeit: X Minuten
- Download-Zeit: X Minuten
- **Total Zeit**: X Minuten

## Probleme

[Keine / Liste aller Probleme]

## Empfehlung

✅ Test PASSED - Cradle Admin Integration funktioniert end-to-end
```

---

## 🎯 Test-Completion Criteria

**Minimale Erfolgs-Kriterien**:
- [ ] Login funktioniert
- [ ] Deployments-Seite lädt
- [ ] Services zeigen grün
- [ ] Form kann ausgefüllt werden
- [ ] Deployment startet ohne Fehler
- [ ] Neue Installation erscheint (auch wenn Build lange dauert)

**Vollständiger Erfolg**:
- [ ] Alle obigen Kriterien
- [ ] Build completet in <25 Minuten
- [ ] Download funktioniert
- [ ] Image ist lauffähig
- [ ] Alle 10 Screenshots gemacht
- [ ] Test-Report erstellt

---

## 🚀 Claude Desktop Kommando

**Zum Starten des Tests**:

```
Führe E2E-Test aus:
File: /home/christoph.bertsch/0711/0711-OS/tests/e2e/claude_desktop_cradle_deployment.md

Verwende Chrome Browser mit Computer-Use.
Mache Screenshots bei jedem Schritt.
Wenn Fehler: Stoppe und berichte.
Wenn Success: Erstelle Test-Report.

Starte jetzt!
```

---

**Test Ready!** Claude Desktop kann diesen Test jetzt end-to-end durchführen! 🎉
