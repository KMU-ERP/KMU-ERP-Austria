# Umsetzungsplan: BMD-NTCS-Export als Modul in `kmu_erp_austria`

Stand: 21.08.2026  
Zielplattform: Frappe 16 / ERPNext 16  
Status: Technisch umgesetzt; produktive BMD-Testbuchhaltung und mandantenspezifische Mappings noch freizugeben

## 1. Ziel und Architekturentscheidung

Der BMD-Export wird als eigenständiges Frappe-Modul **BMD Export** innerhalb der vorhandenen App `kmu_erp_austria` umgesetzt. Es wird keine zweite App angelegt und es werden keine Frappe-/ERPNext-Coredateien verändert.

Das Modul exportiert eingereichte Ausgangs- und Eingangsrechnungen inklusive Gutschriften, Splitbuchungen, Steuerfällen, Kostenrechnung und Belegen in eine BMD-NTCS-konforme `buchungen.csv`. Ein flaches ZIP dient ausschließlich als Transportpaket für CSV und Dokumente.

Nicht Teil des Auftrags sind Bank-, Kassa-, Zahlungs-, Lohn-, Intrastat-, TR/SR- und Saldenbuchungen sowie ein automatischer Import in BMD. Diese Fälle aus dem BMD-Gesamtbeispiel dienen nur zur Abgrenzung.

## 2. Geprüfter Ist-Stand

- Repository der App: `development/frappe-bench/apps/kmu_erp_austria`
- Branch der App: `main`, Commit `b1d5e07`, Arbeitsbaum bei der Prüfung unverändert
- Frappe: `v16.31.0`
- ERPNext: `v16.32.3`
- Testsite: `development.localhost`
- Vorhandenes App-Modul: `Kmu Erp Austria`
- Vorhandener Migrationshook: `kmu_erp_austria.install.after_migrate`
- In der App existieren noch keine eigenen DocTypes, Workspaces oder BMD-Tests.
- Im ERPNext-Arbeitsbaum liegen bereits sachfremde Änderungen. Diese dürfen durch die BMD-Umsetzung nicht verändert werden.
- Es wurde keine einschlägige `AGENTS.md` gefunden.

Geprüfte fachliche Quellen:

1. `BMD_NTCS_ERPNext_v16_Implementierungsplan.md`
2. BMD-Onlinehilfe „Buchungen importieren“, am 21.08.2026 abgerufen:  
   <https://www.bmd.at/Portaldata/1/Resources/help/00.00/OES/Documents/1109441501000002470.html>
3. `Import BMD Gesamtbeispiel.xlsx`
4. `BMD Vorlage_AR_import.csv`
5. `Kontenplan RAN.xlsx`
6. `Kontenplan Allgemein.xlsx`

Wesentliche Ergebnisse der Quellenprüfung:

- Die BMD-Feldüberschriften sind verbindlich; Reihenfolge und Groß-/Kleinschreibung sind grundsätzlich frei.
- BMD empfiehlt nur Hauptbuchungen zu liefern. Steuer-, Sammel- und Gegenbuchungen werden von BMD erzeugt.
- Splitbuchungen werden nur bei aufeinanderfolgenden Zeilen mit identischem Personenkonto, Belegnummer, Belegdatum und Buchcode zusammengefasst.
- Ein Dokument kann in Satzart 0 stehen. Mehrere Dokumente folgen als Satzart 5 unmittelbar nach der ersten Satzart-0-Zeile.
- BMD schreibt kein inhaltliches Namensschema für Dokumentdateien vor. Der Wert in `dokument` muss lediglich exakt dem erreichbaren Dateinamen beziehungsweise Pfad entsprechen. Liegen CSV und Dokument im selben Ordner, genügt der Dateiname inklusive Endung.
- Eine KORE-Aufteilung in Satzart 1 folgt unmittelbar auf ihre Satzart-0-Zeile. Die Summe `kobetrag` muss dem Netto dieser Zeile mit gleichem Vorzeichen entsprechen.
- Bei ig. Erwerb, Bausteuer und Reverse Charge richtet sich das Vorzeichen der BMD-Steuer nach der Umsatzsteuerseite. Bei einer ER ist die Steuer im offiziellen Beispiel negativ, obwohl normale Vorsteuer positiv ist.
- BMD empfiehlt höchstens 20.000 Buchungen pro Importdatei.
- `Kontenplan RAN.xlsx` enthält 171 eindeutige Konten, der allgemeine Plan 1.108. Von 107 identischen Nummern haben 79 unterschiedliche Bezeichnungen. Daher ist eine automatische Gleichsetzung anhand der Kontonummer ausgeschlossen.

## 3. Zielstruktur im Repository

```text
kmu_erp_austria/
├── hooks.py                              # gefilterte Rollen-Fixtures, optionale Hooks
├── modules.txt                           # zusätzliche Zeile: BMD Export
├── patches.txt                           # idempotente BMD-Setup-Patches
└── bmd_export/
    ├── doctype/
    │   ├── bmd_export_settings/
    │   ├── bmd_export_profile/
    │   ├── bmd_export_profile_column/
    │   ├── bmd_account/
    │   ├── bmd_account_mapping/
    │   ├── bmd_party_mapping/
    │   ├── bmd_tax_mapping/
    │   ├── bmd_dimension_mapping/
    │   ├── bmd_export_batch/
    │   └── bmd_export_batch_item/
    ├── page/bmd_export_assistant/
    ├── report/bmd_missing_mappings/
    ├── services/
    │   ├── selection.py
    │   ├── normalization.py
    │   ├── mapping.py
    │   ├── taxes.py
    │   ├── grouping.py
    │   ├── reconciliation.py
    │   ├── documents.py
    │   ├── csv_renderer.py
    │   ├── package.py
    │   ├── fingerprint.py
    │   └── jobs.py
    ├── api.py
    ├── workspace/bmd_export/
    └── tests/
        ├── golden/
        └── files/
```

