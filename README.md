# WordPress to Static Site Converter

Eine einfache aber funktionale Flask-Webanwendung, die WordPress-Websites vollständig als statische Kopien erfasst.

## Features

- 🌐 **Vollständige Website-Erfassung**: Alle öffentlichen Seiten, Posts und Kategorien
- 📱 **Asset-Download**: Automatisches Herunterladen von Bildern, CSS, JavaScript und Fonts
- 🔗 **Link-Rewriting**: Konvertierung interner URLs für lokale Navigation
- 📊 **Live-Fortschritt**: Echtzeit-Updates während des Scraping-Prozesses
- 📦 **ZIP-Export**: Download der kompletten statischen Website
- 🎨 **Responsive Design**: Moderne UI mit TailwindCSS

## Installation

1. **Repository klonen oder herunterladen**

2. **Virtuelle Umgebung erstellen (empfohlen)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder
   venv\Scripts\activate     # Windows
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Playwright Browser installieren**
   ```bash
   playwright install chromium
   ```

## Verwendung

1. **Anwendung starten**
   ```bash
   python app.py
   ```

2. **Browser öffnen**
   - Navigieren Sie zu: `http://localhost:5000`

3. **WordPress-Site scrapen**
   - URL eingeben (z.B. `https://beispiel-wordpress-site.com`)
   - "Scraping starten" klicken
   - Fortschritt live verfolgen
   - ZIP-Datei herunterladen

## Technischer Stack

- **Backend**: Python 3.11+, Flask, Flask-SocketIO
- **Frontend**: TailwindCSS (CDN), Vanilla JavaScript
- **Scraping**: Playwright (Chromium)
- **Parsing**: BeautifulSoup4
- **Storage**: Dateisystem

## Funktionsweise

### 1. URL-Discovery
- Prüfung der Sitemap.xml (falls vorhanden)
- Rekursive Erfassung interner Links
- Vermeidung von Dubletten

### 2. Asset-Handling
- Download aller Medien-Dateien innerhalb der Domain
- Anpassung der HTML-Pfade für lokale Navigation
- Erhaltung der ursprünglichen Ordnerstruktur

### 3. HTML-Processing
- Konvertierung interner Links zu relativen Pfaden
- Deaktivierung von Kontaktformularen
- Erhaltung der ursprünglichen Struktur und Formatierung

## Ausgabestruktur

```
scraped_sites/
└── domain-name/
    └── timestamp/
        ├── index.html
        ├── page/
        │   └── index.html
        ├── wp-content/
        │   └── uploads/
        │       └── images...
        └── wp-includes/
            └── assets...
```

## Einschränkungen

- Nur öffentlich zugängliche Inhalte werden erfasst
- Kontaktformulare werden deaktiviert (keine serverseitige Verarbeitung)
- Such-Funktionen funktionieren nicht (benötigen Datenbank)
- Kommentar-Systeme sind nicht funktional
- WordPress-Admin-Bereich ist nicht enthalten

## Beispiel-Workflow

1. Benutzer öffnet `http://localhost:5000`
2. Gibt WordPress-URL ein: `https://demo-wordpress-site.com`
3. Klickt "Scraping starten"
4. Sieht Live-Fortschritt der Erfassung
5. Nach Abschluss: Datei-Browser mit allen erfassten Inhalten
6. Lädt ZIP der kompletten statischen Site herunter

## Troubleshooting

### Playwright Installation
Falls Playwright-Fehler auftreten:
```bash
playwright install --force chromium
```

### Port bereits in Verwendung
Falls Port 5000 bereits belegt ist, ändern Sie in `app.py`:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

### Performance
- Größere Websites können länger dauern
- Bei sehr großen Sites ggf. Timeout erhöhen
- Scraping ist automatisch "respectful" (0.5s Pause zwischen Requests)

## Lizenz

MIT License - Frei für private und kommerzielle Nutzung.
