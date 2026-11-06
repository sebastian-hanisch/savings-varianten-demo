"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import svv_constants as C
from svv_evaluation import Analysis, Settings, de, gap_percent, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Savings variieren"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Auslastung {s.fill} %, Seed {s.seed}. "
                            f"Kapazität {a.inst.capacity}, Gesamtnachfrage {sum(a.inst.demand)}, Mindestroutenzahl {a.min_routes}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (74, 16, 26, 36, 30)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Strategie", "Läufe", "Kosten", "Über Optimum", "Routen")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    rows = [("Optimum (alle Tourenpläne)", "-", a.exact.cost, len(a.exact.routes))]
    rows += [(C.STRATEGY_NAMES[k], a.strategies[k].runs, a.strategies[k].cost, len(a.strategies[k].routes)) for k in C.STRATEGY_KEYS]
    for name, runs, cost, k in rows:
        for w, v in zip(widths, (name, str(runs), de(cost), pct(gap_percent(cost, a.exact.cost)), str(k))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Kosten über den Formparameter lambda (mu = nu = 0)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _s("parallel: " + ", ".join(f"{lam:.1f}: {de(c)}" for lam, c in a.curve_par.items() if round(lam * 10) % 2 == 0)), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s("sequentiell: " + ", ".join(f"{lam:.1f}: {de(c)}" for lam, c in a.curve_seq.items() if round(lam * 10) % 2 == 0)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Savings legt Einzelrouten nach absteigender Ersparnis zusammen; lambda, mu und nu gewichten die Ersparnis. Bestes von k Läufen: der billigste Plan. "
                            "Quelle: savings-varianten-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