Die Services bleiben weitgehend frei von Frappe-UI-Code. Normalisierung, Mapping, Gruppierung, Vorzeichen, Rundung und CSV-Ausgabe werden als separat testbare Komponenten aufgebaut.

## 4. Datenmodell

### 4.1 `BMD Export Settings`

Normaler DocType, kein Single DocType, da die Einstellungen je Company getrennt sind. Das Feld `company` ist eindeutig.

Enthält mindestens aktives Profil, BMD-Firmennummer, Ausgabedateiname, Buchdatumregel, Belegpflicht je Belegart, erlaubte Erweiterungen und MIME-Typen, Maximalgröße, optionales Sales-Invoice-PDF, Print Format, das Pflichtfeld `document_filename_template` (Typ Code/Jinja), Default-Kostenstelle/-Filiale, maximale Satzart-0-Zeilen und Aufbewahrungsdauer.

`document_filename_template` ist eine zentrale Company-Einstellung und wird auf **jeden Anhang jedes neu erzeugten Exportpakets** angewandt, einschließlich eines automatisch erzeugten Sales-Invoice-PDFs. Der originale ERPNext-`File`-Datensatz und dessen Dateiname werden dabei nicht verändert; umbenannt wird ausschließlich die Kopie im Exportpaket. Abgeschlossene Pakete bleiben unverändert. Eine spätere Templateänderung wirkt erst auf neue Batches beziehungsweise einen ausdrücklich gestarteten Manager-Re-Export.

Standardtemplate für den Dateinamen ohne Erweiterung:

```jinja
{{ voucher_type_code }}-{{ voucher_name }}_{{ attachment_no }}
```

Die Dateiendung wird nicht vom Template erzeugt, sondern unverändert von der geprüften Quelldatei angehängt. Das verhindert, dass Template und tatsächlicher MIME-Typ auseinanderfallen.

Beispiel für die gewünschte globale Umbenennung:

```jinja
{{ invoice_number }}-{{ party_name }}
```

Aus dem ERPNext-Anhang `test.pdf` wird damit beispielsweise `AR-2026-0042-Musterkunde.pdf`. Wer den Originalnamen beibehalten will, kann ausdrücklich `{{ original_stem }}` konfigurieren.

### 4.2 `BMD Export Profile` und `BMD Export Profile Column`

Das Profil macht den variablen BMD-Satzaufbau explizit konfigurierbar. Es enthält Trennzeichen, Encoding (`utf-8-sig` oder `cp1252`), Dezimalzeichen, Datumsformat, Zeilenende, Geld-/Kurs-/Mengenpräzision und eine geordnete Liste zulässiger BMD-Felder.

Ein ausgeliefertes Standardprofil enthält mindestens:

```text
satzart, konto, gkonto, belegnr, buchdatum, belegdatum, buchsymbol,
buchcode, prozent, steuercode, betrag, steuer, kost, filiale,
extbelegnr, fwbetrag, fwsteuer, waehrung, fwkurs, uva-korrperiode,
oss-zielland, oss-schema, oss-uidnr, dokument, kobetrag, kotraeger,
koabteilung, kodimension, kogeschaeftsbereich, komenge, komengenr, text
```

`text` steht im Standardprofil an letzter Stelle. Unbekannte Feldnamen, doppelte Spalten und fehlende Pflichtspalten blockieren die Profilaktivierung.

### 4.3 Mapping-DocTypes

- `BMD Account`: Company, Kontonummer als Text mit maximal 10 Stellen, Bezeichnung, Kontoart, Quelle, Importzeitpunkt und Aktivstatus.
- `BMD Account Mapping`: ERPNext Account auf BMD Account mit Gültigkeit, Priorität und optionalen Bedingungen.
- `BMD Party Mapping`: Customer/Supplier auf ein BMD-Personenkonto mit Gültigkeit.
- `BMD Tax Mapping`: Richtung, Tax Category, Land/Ländergruppe, Steuersatz, optional ERPNext-Steuerkonto, BMD-Steuercode, Steuerbetragsquelle, Vorzeichenregel, Kennzeichen ob die Steuer im offenen Rechnungsbetrag enthalten ist, Filiale und OSS-Werte, Gültigkeit und Priorität.
- `BMD Dimension Mapping`: ERPNext Cost Center, Project oder Accounting Dimension auf `kost`, `kotraeger`, `koabteilung`, `kodimension` oder `kogeschaeftsbereich`.

Alle Resolver verwenden Company und Belegdatum. Kein Treffer und mehrere gleichrangige Treffer sind Fehler. Eine identische Kontonummer ist kein Fallback.

### 4.4 `BMD Export Batch` und `BMD Export Batch Item`

Der Batch hält Filter, anfordernden Benutzer, Status, Revision, Summen, Zeilen-/Dokumentzahlen, Artefakt-Links, SHA-256, Settings-/Profil-/Mapping-Snapshot, Validierungsprotokoll und Verknüpfung zu einem ersetzten Batch.

