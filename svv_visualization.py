"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import svv_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, title_prefix="Route"):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Nummer), jede Route eine Farbe. Gleicher Maßstab in x und y über scaleanchor mit
    autorange; der Rand kommt von zwei unsichtbaren Eckmarken (DEMO-PLAYBOOK §3)."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)], width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    customers = list(range(1, inst.n + 1))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in customers], y=[inst.xy[c][1] for c in customers], mode="markers+text", text=[str(c) for c in customers], textposition="top center",
        marker=dict(size=[9 + 2.5 * inst.demand[c - 1] for c in customers], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in customers], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>", name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, 380)


def _hline(fig, y, text, color, dash="dot"):
    fig.add_hline(y=y, line=dict(color=color, width=1.5, dash=dash), annotation_text=text, annotation_position="top left", annotation_font_size=11)


def build_lambda_curve(curve_par, curve_seq, current_lam, optimum, es_cost):
    """Kosten der parallelen und der sequentiellen Fassung über λ (μ = ν = 0); der gewählte Wert ist markiert, das Optimum und Einfügen nach Split stehen als Linien."""
    lams = sorted(curve_par)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=lams, y=[curve_par[l] for l in lams], mode="lines+markers", name="parallel", line=dict(color=C.COLOR_SAVINGS, width=3, shape="hv"), marker=dict(size=6),
                             hovertemplate="λ = %{x:.1f}: %{y:.2f}<extra>parallel</extra>"))
    fig.add_trace(go.Scatter(x=lams, y=[curve_seq[l] for l in lams], mode="lines+markers", name="sequentiell", line=dict(color="#999999", width=2, dash="dash", shape="hv"), marker=dict(size=5),
                             hovertemplate="λ = %{x:.1f}: %{y:.2f}<extra>sequentiell</extra>"))
    if current_lam in curve_par:
        fig.add_trace(go.Scatter(x=[current_lam], y=[curve_par[current_lam]], mode="markers", name="gewähltes λ", marker=dict(size=13, symbol="diamond", color=C.COLOR_OPT, line=dict(color="#222", width=1)),
                                 hovertemplate="gewähltes λ = %{x:.1f}: %{y:.2f}<extra></extra>"))
    _hline(fig, optimum, f"Optimum {optimum:.2f}", C.COLOR_OPT)
    _hline(fig, es_cost, f"Einfügen nach Split {es_cost:.2f}", C.COLOR_SPLIT, "dash")
    fig.update_xaxes(title_text="Formparameter λ")
    fig.update_yaxes(title_text="Gesamtlänge")
    fig = _base(fig, 380)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=60), legend=dict(orientation="h", y=-0.28))
    return fig


def build_noise_strip(costs, base_cost, optimum, es_cost):
    """Die Kosten der verrauschten Läufe, aufsteigend sortiert; Linien: Lauf ohne Rauschen, Optimum, Einfügen nach Split."""
    order = sorted(costs)
    fig = go.Figure(go.Scatter(x=list(range(1, len(order) + 1)), y=order, mode="markers", marker=dict(size=9, color=C.COLOR_SAVINGS), name="verrauschter Lauf",
                               hovertemplate="Platz %{x}: %{y:.2f}<extra></extra>"))
    _hline(fig, base_cost, f"ohne Rauschen {base_cost:.2f}", "#4c78a8")
    _hline(fig, optimum, f"Optimum {optimum:.2f}", C.COLOR_OPT)
    _hline(fig, es_cost, f"Einfügen nach Split {es_cost:.2f}", C.COLOR_SPLIT, "dash")
    fig.update_xaxes(title_text="Läufe, nach Kosten sortiert", dtick=5)
    fig.update_yaxes(title_text="Gesamtlänge")
    fig = _base(fig, 340)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=40), showlegend=False)
    return fig


def build_bands(gaps_by_key, names, colors):
    """Median des Abstands zur Referenz in Prozent je Strategie, mit Spanne (Minimum bis Maximum) als Fehlerbalken."""
    keys = [k for k in names if k in gaps_by_key]
    fig = go.Figure(go.Bar(
        x=[names[k] for k in keys], y=[gaps_by_key[k]["median"] for k in keys], marker_color=[colors[k] for k in keys],
        error_y=dict(type="data", symmetric=False, array=[gaps_by_key[k]["max"] - gaps_by_key[k]["median"] for k in keys], arrayminus=[gaps_by_key[k]["median"] - gaps_by_key[k]["min"] for k in keys]),
        hovertemplate="%{x}: Median %{y:.1f} %<extra></extra>", name="Median (Balken: Minimum bis Maximum)"))
    fig.update_yaxes(title_text="Abstand zur Referenz (%)", rangemode="tozero")
    fig.update_xaxes(tickangle=-20)
    fig = _base(fig, 400)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=110))
    return fig


def build_band_curve(curve_par, curve_seq, es_median):
    """Median des Abstands über den neun λ-Werten (parallel und sequentiell) und der Median von Einfügen nach Split."""
    lams = sorted(curve_par)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=lams, y=[curve_par[l] for l in lams], mode="lines+markers", name="parallel", line=dict(color=C.COLOR_SAVINGS, width=3), marker=dict(size=7), hovertemplate="λ = %{x:.1f}: %{y:.1f} %<extra>parallel</extra>"))
    fig.add_trace(go.Scatter(x=lams, y=[curve_seq[l] for l in lams], mode="lines+markers", name="sequentiell", line=dict(color="#999999", width=2, dash="dash"), marker=dict(size=6),
                             hovertemplate="λ = %{x:.1f}: %{y:.1f} %<extra>sequentiell</extra>"))
    _hline(fig, es_median, f"Einfügen nach Split {es_median:.1f} %", C.COLOR_SPLIT, "dash")
    fig.update_xaxes(title_text="Formparameter λ", dtick=0.2)
    fig.update_yaxes(title_text="Median des Abstands (%)", rangemode="tozero")
    fig = _base(fig, 360)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=60), legend=dict(orientation="h", y=-0.28))
    return fig
