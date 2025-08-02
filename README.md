# WordPress to Static Site Converter

Eine einfache aber funktionale Flask-Webanwendung, die WordPress-Websites vollständig als statische Kopien erfasst.

## Features

- 🌐 **Vollständige Website-Erfassung**: Alle öffentlichen Seiten, Posts und Kategorien
- 📱 **Asset-Download**: Automatisches Herunterladen von Bildern, CSS, JavaScript und Fonts
- 🔗 **Intelligente Pfad-Konvertierung**: Korrekte relative Pfade für alle Seitenebenen
- 🚫 **Cookie-Banner Entfernung**: Automatische Erkennung und Entfernung von Cookie-Bannern
- 📊 **Live-Fortschritt**: Echtzeit-Updates während des Scraping-Prozesses
- 📁 **File-Browser**: Navigation durch die komplette Website-Struktur
- 📦 **ZIP-Export**: Download der kompletten statischen Website
- 🎨 **Responsive Design**: Moderne UI mit TailwindCSS
- ⚡ **Konflikt-Vermeidung**: Intelligente Behandlung von Pfad-Konflikten zwischen Seiten und Assets

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
- **Intelligente Pfad-Konvertierung**: Korrekte relative Pfade basierend auf Seitentiefe
  - Root-Seiten: `./wp-content/uploads/image.jpg`
  - Unterseiten: `../wp-content/uploads/image.jpg`
  - Tiefe Seiten: `../../wp-content/uploads/image.jpg`
- **Cookie-Banner Entfernung**: Automatische Erkennung und Entfernung häufiger Cookie-Banner
- **Asset-Validierung**: Unterscheidung zwischen Seiten und Assets zur Konflikt-Vermeidung
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
4. Sieht Live-Fortschritt der Erfassung mit detaillierten Logs
5. Nach Abschluss: Ergebnis-Seite mit Statistiken
6. **Browse Files**: Navigation durch die Website-Struktur im Browser
7. **ZIP Download**: Download der kompletten statischen Site
8. **Qualitätskontrolle**: Testen der Seiten vor dem finalen Deployment

## Kürzliche Verbesserungen (v2.0)

### ✅ Pfad-Korrekturen
- **Problem behoben**: Assets hatten falsche relative Pfade auf Unterseiten
- **Lösung**: Intelligente Tiefenberechnung für korrekte `../` Pfade
- **Ergebnis**: Logos, CSS und Bilder laden nun korrekt auf allen Seiten

### ✅ Konflik-Resolution
- **Problem behoben**: "Pfad-Konflikt erkannt" Meldungen eliminiert
- **Lösung**: Bessere Unterscheidung zwischen Seiten und Assets
- **Ergebnis**: Sauberes Scraping ohne Pfad-Kollisionen

### ✅ UI-Verbesserungen
- **Entfernt**: Defekte Preview-Buttons die nicht funktioniert haben
- **Verbessert**: File-Browser als zentrale Navigation
- **Ergebnis**: Intuitivere Benutzerführung mit funktionierender Navigation

### ✅ Cookie-Banner Entfernung
- **Neu**: Automatische Erkennung deutscher und englischer Cookie-Banner
- **Umfang**: 20+ häufige Cookie-Plugin Patterns unterstützt
- **Ergebnis**: Saubere statische Sites ohne störende Banner

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