`BMD Export Batch Item` ist ein eigener, verlinkter DocType und keine große eingebettete Child Table. Dadurch bleiben Batches mit vielen Belegen abfragbar. Er enthält Voucher Type/Name, Datum, Status, Summen, Fingerprint, verwendete Dokument-Hashes sowie Fehler und Warnungen.

Erlaubte serverseitige Statusübergänge:

```text
Draft → Validating → Invalid
                   → Ready → Generating → Completed
                                         → Failed
Completed → Superseded  (nur durch erfolgreichen Manager-Re-Export)
```

Fertige Artefakte, Snapshots und Batch Items sind unveränderlich. Ein fehlgeschlagener Lauf überschreibt keinen abgeschlossenen Lauf.

## 5. Datengewinnung und Transformationsregeln

### 5.1 ERPNext-v16-Quellen

- Nur `Sales Invoice` und `Purchase Invoice` mit `docstatus = 1`.
- Retouren/Gutschriften über `is_return` und `return_against`.
- Sachkonto, Netto, Cost Center und Project aus den Invoice Items.
- Positionssteuern primär aus der in ERPNext v16 vorhandenen Child Table `Item Wise Tax Detail` (`item_row`, `tax_row`, `rate`, `amount`, `taxable_amount`).
- Die zugehörige Steuerzeile liefert unter anderem Steuerkonto und Berechnungsart.
- Rechnungsweite Steuersummen dürfen nur zur Kontrolle verwendet werden. Fehlen bei einem steuerpflichtigen Beleg eindeutige Positionsdetails, wird der Export blockiert.
- Grund- und Belegwährungswerte sowie `conversion_rate` werden getrennt normalisiert.
- `GL Entry` wird ausschließlich zur Abstimmung verwendet.
- Nur direkt an die Rechnung verknüpfte `File`-Datensätze werden berücksichtigt.

Beim Einlesen werden Geldwerte unmittelbar aus ihrer String-/Decimal-Repräsentation in `Decimal` überführt. Danach sind keine `float`-Operationen im Exportkern zulässig.

### 5.2 Verarbeitung je Rechnung

1. Berechtigung, Company, Status, Zeitraum und bisherige Exporte prüfen.
2. Invoice- und Dokument-Fingerprint erzeugen.
3. Personenkonto eindeutig auflösen.
4. Jede Item-Zeile inklusive positionsbezogener Steuern normalisieren.
5. Sachkonto, Steuerfall, Steuercode und Dimensionen zum Belegdatum auflösen.
6. Nach Personenkonto, Gegenkonto, Steuercode, Steuersatz, Dimensionen, Filiale/OSS und Währung gruppieren.
7. Netto, im Rechnungsbetrag enthaltene Steuer und BMD-Steuer pro Gruppe mit `Decimal` berechnen.
8. Rundungsreste deterministisch der betragsmäßig größten geeigneten Gruppe zuordnen.
9. AR/GU/ER/EG-Symbole, Buchcodes und Vorzeichen anwenden.
10. KORE-Satzart-1-Zeilen direkt nach der betreffenden Satzart-0-Zeile einfügen.
11. Dokumente in der vorgeschriebenen Reihenfolge einfügen.
12. Rechnung, Split und Batch abstimmen.

Verbindliche Vorzeichenmatrix:

| Fall | Symbol | Buchcode | `betrag` | normale `steuer` |
| --- | --- | ---: | --- | --- |
| Ausgangsrechnung | AR | 1 | positiv | negativ |
| Ausgangsgutschrift | GU | 1 | negativ | positiv |
| Eingangsrechnung | ER | 2 | negativ | positiv |
| Eingangsgutschrift | EG | 2 | positiv | negativ |

Für ig. Erwerb, Bausteuer und Reverse Charge wird nicht die normale Vorsteuermatrix angewandt: Laut BMD-Beispiel ist die Steuer der ER negativ und bei der Gutschrift umgekehrt. Steuerbetragsquelle, Einbeziehung in den Rechnungsbetrag und Vorzeichen kommen aus dem Tax Mapping, nicht aus hart codierten Steuercodes.

### 5.3 Reihenfolge

Rechnungen werden deterministisch nach Posting Date, Voucher Type und Voucher Name sortiert. Innerhalb einer Rechnung bleiben alle Satzarten zusammenhängend.

```text
erste Satzart-0-Zeile
├── optional: mehrere Satzart-5-Dokumentzeilen
├── optional: zu dieser Buchungszeile gehörende Satzart-1-KORE-Zeilen
weitere Satzart-0-Splitzeile
└── optional: deren Satzart-1-KORE-Zeilen
```

Bei genau einem Dokument steht der Dateiname nur in der ersten Satzart-0-Zeile. Bei mehreren Dokumenten bleibt dieses Feld leer; alle Satzart-5-Zeilen folgen direkt auf die erste Satzart-0-Zeile. Das Dokument wird nicht auf jede Splitzeile kopiert.

## 6. CSV-, Dokument- und Paketregeln

