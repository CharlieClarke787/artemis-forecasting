"""Build a reproducible, open-data composite country risk index.

The default scope mirrors the country names already present in
``import_ofac_api.py``.  It is intentionally a support for qualitative work,
not a forecast or a substitute for a country briefing.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.request
import urllib.error
import zipfile
from pathlib import Path
from xml.etree import ElementTree

COUNTRIES = {
    "RUS": ("Russia", "Country appears in repository sanctions examples; no qualitative briefing found."),
    "IRN": ("Iran", "Country appears in repository sanctions examples; no qualitative briefing found."),
    "VEN": ("Venezuela", "Country appears in repository sanctions examples; no qualitative briefing found."),
    "SYR": ("Syria", "Country appears in repository sanctions examples; no qualitative briefing found."),
}
WB_INDICATORS = {
    "government_effectiveness": ("GE.EST", True),
    "political_stability": ("PV.EST", True),
    "rule_of_law": ("RL.EST", True),
    "control_of_corruption": ("CC.EST", True),
}
IMF_INDICATORS = {
    "real_gdp_growth": ("NGDP_RPCH", False),
    "gross_debt_pct_gdp": ("GGXWDG_NGDP", True),
}
SOURCE_URLS = {
    "world_bank": "https://api.worldbank.org/v2/en/indicator/{indicator}?downloadformat=csv",
    "imf": "https://www.imf.org/external/datamapper/api/v1/{indicator}/{codes}",
    "freedom_house": (
        "https://raw.githubusercontent.com/xmarquez/democracyData/"
        "84290a7f31375228cf83d059f587f81832c37d97/data-raw/"
        "fh_aggregate_scores_2003_2026.xlsx"
    ),
}
OUTPUT_FIELDS = [
    "country_code", "country", "reference_year", "government_score",
    "macroeconomic_score", "freedom_score", "composite_score", "risk_band",
    "available_components", "missing_indicators", "qualitative_cross_check",
]


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "ArtemisForecasting/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_world_bank(indicator: str, target_year: int) -> dict[str, dict]:
    url = SOURCE_URLS["world_bank"].format(indicator=indicator)
    request = urllib.request.Request(url, headers={"User-Agent": "ArtemisForecasting/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
        filename = next(name for name in archive.namelist() if name.startswith("API_"))
        text = archive.read(filename).decode("utf-8-sig")
    lines = text.splitlines()
    header_index = next(index for index, line in enumerate(lines) if line.startswith('"Country Name"'))
    rows = csv.DictReader(lines[header_index:])
    result = {}
    for row in rows:
        code = row.get("Country Code")
        if code not in COUNTRIES:
            continue
        available = [(int(year), value) for year, value in row.items()
                     if year.isdigit() and int(year) <= target_year and value not in (None, "")]
        if available:
            year, value = max(available)
            result[code] = {"year": year, "value": float(value), "source": url}
    return result


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _normalise_wgi(value: float) -> float | None:
    if not -2.5 <= value <= 2.5:
        return None
    return (2.5 - value) / 5 * 100


def _normalise_growth(value: float) -> float:
    return _clamp((10 - value) / 20 * 100)


def _normalise_debt(value: float) -> float:
    return _clamp(value / 150 * 100)


def _latest(values: dict, code: str, target_year: int) -> tuple[int, float] | None:
    available = [(int(year), value) for year, value in values.get(code, {}).items()
                 if int(year) <= target_year and value is not None]
    return max(available, default=None, key=lambda item: item[0])


def fetch_open_data(target_year: int) -> tuple[dict, dict]:
    raw: dict = {"sources": [], "observations": {}}
    observations = {code: {} for code in COUNTRIES}
    for name, (indicator, _) in WB_INDICATORS.items():
        url = SOURCE_URLS["world_bank"].format(indicator=indicator)
        payload = _get_world_bank(indicator, target_year)
        raw["sources"].append(url)
        for code, item in payload.items():
            observations[code][name] = item
    for name, (indicator, _) in IMF_INDICATORS.items():
        url = SOURCE_URLS["imf"].format(codes=",".join(COUNTRIES), indicator=indicator)
        raw["sources"].append(url)
        try:
            payload = _get_json(url)
        except urllib.error.HTTPError as error:
            raw.setdefault("warnings", []).append(
                f"IMF {indicator} unavailable ({error.code}); component left missing."
            )
            continue
        for code in COUNTRIES:
            selected = _latest(payload.get("values", {}).get(indicator, {}), code, target_year)
            if selected:
                year, value = selected
                observations[code][name] = {"year": year, "value": float(value), "source": url}
    return observations, raw


def _freedom_rows(content: bytes, target_year: int) -> dict[str, dict]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(Path(__file__).with_name("_freedom_house.xlsx"), "r") as workbook:
        strings_root = ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
        strings = ["".join(t.text or "" for t in item.findall(".//m:t", ns))
                   for item in strings_root.findall("m:si", ns)]
        sheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet2.xml"))
    result = {}
    headers = None
    for row in sheet.findall(".//m:row", ns):
        values = {}
        for cell in row.findall("m:c", ns):
            value = cell.find("m:v", ns)
            if value is None:
                continue
            text = value.text or ""
            if cell.get("t") == "s":
                text = strings[int(text)]
            values[cell.get("r", "").rstrip("0123456789")] = text
        if headers is None:
            headers = values
            continue
        if values.get("D") != str(target_year + 1):
            continue
        country = values.get("A")
        match = next((code for code, (name, _) in COUNTRIES.items() if name == country), None)
        if match and values.get("S") not in (None, "N/A", ""):
            result[match] = {
                "year": target_year, "value": float(values["S"]),
                "source": SOURCE_URLS["freedom_house"],
            }
    return result


def score(observations: dict, target_year: int) -> list[dict]:
    rows = []
    for code, (country, cross_check) in COUNTRIES.items():
        values = observations.get(code, {})
        missing = []
        governance_values = []
        for name in WB_INDICATORS:
            item = values.get(name)
            if item is None:
                missing.append(name)
            else:
                normalised = _normalise_wgi(item["value"])
                if normalised is None:
                    missing.append(name)
                else:
                    governance_values.append(normalised)
        government = sum(governance_values) / len(governance_values) if governance_values else None
        macro_values = []
        for name in IMF_INDICATORS:
            item = values.get(name)
            if item is None:
                missing.append(name)
            else:
                macro_values.append(_normalise_growth(item["value"]) if name == "real_gdp_growth"
                                    else _normalise_debt(item["value"]))
        macro = sum(macro_values) / len(macro_values) if macro_values else None
        freedom_item = values.get("freedom_total")
        freedom = None if freedom_item is None else 100 - _clamp(freedom_item["value"], 0, 100)
        if freedom is None:
            missing.append("freedom_total")
        components = [value for value in (government, macro, freedom) if value is not None]
        if not components:
            raise ValueError(f"No usable observations for {code}")
        weights = [weight for value, weight in zip((government, macro, freedom), (0.5, 0.25, 0.25))
                   if value is not None]
        composite = sum(value * weight for value, weight in zip(components, weights)) / sum(weights)
        band = "low" if composite < 25 else "moderate" if composite < 50 else "high" if composite < 75 else "very high"
        years = [item["year"] for item in values.values()]
        rows.append({
            "country_code": code, "country": country, "reference_year": max(years, default=target_year),
            "government_score": None if government is None else round(government, 2),
            "macroeconomic_score": None if macro is None else round(macro, 2),
            "freedom_score": None if freedom is None else round(freedom, 2),
            "composite_score": round(composite, 2), "risk_band": band,
            "available_components": len(components), "missing_indicators": ";".join(missing),
            "qualitative_cross_check": cross_check,
        })
    return rows


def build_index(target_year: int, output_dir: Path) -> list[dict]:
    observations, raw = fetch_open_data(target_year)
    raw["sources"].append(SOURCE_URLS["freedom_house"])
    for warning in raw.get("warnings", []):
        print(f"WARNING: {warning}")
    xlsx_path = Path(__file__).with_name("_freedom_house.xlsx")
    url = SOURCE_URLS["freedom_house"]
    request = urllib.request.Request(url, headers={"User-Agent": "ArtemisForecasting/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        xlsx_path.write_bytes(response.read())
    try:
        for code, item in _freedom_rows(b"", target_year).items():
            observations[code]["freedom_total"] = item
    finally:
        xlsx_path.unlink(missing_ok=True)
    rows = score(observations, target_year)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "country_risk_index.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "country_risk_index.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (output_dir / "source_manifest.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Artemis's open-data country risk index.")
    parser.add_argument("--target-year", type=int, default=2024)
    parser.add_argument("--output-dir", type=Path, default=Path("data/country-risk"))
    args = parser.parse_args()
    rows = build_index(args.target_year, args.output_dir)
    print(f"Wrote {len(rows)} country risk rows to {args.output_dir}")


if __name__ == "__main__":
    main()
