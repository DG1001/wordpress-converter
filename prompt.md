# WordPress to Static Site Converter - MVP

Erstelle eine einfache aber funktionale Python/Flask-Webanwendung, die WordPress-Websites vollständig als statische Kopien erfasst.

## Ziel
Eine GUI-basierte Anwendung, die eine WordPress-Site komplett herunterladen und als 1:1-Kopie speichern kann.

## Technischer Stack
- **Backend**: Python 3.11+, Flask
- **Frontend**: TailwindCSS (CDN-basiert für Einfachheit)
- **Scraping**: Playwright (für JavaScript-Rendering)
- **Storage**: Dateisystem (keine Datenbank)

## Kernfunktionen MVP

### 1. Einfache Web-GUI
- **Startseite**: URL-Eingabefeld und "Scraping starten" Button
- **Fortschritts-Seite**: Live-Updates während des Scraping-Prozesses
- **Ergebnis-Seite**: Datei-Browser und Download-Option
- **Responsive Design**: Funktional und sauber mit TailwindCSS

### 2. WordPress Scraper (Playwright)
```python
# Kern-Funktionalität:
- URL eingeben (z.B. https://example-wordpress-site.com)
- Alle Seiten der Domain erfassen
- Assets herunterladen (Bilder, CSS, JS innerhalb der Domain)
- Interne Links zu relativen Pfaden konvertieren
- Externe Links unverändert lassen
- Ordnerstruktur nachbilden
```

### 3. Scraping-Features
- **Vollständige Erfassung**: Alle Seiten, Posts, Kategorien
- **Asset-Download**: Bilder, Stylesheets, JavaScript, Fonts
- **Link-Rewriting**: Interne URLs lokalisieren
- **Strukturerhaltung**: Original-Pfade beibehalten
- **Fortschritts-Tracking**: Anzahl erfasster Seiten anzeigen

### 4. Datei-Management
- **Strukturierte Speicherung**: `scraped_sites/domain-name/timestamp/`
- **Einfacher Datei-Browser**: Navigierbare Ordnerstruktur
- **ZIP-Export**: Komplette Site als Download

## Spezifische Anforderungen

### Playwright-Konfiguration
```python
# Browser-Setup für WordPress:
- Headless-Modus für Performance
- User-Agent: Realistischen Browser simulieren
- JavaScript-Rendering aktiviert
- Cookies und Sessions handhaben
- 30-Sekunden Timeout pro Seite
```

### Link-Processing
```python
# URL-Konvertierung:
- https://example.com/page/ → ./page/index.html
- https://example.com/wp-content/uploads/image.jpg → ./wp-content/uploads/image.jpg
- Externe Links: unverändert
- Anchor-Links: erhalten
```

### Dateistruktur
```
wordpress-scraper-mvp/
├── app.py                 # Haupt-Flask-App
├── scraper.py            # Playwright-Scraper
├── templates/
│   ├── index.html        # URL-Eingabe
│   ├── progress.html     # Scraping-Fortschritt
│   └── result.html       # Datei-Browser
├── static/
│   └── style.css         # Minimales Custom CSS
├── scraped_sites/        # Output-Verzeichnis
└── requirements.txt
```

## UI-Anforderungen (Einfach aber funktional)

### Startseite (index.html)
- URL-Eingabefeld mit Validierung
- "Scraping starten" Button
- Kurze Anleitung/Hilfe

### Fortschritts-Seite (progress.html)
- Live-Updates via WebSocket oder AJAX
- Fortschrittsbalken
- Log-Ausgaben (gefundene URLs, heruntergeladene Dateien)
- "Abbrechen" Option

### Ergebnis-Seite (result.html)
- Datei-Browser (einfache Ordnerliste)
- Statistiken (Anzahl Seiten, Dateigröße)
- "ZIP herunterladen" Button
- "Neue Site scrapen" Link

## Scraping-Logik (Vereinfacht)

### 1. URL-Discovery
```python
# Sitemap.xml prüfen (falls vorhanden)
# Links von Startseite folgen
# Interne Links rekursiv erfassen
# Dubletten vermeiden
```

### 2. Asset-Handling
```python
# Alle src/href Attribute scannen
# Bilder, CSS, JS innerhalb der Domain herunterladen
# Pfade in HTML entsprechend anpassen
# Assets in ursprünglicher Struktur speichern
```

### 3. Form-Handling
```python
# Kontaktformulare: action="" setzen (deaktivieren)
# Input-Felder: beibehalten aber funktionslos
# Submit-Buttons: als normale Buttons
```

## Ausschlüsse für MVP
- Keine Datenbank (alles im Dateisystem)
- Keine KI-Integration
- Keine Benutzer-Accounts
- Keine komplexen Konfigurationen
- Keine Scheduling-Features

## Deliverables MVP
1. **Funktionierende Flask-App** (sofort ausführbar)
2. **Requirements.txt** mit allen Dependencies
3. **README.md** mit Setup-Anweisungen
4. **Einfache Tests** für Basis-Funktionalität

## Beispiel-Workflow
1. User öffnet http://localhost:5000
2. Gibt WordPress-URL ein: `https://demo-wordpress-site.com`
3. Klickt "Scraping starten"
4. Sieht Live-Fortschritt der Erfassung
5. Nach Abschluss: Datei-Browser mit allen erfassten Inhalten
6. Lädt ZIP der kompletten statischen Site herunter

**Fokus: Einfachheit, Funktionalität, solide Basis für spätere Erweiterungen.**