- Standarddatei: `buchungen.csv`, Semikolon, `utf-8-sig`, CRLF.
- Datum: `TT.MM.JJJJ`.
- Kein Tausendertrennzeichen; Dezimalzeichen und Präzision gemäß Profil.
- Kaufmännische Rundung mit `Decimal`/`ROUND_HALF_UP`.
- Aktives Trennzeichen wird in allen Textwerten durch ein Komma ersetzt; CR/LF/Tabs werden in Leerzeichen normalisiert.
- `text` ist die letzte Standardspalte.
- Feldlängen werden vor dem Rendern validiert. Für `dokument` gilt wegen Satzart 5 konservativ maximal 255 Zeichen.
- BMD verlangt kein bestimmtes Namensmuster. Ohne eigene Konfiguration wird `<Belegtyp>-<Belegnummer>_<Nr>.<ext>` verwendet.
- Der Dateinamensstamm wird bei allen neuen Exporten mit dem in `BMD Export Settings` hinterlegten sandboxed Jinja-Template erzeugt. Der Template-Kontext enthält ausschließlich primitive, freigegebene Werte: `company`, `voucher_type`, `voucher_type_code`, `voucher_name`, `invoice_number` (exportierte BMD-`belegnr`), `external_invoice_number`/`bill_no`, `posting_date_yyyymmdd`, `party`, `party_name`, `return_against`, `attachment_no`, `original_stem` und `extension`.
- Es wird niemals das vollständige Frappe-Dokument, `frappe`, ein Datenbankzugriff oder eine aufrufbare Funktion an das Template übergeben. Unbekannte Variablen, Templatefehler sowie ein leeres Ergebnis blockieren bereits die Vorschau.
- Die geprüfte Originalerweiterung wird nach dem Rendern angehängt. Das Template liefert daher immer nur den Dateinamensstamm; `extension` steht lediglich für Bedingungen zur Verfügung. Pfadbestandteile, Steuerzeichen und für ZIP/Windows unsichere Zeichen werden entfernt; Unicode wird normalisiert und der Stamm nötigenfalls gekürzt, ohne die Erweiterung oder den Kollisionssuffix abzuschneiden.
- Der endgültige Name muss im aktiven CSV-Encoding darstellbar sein. Andernfalls blockiert die Vorschau, damit CSV-Referenz und ZIP-Dateiname nicht voneinander abweichen.
- Kollisionen werden deterministisch mit einem Suffix vor der Erweiterung aufgelöst. Die Vorschau zeigt den endgültigen Namen; genau dieser Name wird in `dokument` und im flachen ZIP verwendet.
- Die Quelldatei in ERPNext wird weder umbenannt noch verschoben. Das Template verändert ausschließlich den Namen der Exportkopie sowie die dazugehörige BMD-Referenz.
- Das ZIP ist flach. Es enthält exakt eine CSV und alle referenzierten Belege.
- ZIP-Reihenfolge und ZIP-Metadaten werden normalisiert, damit ein Retry desselben Batches identische Bytes erzeugt.
- CSV, ZIP und jeder Beleg erhalten einen SHA-256-Hash.
- CSV und ZIP werden als private `File`-Datensätze am Batch gespeichert.
- Standardgrenze: maximal 20.000 Satzart-0-Zeilen je Batch; bei Überschreitung wird eine Aufteilung in mehrere Batches verlangt.

## 7. Sicherheit und Idempotenz

Rollen:

- `BMD Export User`: Vorschau, Export und Download für erlaubte Companies.
- `BMD Export Manager`: zusätzlich Einstellungen, Profile und Mappings pflegen sowie Re-Exporte freigeben.

Regeln:

- Server-APIs prüfen Rolle, DocType-Berechtigung und Company User Permissions.
- Rechnungslisten werden mit berechtigungsbeachtenden Abfragen ermittelt.
- Der Background Job arbeitet im Kontext des anfordernden Benutzers beziehungsweise prüft dessen gespeicherte Berechtigung erneut.
- Private Anhänge werden erst nach Prüfung der Rechnung und des `File`-Links serverseitig gelesen.
- Kein pauschales `ignore_permissions=True` in benutzerinitiierten Pfaden.
- ZIP-Einträge verbieten absolute Pfade, Laufwerksangaben, `..`, Unterordner und doppelte Namen.
- Ein Redis-Lock verhindert die parallele Generierung desselben Batches.
- Vor Generierung werden Invoice-`modified`, Settings-/Profil-/Mappingstände und Dokument-Hashes aus der Vorschau erneut geprüft.
- Ein Voucher aus einem abgeschlossenen Batch wird standardmäßig unabhängig von späteren Änderungen ausgeschlossen und als Konflikt gemeldet. Nur ein Manager kann eine neue Revision erzeugen.
- Der alte Batch wird erst nach erfolgreichem Re-Export als `Superseded` markiert.

## 8. Task-Backlog

Prioritäten: **P0** = für produktiven Erstbetrieb zwingend, **P1** = unmittelbar danach beziehungsweise optional konfigurierbar.

### Phase A – Fundament

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-001 | P0 | Versionsstand, Site, Arbeitsbäume und Referenzen dokumentieren | – | Die Angaben aus Abschnitt 2 sind im Projekt nachvollziehbar; sachfremde Änderungen bleiben unangetastet. |
| BMD-002 | P0 | Offizielle Beispiele in kleine, versionierte Test-Golden-Files überführen | BMD-001 | Herkunft, Abrufdatum und BMD-Blatt sind je Golden File dokumentiert. |
| BMD-003 | P0 | Modul `BMD Export` in `modules.txt` und Python-Package anlegen | BMD-001 | `bench migrate` synchronisiert ein eigenes Module Def ohne zweite App. |
| BMD-004 | P0 | Rollen und gefilterte Role-Fixtures ergänzen | BMD-003 | Nur die beiden BMD-Rollen werden als Fixture exportiert und nach Migration angelegt. |
| BMD-005 | P0 | Service-, Test- und Golden-File-Struktur anlegen | BMD-003 | Imports funktionieren und ein leerer Modultest läuft. |

