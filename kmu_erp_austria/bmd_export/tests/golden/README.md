# Herkunft der BMD-Golden-Daten

Die erwarteten Werte der Transformtests wurden am 21.08.2026 gegen folgende offizielle Quellen geprüft:

- BMD-Onlinehilfe „Buchungen importieren“: <https://www.bmd.at/Portaldata/1/Resources/help/00.00/OES/Documents/1109441501000002470.html>
- `Import BMD Gesamtbeispiel.xlsx`, insbesondere `Ausgangsrechnungen`, `Eingangsrechnungen`, `AR mit KST inkl. Aufteilung`, `ER mit KST inkl. Aufteilung`, `Fremdwährung`, `AR_Dokumente` und `OSS-Umsätze`
- `BMD Vorlage_AR_import.csv`

Die Binärdateien selbst werden nicht in der App dupliziert. Die Tests versionieren die daraus übernommenen fachlichen Erwartungen: AR/GU/ER/EG-Vorzeichen, output-side Steuer bei ig. Erwerb/RC/Bausteuer, Satzarten 0/1/5, Fremdwährungsvariante 1, OSS-Korrekturperiode sowie CSV/ZIP-Regeln.
