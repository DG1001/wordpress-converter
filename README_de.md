# WordPress to Static Site Converter

Eine umfassende Flask-Webanwendung, die WordPress-Websites in vollständig funktionale statische Kopien mit erweiterten Asset-Handling und Cookie-Banner-Entfernung konvertiert.

*🤖 Diese Anwendung wurde mit [XaresAICoder](https://github.com/DG1001/XaresAICoder) und Claude Code entwickelt*

🌍 **[English Documentation](README.md)** | 📖 **Deutsche Dokumentation**

## Features

- 🌐 **Vollständige Website-Erfassung**: Alle öffentlichen Seiten, Posts und Kategorien
- 📱 **Asset-Download**: Automatisches Herunterladen von Bildern, CSS, JavaScript und Fonts
- 🔗 **Zwei-Phasen Domain-Ersetzung**: 100% Konvertierung zu relativen Pfaden
- 📱 **Srcset-Unterstützung**: Responsive Bilder mit allen Auflösungsvarianten
- 🚫 **Erweiterte Cookiebot-Entfernung**: Vollständige Banner-Entfernung (85+ Elemente)
- ⚙️ **JavaScript-Navigation Schutz**: Erhaltung funktionaler Website-Navigation
- 📊 **Live-Fortschritt**: Echtzeit-Updates während des Scraping-Prozesses
- 📁 **File-Browser**: Navigation durch die komplette Website-Struktur
- 📦 **ZIP-Export**: Download der kompletten statischen Website
- 🎨 **Responsive Design**: Moderne UI mit TailwindCSS
- ⚡ **Query-Parameter Support**: Korrekte Behandlung von CSS/JS-Versionierung
- 🤖 **KI-gestützte Bearbeitung**: Bearbeitung gescrapeter Websites mit KI (DeepSeek Integration)
- 📚 **Projekt-Management**: Professionelles Dashboard mit Thumbnails und Favoriten
- 📸 **Automatische Screenshots**: Visuelle Vorschau gescrapeter Websites

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

5. **KI-Bearbeitung konfigurieren (optional)**
   ```bash
   # .env Datei erstellen und DeepSeek API Key hinzufügen
   echo "DEEPSEEK_API_KEY=ihr_api_key_hier" >> .env
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

### 3. HTML-Processing & Domain-Ersetzung

**Zwei-Phasen-Ansatz:**
- **Phase 1**: Vollständige Asset-Entdeckung und Download
- **Phase 2**: Nachbearbeitung aller HTML-Dateien für lokale Referenzen

**Intelligente Pfad-Konvertierung:**
- Root-Seiten: `./wp-content/uploads/image.jpg`
- Unterseiten: `../wp-content/uploads/image.jpg`  
- Tiefe Seiten: `../../wp-content/uploads/image.jpg`
- Srcset-Attribute: `./image-300w.jpg 300w, ./image-150w.jpg 150w`

**Erweiterte Cookiebot-Entfernung:**
- Externe Cookiebot-Scripts (`cookiebot.com`)
- Inline-Scripts mit >80% Cookiebot-Inhalt
- Cookiebot-IDs, -Klassen und data-Attribute
- Erhaltung funktionaler Navigation-Scripts

**Weitere Verbesserungen:**
- Query-Parameter-Behandlung (`style.css?ver=1.2.3`)
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

## KI-gestützte Website-Bearbeitung

Die Anwendung enthält jetzt eine KI-gestützte Bearbeitungsfunktion, mit der Sie gescrapete Websites mit natürlichsprachlichen Prompts bearbeiten können.

### Features
- **Natürlichsprachliche Befehle**: Beschreiben Sie Änderungen in einfachem Deutsch (z.B. "mache den Header moderner")
- **Intelligente Code-Analyse**: KI analysiert HTML/CSS-Struktur und wendet passende Änderungen an
- **Versionskontrolle**: Alle Änderungen werden mit Git-Commits verfolgt
- **Änderungshistorie**: Zeigen Sie alle Modifikationen mit Zeitstempeln und Commit-Nachrichten an
- **File-Browser**: Navigation durch Website-Struktur während der Bearbeitung

### Verwendung
1. **Website scrapen**: Scrapen Sie zuerst eine Website mit der Hauptfunktion
2. **Editor öffnen**: Klicken Sie "Mit KI bearbeiten" auf der Vorschau-Seite
3. **Prompt eingeben**: Beschreiben Sie gewünschte Änderungen im Textfeld
4. **Änderungen generieren**: KI analysiert den Code und wendet Modifikationen an
5. **Historie ansehen**: Betrachten Sie alle Änderungen im Historie-Panel

### Konfiguration
Um KI-Bearbeitung zu aktivieren, fügen Sie Ihren DeepSeek API-Schlüssel zur `.env` Datei hinzu:
```bash
DEEPSEEK_API_KEY=ihr_deepseek_api_key_hier
```

### Beispiel-Prompts
- "Mache die Website moderner mit einem dunklen Thema"
- "Ändere den Header-Hintergrund zu blau"
- "Füge abgerundete Ecken zu allen Buttons hinzu"
- "Verbessere die mobile Responsivität"
- "Aktualisiere die Typographie für eine professionellere Schrift"

## Projekt-Management Dashboard

Professionelles Projekt-Management-Interface mit:
- **Visuelle Thumbnails**: Automatische Screenshots gescrapeter Websites
- **Favoriten-System**: Wichtige Projekte für schnellen Zugriff markieren
- **Such-Funktionalität**: Projekte nach Name oder URL finden
- **Projekt-Statistiken**: Scraping-Statistiken und Dateigrößen anzeigen
- **Session-Historie**: Alle Scraping-Sessions pro Projekt verfolgen

## Kürzliche Verbesserungen (v2.1)

### ✅ Zwei-Phasen Domain-Ersetzung
- **Implementiert**: Vollständige Überarbeitung der Domain-Referenz-Behandlung
- **Phase 1**: Alle Assets vollständig entdecken und herunterladen
- **Phase 2**: HTML-Nachbearbeitung für lokale Pfad-Ersetzung
- **Ergebnis**: 100% Domain-Referenzen durch relative Pfade ersetzt

### ✅ Erweiterte Cookiebot-Entfernung
- **Problem gelöst**: Cookiebot-Banner wurden nicht vollständig entfernt
- **Neue Technik**: Aggressive Entfernung (85+ Elemente vs. vorher 6)
- **Intelligente Filterung**: Navigations-JavaScript bleibt erhalten
- **Ergebnis**: Vollständige Cookiebot-Entfernung ohne Funktionsverlust

### ✅ JavaScript-Navigation Schutz
- **Problem behoben**: Navigation-Menüs funktionierten nach Scraping nicht
- **Lösung**: Konservative Script-Analyse (nur >80% Cookiebot-Inhalt entfernt)
- **Erhaltung**: Responsive Navigation und Hamburger-Menüs bleiben funktional
- **Ergebnis**: Perfekte Navigation-Funktionalität in statischen Sites

### ✅ Srcset-Unterstützung
- **Neu**: Vollständige Responsive-Image-Unterstützung
- **Funktion**: Alle Bildvarianten (300w, 150w, etc.) werden gefunden und heruntergeladen
- **Relative Pfade**: Korrekte srcset-Verarbeitung für alle Seitenebenen
- **Ergebnis**: Responsive Bilder funktionieren offline perfekt

### ✅ Verbesserte Asset-Erkennung
- **Enhancement**: Query-Parameter-Behandlung (style.css?ver=1.2.3)
- **Intelligenz**: Dateierweiterung-basierte Asset-Erkennung
- **Abdeckung**: CSS, JS, Bilder, Fonts, Videos vollständig unterstützt
- **Ergebnis**: Keine fehlenden Assets mehr

### ✅ UI & Workflow-Verbesserungen  
- **Entfernt**: Defekte Preview-Buttons die nicht funktioniert haben
- **Verbessert**: File-Browser als zentrale Navigation
- **Workflow**: Klarer 8-Schritt-Prozess mit Qualitätskontrolle
- **Ergebnis**: Intuitive Benutzerführung mit funktionierender Navigation

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

## Entwicklung

Diese Anwendung wurde entwickelt mit:
- **[XaresAICoder](https://github.com/DG1001/XaresAICoder)**: KI-gestützte Entwicklungsumgebung
- **Claude Code**: Fortgeschrittener KI-Coding-Assistent
- **Kollaborative KI-Entwicklung**: Iterative Verbesserung durch KI-Mensch-Zusammenarbeit

### Technologie-Stack
- **Backend**: Flask mit SocketIO für Echtzeit-Kommunikation
- **Scraping**: Playwright für JavaScript-fähiges Browsing
- **HTML-Verarbeitung**: BeautifulSoup für Content-Manipulation
- **Frontend**: TailwindCSS für responsives Design
- **Asset-Handling**: Benutzerdefinierte Logik für WordPress-spezifische Patterns

### Wichtige technische Innovationen
- Zwei-Phasen Domain-Ersetzungs-Architektur
- Konservative JavaScript-Filterung für Navigation-Erhaltung
- Intelligente Asset-Validierung mit Konflikt-Resolution
- Echtzeit-Fortschritts-Tracking mit WebSocket-Kommunikation

## Beiträge

Beiträge sind willkommen! Bitte:
1. Repository forken
2. Feature-Branch erstellen
3. Gründlich mit echten WordPress-Sites testen
4. Pull Request mit detaillierter Beschreibung einreichen

## Lizenz

MIT License - Frei für private und kommerzielle Nutzung.

---

*Entwickelt mit ❤️ unter Verwendung von KI-gestützten Entwicklungstools*