### Phase B – Datenmodell und Setup

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-010 | P0 | `BMD Export Profile` plus Spalten-Child-DocType implementieren | BMD-003 | Standardprofil ist gültig, `text` zuletzt; unbekannte/doppelte Felder werden abgelehnt. |
| BMD-011 | P0 | `BMD Export Settings` je Company implementieren | BMD-010 | Pro Company ist höchstens ein Datensatz möglich; Profil, Dateiregeln und das global auf alle neuen Exportanhänge anzuwendende `document_filename_template` werden validiert. |
| BMD-012 | P0 | `BMD Account` implementieren | BMD-003 | Company + Kontonummer ist eindeutig; Nummer bleibt Text und maximal 10 Stellen. |
| BMD-013 | P0 | Vorschaugestützten XLSX/CSV-Kontenimport implementieren | BMD-012 | RAN-Datei importiert 171 Konten; Duplikate/Fehler werden vor dem Schreiben angezeigt. |
| BMD-014 | P1 | Allgemeinen Kontenplan als getrennte Vorschlagsquelle importierbar machen | BMD-013 | Keine automatische Verknüpfung oder Überschreibung des RAN-Katalogs. |
| BMD-015 | P0 | `BMD Account Mapping` implementieren | BMD-012 | Company-Konsistenz, Gültigkeit und gleichrangige Überschneidungen werden validiert. |
| BMD-016 | P0 | `BMD Party Mapping` implementieren | BMD-012 | Customer/Supplier und Personenkonto sind eindeutig, company- und datumsbezogen. |
| BMD-017 | P0 | `BMD Tax Mapping` mit Betragsquelle und Vorzeichenregel implementieren | BMD-003 | Inland, 0 %, igL, EU-Leistung, ig. Erwerb, RC und Bausteuer sind ohne hart codierte Codes beschreibbar. |
| BMD-018 | P0 | `BMD Dimension Mapping` implementieren | BMD-003 | Cost Center/Project/Dimension kann eindeutig auf ein BMD-KORE-Feld gemappt werden. |
| BMD-019 | P0 | Batch und eigenständige Batch Items inklusive Statusautomat implementieren | BMD-003 | Ungültige Statuswechsel und Änderungen an abgeschlossenen Snapshots werden serverseitig blockiert. |
| BMD-020 | P0 | Idempotentes Setup für Rollen und Standardprofil ergänzen | BMD-010, BMD-019 | Neue und bestehende Sites erhalten nach `migrate` genau einen Standardprofil-Stand; Benutzerdaten werden nicht überschrieben. |

### Phase C – Auswahl, Normalisierung und Mapping

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-030 | P0 | Berechtigungsbeachtenden Invoice-Selektor implementieren | BMD-011, BMD-019 | Nur eingereichte, erlaubte SI/PI der gewählten Company und Periode werden geliefert. |
| BMD-031 | P0 | Doppelexport-, Storno- und Re-Export-Erkennung implementieren | BMD-030 | Abgeschlossene Voucher werden ausgeschlossen; geänderte/stornierte Voucher erscheinen als Konflikt. |
| BMD-032 | P0 | Immutable Decimal-Domainmodelle für Invoice, Item, Tax, Booking und KORE definieren | BMD-005 | Kernmodelle sind ohne DB/UI testbar und enthalten keine binären Float-Berechnungen. |
| BMD-033 | P0 | Sales-/Purchase-Invoice-Normalisierung implementieren | BMD-032 | AR, GU, ER und EG liefern Basis-/Belegwährung, Konten, Dimensionen und stabile Belegnummern. |
| BMD-034 | P0 | ERPNext-v16-`Item Wise Tax Detail` auswerten | BMD-033 | Steuerdetails werden über `item_row`/`tax_row` einer Position zugeordnet; uneindeutige Daten blockieren. |
| BMD-035 | P0 | Generischen Mapping-Resolver mit Priorität/Gültigkeit implementieren | BMD-015–BMD-018 | Kein Treffer und gleichrangige Mehrfachtreffer erzeugen strukturierte Fehler. |
| BMD-036 | P0 | Konten-, Party- und Dimensionsauflösung integrieren | BMD-033, BMD-035 | Jede exportierte Gruppe enthält nur bestätigte BMD-Zielwerte. |
| BMD-037 | P0 | Tax-Resolver für normale und steuerfreie Fälle implementieren | BMD-034, BMD-035 | Inland 20/10/0 %, igL und EU-Dienstleistung entsprechen den Golden Files. |
| BMD-038 | P0 | Tax-Resolver für ig. Erwerb, RC und Bausteuer implementieren | BMD-037 | BMD-Steuer wird positionsbezogen berechnet und hat das offizielle BMD-Vorzeichen, auch wenn ERPNext netto 0 Steuerwirkung zeigt. |
| BMD-039 | P0 | OSS-Zielland, Schema, UID und Korrekturperiode integrieren | BMD-037 | OSS-Rechnung und -Gutschrift entsprechen dem Blatt `OSS-Umsätze`. |

