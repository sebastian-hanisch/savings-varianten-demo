"""Die fünf Experimente der App per AppTest: λ-Regler (mit μ und ν), parallel gegen sequentiell, Rauschen und Kippstellen, Mehrfachrechnen und Bänder (inklusive kurzer Routen); dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import svv_constants as C
import svv_evaluation as ev
from svv_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SHORT = f"Kurze Routen ({C.SHORT_N} Kunden, {C.SHORT_ROUTES} Zielrouten)"
SETTING_KEYS = {"n": "n_slider", "family": "family_select", "depot": "depot_select", "routes": "routes_slider", "fill": "fill_slider", "seed": "seed_input"}


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning])


def test_lambda_slider_changes_the_plan_and_the_verdict_on_the_hand_preset():
    at = _app("Zwei Paare vertauschen die Plätze (n = 6)")
    assert "Mit λ = 1,0 kostet Savings 62,26" in _texts(at)
    at.slider(key="lam_slider").set_value(0.8).run()
    assert not at.exception and "Mit λ = 0,8 kostet Savings 56,73 (2 Routen, 0,0 %" in _texts(at) and "Die Wahl ist 8,9 % billiger" in _texts(at)
    assert "10,23" in " ".join(m.value for m in at.markdown) and "8,79" in " ".join(m.value for m in at.markdown)         # die erste abweichende Zusammenlegung (Tabelle)


def test_mu_and_nu_sliders_work_at_their_limits():
    at = _app()
    for key, value in (("mu_slider", C.MU_MAX), ("nu_slider", C.NU_MIN), ("nu_slider", C.NU_MAX), ("mu_slider", C.MU_MIN)):
        at.slider(key=key).set_value(value).run()
        assert not at.exception, (key, value)
    at.slider(key="lam_slider").set_value(C.LAM_MAX).run()
    assert not at.exception and "λ = 2,4" in _texts(at)
    at.slider(key="lam_slider").set_value(C.LAM_MIN).run()
    assert not at.exception and "λ = 0,2" in _texts(at)


def test_sequential_experiment_shows_both_plans():
    text = _texts(_app())
    assert "parallel 459,10 (4 Routen), sequentiell 492,45 (3 Routen)" in text and "7,3 % teurer" in text


def test_noise_and_swaps_controls():
    at = _app("λ oder Rauschen finden das Optimum (n = 8)")
    assert "20 Läufe mit Rauschen 1,0 %" in _texts(at) and "Von 27 Vertauschungen benachbarter Paare ändern 2 den Plan" in _texts(at)
    at.slider(key="eps_slider").set_value(0.0).run()
    assert not at.exception and "20 Läufe mit Rauschen 0,0 %: 20 von 20 liefern denselben Plan" in _texts(at) and "1 verschiedene" in _texts(at)
    at.slider(key="eps_slider").set_value(C.EPS_MAX).run()
    at.slider(key="runs_slider").set_value(C.RUNS_MAX).run()
    assert not at.exception and f"{C.RUNS_MAX} Läufe mit Rauschen 10,0 %" in _texts(at)
    at.slider(key="runs_slider").set_value(C.RUNS_MIN).run()
    assert not at.exception and f"{C.RUNS_MIN} Läufe" in _texts(at)


def test_strategy_table_and_map_selection():
    at = _app()
    for key in C.STRATEGY_KEYS:
        at.selectbox(key="strategy_pick").set_value(key).run()
        assert not at.exception, key
    table = [m.value for m in at.markdown if m.value.startswith("| Strategie | Läufe | Kosten")][0]
    assert all(C.STRATEGY_NAMES[k] in table for k in C.STRATEGY_KEYS)


def test_band_selection_for_every_size_and_fill():
    at = _app()
    for n in C.BAND_SIZES:
        at.radio(key="band_n").set_value(n).run()
        assert not at.exception, n
        for fill in C.BAND_FILLS[n]:
            at.radio(key=f"band_fill_{n}_{C.BAND_ROUTES}").set_value(fill).run()
            assert not at.exception, (n, fill)
            assert f"Bei n = {n}, 3 Routen, Auslastung {fill} %" in _texts(at)


def test_short_routes_option_shows_the_eight_route_bands():
    at = _app()
    at.radio(key="band_kind").set_value(SHORT).run()
    assert not at.exception and f"Bei n = {C.SHORT_N}, {C.SHORT_ROUTES} Routen, Auslastung 90 %" in _texts(at)
    at.radio(key=f"band_fill_{C.SHORT_N}_{C.SHORT_ROUTES}").set_value(98).run()
    assert not at.exception and "Auslastung 98 %" in _texts(at)


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["n"], preset["family"], preset["depot"], preset["routes"], preset["fill"], preset["seed"])
        data = build_pdf(s, ev.analyse(s))
        assert data[:5] == b"%PDF-" and len(data) > 1500
