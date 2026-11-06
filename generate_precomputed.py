"""Erzeugt svv_bands.json: die Bänder über feste Instanzen (alle Savings-Läufe je Instanz).

Die Instanzen, die Referenzen (exaktes Optimum bis 12 Kunden, PyVRP 0.14.1 darüber) und die Kosten von Einfügen nach Split stammen aus sgs_bands.json der savings-gegen-split-demo (Stück 4 der Linie,
Ordner daneben); es werden nur Zellen mit Referenz übernommen. Je Instanz rechnet dieses Skript: Savings parallel für 9 λ-Werte (μ = ν = 0), sequentiell für 9 λ-Werte, parallel für 36 Tripel
(λ, μ, ν), je 20 verrauschte Läufe für vier Rauschstufen, dazu wie oft der Split einen der neun Pläne verbessert und die Zeit eines Laufs. PyVRP wird hier nicht gebraucht.

Aufruf (Teile können parallel laufen):
    python generate_precomputed.py cells 100 3 90 --out part_100.json      # Größe, Zielrouten, Auslastungen in Prozent
    python generate_precomputed.py merge part_*.json                      # zu svv_bands.json zusammenführen"""

import argparse
import json
import time
from pathlib import Path

import svv_constants as C
from svv_evaluation import instance_row

TARGET = Path(__file__).with_name(C.BAND_FILE)
SOURCE = Path(__file__).resolve().parent.parent / "savings-gegen-split-demo" / C.SOURCE_BANDS_FILE


def source_cells() -> dict:
    """{(n, Zielrouten, Auslastung, Familie, Depot): {Seed: (Referenz, Kosten von Einfügen nach Split)}} nur für Zellen mit Referenz bei allen Instanzen."""
    out = {}
    for c in json.loads(SOURCE.read_text(encoding="utf-8"))["cells"]:
        if all(r["ref"] is not None for r in c["rows"]):
            out[(c["n"], c["routes"], c["fill"], c["family"], c["depot"])] = {r["seed"]: (r["ref"], r["es"]) for r in c["rows"]}
    return out


def build(n: int, routes: int, fills) -> list[dict]:
    cells, start, src = [], time.time(), source_cells()
    for fill in fills:
        for family, depot in C.BAND_CELLS:
            refs = src[(n, routes, fill, family, depot)]
            rows = [instance_row(n, family, depot, routes, seed, fill, *refs[seed]) for seed in C.BAND_SEEDS[n]]
            cells.append({"n": n, "fill": fill, "routes": routes, "family": family, "depot": depot, "rows": rows})
            print("cells", n, routes, fill, family, depot, f"{time.time() - start:.0f} s", flush=True)
    return cells


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["cells", "merge"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.kind == "merge":
        cells = []
        for f in args.args:
            cells += json.loads(Path(f).read_text(encoding="utf-8"))["cells"]
        key = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
        cells.sort(key=lambda c: (c["routes"], c["n"], c["fill"], key[(c["family"], c["depot"])]))
        meta = {"lams": list(__import__("svv_savings").LAMS), "noise": list(C.BAND_NOISE), "noise_runs": 20, "seeds": {str(n): [s[0], s[-1]] for n, s in C.BAND_SEEDS.items()},
                "source": f"Referenzen und Einfügen nach Split aus {C.SOURCE_BANDS_FILE} (savings-gegen-split-demo, Stück 4)"}
        TARGET.write_text(json.dumps({"meta": meta, "cells": cells}, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", TARGET.name, len(cells), "Zellen")
    else:
        data = {"cells": build(int(args.args[0]), int(args.args[1]), [int(x) for x in args.args[2:]])}
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", args.out)