### Phase D – Gruppierung, Rundung und Abstimmung

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-040 | P0 | Gruppierung und aufeinanderfolgende Splitzeilen implementieren | BMD-036–BMD-039 | Unterschiedliche Konten, Steuerfälle, Sätze, KORE-Werte, Filialen und Währungen bleiben getrennt. |
| BMD-041 | P0 | AR/GU/ER/EG-Symbole, Buchcodes und Vorzeichen anwenden | BMD-040 | Alle vier Fälle entsprechen der Vorzeichenmatrix und den offiziellen Beispielen. |
| BMD-042 | P0 | Deterministische Rundungsrestverteilung implementieren | BMD-040 | Gruppen summieren sich centgenau auf die ERPNext-Rechnung; Wiederholungen sind identisch. |
| BMD-043 | P0 | Satzart-1-KORE-Aufteilung implementieren | BMD-018, BMD-040 | `kobetrag` summiert sich je Hauptzeile mit gleichem Vorzeichen exakt auf deren Netto. |
| BMD-044 | P0 | Fremdwährungsfelder nach bevorzugter BMD-Variante 1 implementieren | BMD-040 | Grund- und Fremdwährungsbetrag/-steuer sowie Währung sind konsistent; Kurs ist optional konfigurierbar. |
| BMD-045 | P0 | Rechnungs-, Split- und Batch-Abstimmung implementieren | BMD-041–BMD-044 | Netto, Steuer, offener Betrag und relevante GL-Kontrollsumme werden geprüft; Differenzen blockieren. |

### Phase E – Dokumente und Paket

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-050 | P0 | Direkte private/public `File`-Anhänge sicher laden | BMD-030 | Nur berechtigte, direkt verknüpfte Dateien werden gelesen; fehlende Inhalte werden gemeldet. |
| BMD-051 | P0 | Erweiterung, MIME, Größe und Lesbarkeit prüfen | BMD-050 | Nicht erlaubte, leere, zu große oder unlesbare Belege blockieren nach Einstellung. |
| BMD-052 | P0 | Sichere deterministische Exportdateinamen mit globalem sandboxed Jinja-Template erzeugen | BMD-011, BMD-051 | Das Company-Template wird auf jeden exportierten Anhang angewandt, ohne den ERPNext-Originalnamen zu ändern; Erweiterung bleibt erhalten; ungültige Variablen/Ergebnisse blockieren; Pfadtraversal und Kollisionen sind ausgeschlossen. |
| BMD-053 | P0 | Einzel- und Mehrfachdokumentzeilen erzeugen | BMD-040, BMD-052 | Ein Dokument steht nur in erster Satzart 0; mehrere folgen dort als Satzart 5 vor weiteren Splits. |
| BMD-054 | P1 | Optionales Sales-Invoice-PDF generieren | BMD-011, BMD-053 | Nur bei aktivierter Einstellung und fehlendem Beleg; auch das generierte PDF erhält den global gerenderten Exportnamen; Print-Format- und Berechtigungsfehler sind sichtbar. |
| BMD-055 | P0 | Fingerprints und Einzeldatei-Hashes implementieren | BMD-031, BMD-052 | Fingerprint enthält Voucherstand, Settings-/Profil-/Mappingstand einschließlich Jinja-Template und Dokumenthashes. |

### Phase F – CSV und ZIP

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-060 | P0 | Feldregistry mit BMD-Namen, Typen, Längen und Präzision implementieren | BMD-010 | Renderer akzeptiert ausschließlich unterstützte Profilfelder. |
| BMD-061 | P0 | CSV-Renderer mit Decimal-, Datum-, Encoding- und CRLF-Regeln implementieren | BMD-060, BMD-045 | Bytes entsprechen Profil; kein Tausendertrennzeichen und keine Float-Artefakte. |
| BMD-062 | P0 | Text- und Trennzeichensanitisierung implementieren | BMD-061 | Semikolon, aktive Delimiter, Tabs und Zeilenumbrüche können keine Zusatzspalte/-zeile erzeugen. |
| BMD-063 | P0 | Deterministische Gesamtzeilenreihenfolge implementieren | BMD-043, BMD-053 | Identischer Snapshot erzeugt byteidentische CSV. |
| BMD-064 | P0 | Flaches deterministisches ZIP erzeugen | BMD-055, BMD-063 | ZIP enthält `buchungen.csv` und exakt alle referenzierten Dateien ohne Pfade. |
| BMD-065 | P0 | Private CSV/ZIP-Files, SHA-256 und Konfigurations-/Mapping-Snapshot atomar speichern | BMD-019, BMD-064 | Batch wird erst nach vollständig gespeicherten Artefakten `Completed`; Teilfehler hinterlassen keinen falschen Erfolg. |
| BMD-066 | P0 | Grenze von 20.000 Satzart-0-Zeilen erzwingen | BMD-063 | Zu große Exporte werden vor Jobstart mit einem Vorschlag zur Zeitraumteilung abgewiesen. |

