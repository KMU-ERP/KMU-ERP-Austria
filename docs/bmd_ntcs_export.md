# BMD-NTCS-Export – Einrichtung und Betrieb

Stand: 21.08.2026

Das Modul `BMD Export` erzeugt aus eingereichten Sales und Purchase Invoices eine BMD-konforme `buchungen.csv` und ein flaches Transport-ZIP mit den referenzierten Belegen. Fachliche Grundlage sind die BMD-Onlinehilfe „Buchungen importieren“ und das offizielle Gesamtbeispiel 2026.

Die Anleitung ist auch direkt im Desk verfügbar: In der linken Navigation des Moduls `BMD Export` stehen Startseite, Export-Assistent, Export-Batches, Einstellungen und Hilfe direkt zur Auswahl. Die Kapitelnavigation innerhalb der Hilfe führt zu Einrichtung, Mappings, Dateinamen, Export, BMD-Import und Fehlerbehebung. Assistent, Einstellungen und Batches besitzen ebenfalls einen Hilfe-Button.

## Oberfläche und Sprache

Alle BMD-Formulare verwenden ein gemeinsames responsives Kartendesign. Die linke Modulnavigation zeigt für Assistent, Exportläufe, Einstellungen, Hilfe, Profile, Konten, Zuordnungen und Prüfbericht jeweils ein eigenes Symbol. Kurze Hilfetexte unter den Konfigurationsfeldern erläutern Zweck und Auswirkung der Einstellung.

Die Quellsprache und Standardsprache des Moduls ist Englisch. Ist beim ERPNext-Benutzer im Feld `Language` Deutsch (`de`) ausgewählt, übersetzt Frappe Navigation, Formulare, Auswahlwerte, Hilfe, Aktionen und BMD-Fehlermeldungen automatisch ins Deutsche. Nach einer Sprachänderung muss der Desk neu geladen werden.

## Installation

```sh
cd /workspace/development/development/frappe-bench
bench --site <site> migrate
bench build --app kmu_erp_austria
```

`migrate` legt das Modul, die Rollen `BMD Export User` und `BMD Export Manager`, alle DocTypes, Page, Report, Workspace und das unveränderliche Standardprofil `BMD NTCS Standard` idempotent an.

## Ersteinrichtung je Company

1. Einen Datensatz `BMD Export Settings` für die Company anlegen und das Standardprofil oder eine Kopie davon auswählen.
2. Den BMD-Kontenplan in `BMD Account` über „Import XLSX/CSV“ zuerst als Vorschau prüfen und danach importieren. Bereits vorhandene Konten werden nicht überschrieben.
3. Eindeutige `BMD Account Mapping` und `BMD Party Mapping` anlegen.
4. Je Richtung, Steuersatz und Steuerfall ein `BMD Tax Mapping` anlegen. Für normale Umsatz-/Vorsteuer ist die Steuer im Bruttobetrag enthalten. Für ig. Erwerb, Reverse Charge und Bausteuer wird die ausgabeseitige Komponente exportiert und nicht zum offenen Rechnungsbetrag addiert.
5. Verwendete Cost Center, Projects und Accounting Dimensions über `BMD Dimension Mapping` abbilden.
6. Den Report `BMD Missing Mappings` für den ersten Exportzeitraum ausführen.

Fehlende oder gleichrangig mehrdeutige Mappings blockieren die Vorschau. Eine gleiche Kontonummer in ERPNext und BMD wird nie automatisch als Mapping interpretiert.

## Globale Jinja-Dateinamen

`document_filename_template` in den Company-Einstellungen wird bei jedem neuen Export auf jeden direkt verknüpften Anhang und auf ein optional erzeugtes Sales-Invoice-PDF angewandt. Das Template liefert nur den Stamm; die geprüfte Originalerweiterung wird automatisch angehängt.

Beispiel:

```jinja
{{ invoice_number }}-{{ party_name }}
```

Damit wird die Exportkopie von `test.pdf` beispielsweise zu `AR-2026-0042-Musterkunde.pdf`. Der originale ERPNext-`File`-Datensatz wird weder umbenannt noch verschoben. Der endgültige kollisionsfreie Name steht identisch in der CSV-Spalte `dokument` und im ZIP.

Freigegebene Variablen:

- `company`
- `voucher_type`, `voucher_type_code`, `voucher_name`
- `invoice_number`, `external_invoice_number`, `bill_no`
- `posting_date_yyyymmdd`
- `party`, `party_name`
- `return_against`
- `attachment_no`
- `original_stem`, `extension`

Das Jinja läuft in einer Sandbox mit `StrictUndefined`. Dokumentobjekte, Datenbankzugriffe, `frappe`, Attribute und aufrufbare Funktionen stehen nicht zur Verfügung. Pfade, Steuerzeichen und Windows-/ZIP-gefährliche Zeichen werden entfernt. Unbekannte Variablen, leere Resultate, nicht darstellbare Zeichen im gewählten CSV-Encoding und Namen über der BMD-Grenze blockieren die Vorschau. Über den Button „Test Attachment Filename“ kann das Template mit `test.pdf` geprüft werden.

## Exportablauf

1. Im Workspace `BMD Export` den `BMD Export Assistant` öffnen.
2. Company, Zeitraum und Belegarten wählen und die Vorschau erstellen.
3. Batch Items, Summen, Dokumentnamen, Fehler und Warnungen kontrollieren.
4. Einen Batch im Status `Ready` über „Generate Export“ starten.
5. Nach Status `Completed` CSV oder Transport-ZIP über die privaten Attach-Felder herunterladen.

Der Job prüft unmittelbar vor der Erzeugung alle Voucher-, Settings-, Profil-, Mapping- und Dokumentfingerprints erneut. Geänderte Daten verlangen eine neue Vorschau. Ein Redis-Lock verhindert Doppelstarts. Abgeschlossene Batches, Snapshots, Hashes und Batch Items sind unveränderlich. Ein Manager-Re-Export erzeugt eine getrennte Revision mit exakt den Vouchern der ersetzten Revision; der alte Batch wird erst nach erfolgreicher Erzeugung als `Superseded` markiert.

Der tägliche Aufbewahrungsjob entfernt nach den je Company konfigurierten `retention_days` ausschließlich die privaten CSV-/ZIP-Artefakte. Hashes, Snapshots, Batch Items und ein Löschprotokoll bleiben erhalten.

Wichtig für BMD NTCS: Das ZIP ist nur ein Transportpaket. ZIP entpacken und beim Buchungsimport ausschließlich `buchungen.csv` auswählen. Die Dokumente müssen beim Import im gleichen entpackten Ordner liegen.

## Fehlercodes

- `MISSING_MAPPING`: kein gültiges Mapping zum Belegdatum
- `AMBIGUOUS_MAPPING`: mehrere gleichrangige Treffer
- `AMBIGUOUS_TAX_COMPONENT`: nicht genau eine Steuerkomponente ist als BMD-Komponente markiert
- `ATTACHMENT_REQUIRED`, `ATTACHMENT_EMPTY`, `ATTACHMENT_TOO_LARGE`
- `ATTACHMENT_EXTENSION_NOT_ALLOWED`, `ATTACHMENT_MIME_NOT_ALLOWED`, `ATTACHMENT_MIME_MISMATCH`
- `ATTACHMENT_UNREADABLE`, `PDF_GENERATION_FAILED`
- `NET_RECONCILIATION_FAILED`, `GROSS_RECONCILIATION_FAILED`, `GL_RECONCILIATION_FAILED`
- `KORE_RECONCILIATION_FAILED`, `FOREIGN_GROSS_RECONCILIATION_FAILED`
- `FIELD_TOO_LONG`, `ENCODING_ERROR`, `ROW_LIMIT_EXCEEDED`

## Technische Verifikation

```sh
bench --site <site> migrate
bench --site <site> run-tests --app kmu_erp_austria \
  --module kmu_erp_austria.bmd_export.tests.test_transform
bench build --app kmu_erp_austria
```

Vor Produktivbetrieb bleibt ein manueller Import aller Fälle der Testmatrix aus dem Umsetzungsplan in einer BMD-NTCS-Testbuchhaltung erforderlich. Steuercodes, Konten, Filialen und Personenkonten sind mandantenspezifisch und werden bewusst nicht mit Beispieldaten vorbelegt.

Quelle: <https://www.bmd.at/Portaldata/1/Resources/help/00.00/OES/Documents/1109441501000002470.html>