### Phase G – Workflow, UI und Sicherheit

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-070 | P0 | Rollen- und Company-Permissions für alle DocTypes definieren | BMD-004, BMD-019 | Export User kann keine Mappings ändern; beide Rollen sehen nur erlaubte Companies/Batches. |
| BMD-071 | P0 | Gesicherte APIs für Batch, Vorschau, Job und Download implementieren | BMD-070 | Direkte API-Aufrufe ohne Rolle/Company-Recht schlagen fehl. |
| BMD-072 | P0 | Exportassistent als Frappe Page implementieren | BMD-071 | Company, Zeitraum und Belegarten erzeugen einen Draft Batch und eine prüfbare Vorschau. |
| BMD-073 | P0 | Vorschau für Rechnungen, Anhänge, endgültige Exportdateinamen, Summen, Fehler und Warnungen implementieren | BMD-045, BMD-053, BMD-072 | Fehlende/mehrdeutige Mappings und ungültige Dateinamen-Templates sind voucher- und positionsbezogen sichtbar und blockieren den Start. |
| BMD-074 | P0 | Background Job, Lock, Fortschritt und Retry implementieren | BMD-065, BMD-071 | UI bleibt responsiv; Doppelstart ist ausgeschlossen; Status und Fehler bleiben nachvollziehbar. |
| BMD-075 | P0 | ZIP- und CSV-Download samt Importhinweis implementieren | BMD-074 | Neben Downloads steht sichtbar: ZIP entpacken und ausschließlich `buchungen.csv` in BMD auswählen. |
| BMD-076 | P0 | Workspace `BMD Export` erstellen | BMD-070–BMD-075 | Workspace enthält Assistent, Batches, Einstellungen, Profile, alle Mappings und Bericht. |
| BMD-077 | P0 | Bericht `BMD Missing Mappings` implementieren | BMD-035, BMD-070 | Bericht filtert nach Company/Zeitraum/Belegart und respektiert Berechtigungen. |
| BMD-078 | P0 | Manager-Re-Export und Supersede-Workflow implementieren | BMD-031, BMD-074 | Neue Revision bleibt getrennt; alter Batch wird erst nach Erfolg ersetzt. |
| BMD-079 | P1 | Kontrollierte Artefakt-Aufbewahrung implementieren | BMD-065, BMD-070 | Nur abgelaufene private Dateien werden entfernt; Auditdaten und Löschprotokoll bleiben erhalten. |

### Phase H – Tests und Abnahme

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-080 | P0 | Pure Unit Tests für Decimal, Gruppierung, Vorzeichen und Rundung | Phase D | Grenz- und Restcentfälle laufen ohne DB. |
| BMD-081 | P0 | Golden Tests für AR/GU/ER/EG und Splits | BMD-002, Phase D | Ergebnisse entsprechen `Ausgangsrechnungen` und `Eingangsrechnungen`. |
| BMD-082 | P0 | Golden Tests für igL, EU-Leistung, ig. Erwerb, RC, Bausteuer und OSS | BMD-002, BMD-039 | Codes, Prozent, Betrag und Steuer entsprechen den offiziellen Blättern. |
| BMD-083 | P0 | Golden Tests für KORE und Fremdwährung | BMD-043, BMD-044 | Satzart 1 und FW-Felder entsprechen den offiziellen Blättern. |
| BMD-084 | P0 | Dokument-/ZIP-/Jinja-Tests mit Dummy-PDF/JPG/PNG | BMD-064 | Einzel-, Mehrfach-, Split- und KORE-Fälle sowie globale Default-/Custom-Templates, Umbenennung von `test.pdf`, unveränderter ERPNext-Originalname, generierte PDFs, Sonderzeichen, unbekannte Variablen, Längengrenzen und Kollisionen sind geprüft; CSV-Referenz und flacher ZIP-Eintrag sind identisch. |
| BMD-085 | P0 | Mapping- und Profiltoleranztests | Phase B, BMD-060 | Fehlend, doppelt, überlappend, falsche Company, unbekannte Felder und ungültige Encodings blockieren. |
| BMD-086 | P0 | Idempotenz-, Parallelitäts- und Re-Export-Tests | BMD-078 | Doppelexport und parallele Jobs sind verhindert; Revisionen bleiben vollständig. |
| BMD-087 | P0 | Berechtigungs-, Company-Isolations- und private-File-Tests | BMD-071 | Unberechtigte Benutzer können weder Vorschau noch Dateiinhalt einer fremden Company lesen. |
| BMD-088 | P0 | Frappe-Integrationstest vom Invoice-Dokument bis ZIP | BMD-080–BMD-087 | Ein Batch mit SI, PI, Return und Belegen endet reproduzierbar in `Completed`. |
| BMD-089 | P0 | Manuellen Import in einer BMD-NTCS-Testbuchhaltung durchführen | BMD-088 | Alle Fälle der fachlichen Testmatrix sind importiert und fachlich abgezeichnet. |

### Phase I – Dokumentation und Betrieb

| ID | Prio | Aufgabe | Abhängigkeit | Abnahmekriterium |
| --- | --- | --- | --- | --- |
| BMD-090 | P0 | Installations-/Migrationsanleitung schreiben | BMD-020 | Befehle für bestehende und neue Site sind reproduzierbar. |
| BMD-091 | P0 | Einrichtungsanleitung für Profile, Mappings und Jinja-Dateinamensvorlage schreiben | Phase B | RAN-Import, Party-, Steuer- und Dimensionsmapping sowie erlaubte Templatevariablen und Namensvorschau sind mit Beispielen beschrieben. |
| BMD-092 | P0 | Benutzeranleitung für Vorschau, Export und BMD-Import schreiben | BMD-075 | Entpacken des ZIP und Auswahl nur der CSV sind unmissverständlich erklärt. |
| BMD-093 | P0 | Troubleshooting und Fehlercodes dokumentieren | BMD-073, BMD-074 | Mapping-, Steuer-, Attachment-, Encoding- und BMD-Vorschaufehler sind auffindbar. |
| BMD-094 | P0 | Betriebs-/Revisionsdokumentation schreiben | BMD-078, BMD-079 | Fingerprint, Snapshot, Re-Export, Aufbewahrung und Verantwortlichkeiten sind erklärt. |

## 9. Empfohlene Lieferreihenfolge und Gates

1. **Gate 1 – Modul und Schema:** BMD-001 bis BMD-020. `bench migrate` läuft auf einer frischen und auf der bestehenden Site.
2. **Gate 2 – Fachlicher Kern:** BMD-030 bis BMD-045. AR/GU/ER/EG und Sondersteuern bestehen Pure/Golden Tests.
3. **Gate 3 – Transport:** BMD-050 bis BMD-066. Dokumentreferenzen, CSV und ZIP sind reproduzierbar.
4. **Gate 4 – Produktworkflow:** BMD-070 bis BMD-079. Berechtigungen, Assistent, Background Job und Re-Export funktionieren.
5. **Gate 5 – Freigabe:** BMD-080 bis BMD-094. Automatisierte Tests sind grün und der reale BMD-Testimport ist abgezeichnet.

Kein Gate darf durch Beispieldaten-Mappings „grün“ gemacht werden. Reale Debitoren-/Kreditoren-, Steuer-, Kostenstellen- und Filialmappings werden mandantenspezifisch gepflegt.

## 10. Testmatrix für BMD NTCS

Mindestens folgende Fälle müssen in einem BMD-Testmandanten importiert werden:

1. AR Inland 20 % mit einem PDF
2. AR mit 10 %/20 %, mehreren Gegenkonten und Rundungsrest
3. GU zu einer AR
4. ER Inland mit `bill_no` und JPG
5. EG zu einer ER
6. ER mit mehreren Aufwandskonten/Steuersätzen
7. innergemeinschaftliche Lieferung
8. EU-Dienstleistung, ZM-pflichtig
9. innergemeinschaftlicher Erwerb
10. Reverse Charge
11. Bausteuer
12. OSS-Umsatz und OSS-Gutschrift mit Korrekturperiode
13. Fremdwährungsrechnung
14. einfache Kostenstelle und Satzart-1-KORE-Aufteilung
15. mehrere Dokumente und Splitbuchung
16. fehlendes und mehrdeutiges Mapping als blockierender Fehler
17. Doppelexport und Manager-Re-Export
18. unberechtigter Company-/Dateizugriff

Pro Fall werden Personenkonto, Gegenkonto, Belegnummer, externe Belegnummer, Buchsymbol/-code, Steuercode/-satz/-wirkung, Kostenstelle/Filiale, offener Posten, Dokumentanzeige und Summengleichheit geprüft.

## 11. Vorgesehene technische Prüfungen

```sh
cd /workspace/development/development/frappe-bench
bench --site development.localhost migrate
bench --site development.localhost run-tests --app kmu_erp_austria \
  --module kmu_erp_austria.bmd_export
bench build --app kmu_erp_austria

cd apps/kmu_erp_austria
ruff check .
ruff format --check .
```

Zusätzlich ist ein Test auf einer frisch installierten Site erforderlich, damit Rollen, Standardprofil und Migrationen nicht nur auf der bestehenden Entwicklungsdatenbank funktionieren.

## 12. Definition of Done

- `BMD Export` ist als eigenes Modul der App sichtbar und migrationsfähig.
- Es gibt keine Core-Änderungen und keine ungesicherten Berechtigungsumgehungen.
- AR, GU, ER und EG inklusive Split, Sondersteuer, OSS, Fremdwährung und KORE werden korrekt erzeugt.
- Alle fachlichen Zielwerte stammen aus eindeutigen, versionierten Mappings.
- CSV und flaches ZIP sind deterministisch; alle referenzierten Dokumente liegen im Paket.
- Mapping-Snapshot, Voucher-/Dokument-Fingerprints, Hashes, Benutzer und Zeitpunkte sind revisionsfähig gespeichert.
- Doppelexport, Parallelstart und unberechtigter Zugriff sind automatisiert getestet.
- UI und Dokumentation erklären ausdrücklich: ZIP entpacken, danach nur `buchungen.csv` in BMD NTCS auswählen.
- Automatisierte Tests laufen erfolgreich.
- Der vollständige Fallkatalog wurde in einer BMD-NTCS-Testbuchhaltung importiert und fachlich freigegeben.

## 13. Vor Produktivfreigabe noch fachlich zu bestätigen

Diese Punkte sind konfigurierbar vorgesehen, benötigen aber reale Mandantenentscheidungen:

1. BMD-Debitoren- und Kreditorenkonten je Customer/Supplier
2. ERPNext- auf BMD-Sachkontenmapping auf Basis des RAN-Plans
3. Steuerfall-/Steuercodemapping einschließlich ERPNext-Steuerkonten
4. Kostenstellen-, Projekt-, Filial- und OSS-Mappings
5. BMD-intern gewünschte `belegnr` für Purchase Invoices; Default ist der stabile ERPNext-Name, `extbelegnr` bleibt `bill_no`
6. Aktives Encoding (`utf-8-sig` oder `cp1252`) und Dezimalzeichen
7. Print Format und Regel für automatisch erzeugte Ausgangsrechnungs-PDFs
8. Maximale Beleggröße und Aufbewahrungsdauer
9. Gewünschtes Jinja-Namensschema; technisch sicherer Default ist `{{ voucher_type_code }}-{{ voucher_name }}_{{ attachment_no }}` plus geprüfte Originalerweiterung

Diese Bestätigungen blockieren nicht die technische Umsetzung, wohl aber die produktive fachliche Abnahme.
