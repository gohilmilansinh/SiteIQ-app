from __future__ import annotations

from typing import Any, Dict

import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from report import generate_report
from benchmarks import get_category_context
import os
from roi_calculator import calculate_roi
from score_explainer import explain_scores
from brand_registry import detect_known_brands
from persistence import get_address_history

def render_address_trend(address: str) -> None:
    """Renders score trend chart + table for a specific address."""
    history = get_address_history(address)

    if len(history) < 2:
        return  # Need at least 2 data points for a trend

    st.markdown("### Score Trend for This Location")
    st.markdown(
        f"<div style='font-size:12px;color:#888;margin-bottom:12px'>"
        f"This site has been scored {len(history)} times. "
        f"Showing how scores have changed over time.</div>",
        unsafe_allow_html=True,
    )

    timestamps  = [h.get("timestamp", "") for h in history]
    totals      = [h.get("total_score", 0) for h in history]
    short_times = [t[:12] if t else "" for t in timestamps]

    # ── Delta badge ───────────────────────────────────────
    first_score = totals[0]
    last_score  = totals[-1]
    delta       = round(last_score - first_score, 1)
    delta_col   = "#1D9E75" if delta >= 0 else "#C0392B"
    delta_str   = f"+{delta}" if delta >= 0 else str(delta)

    col1, col2, col3 = st.columns(3)
    col1.metric(f"First Score",  first_score)
    col2.metric(f"Latest Score", last_score, delta=delta_str)
    col3.metric(f"Times Scored", len(history))

    # ── Line chart ────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(history))),
        y=totals,
        mode="lines+markers",
        line=dict(color="#1D9E75", width=2),
        marker=dict(
            color=[
                "#1D9E75" if s >= 65
                else "#BA7517" if s >= 45
                else "#C0392B"
                for s in totals
            ],
            size=12,
            line=dict(color="#0A2E26", width=2),
        ),
        text=short_times,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Score: %{y}<extra></extra>"
        ),
    ))
    fig.add_hline(
        y=65, line_dash="dash", line_color="#1D9E75",
        opacity=0.4, annotation_text="Strong",
        annotation_font_color="#1D9E75",
        annotation_font_size=10,
    )
    fig.add_hline(
        y=45, line_dash="dash", line_color="#BA7517",
        opacity=0.4, annotation_text="Moderate",
        annotation_font_color="#BA7517",
        annotation_font_size=10,
    )
    fig.update_layout(
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickvals=list(range(len(history))),
            ticktext=short_times,
            tickangle=-30,
            tickfont=dict(size=9),
        ),
        yaxis=dict(range=[0, 105], title="Score"),
        margin=dict(l=10, r=10, t=20, b=60),
        showlegend=False,
    )
    import hashlib
    chart_key = hashlib.md5(address.encode()).hexdigest()[:8]
    st.plotly_chart(fig, use_container_width=True, key=f"trend_{chart_key}")

    # ── History table ─────────────────────────────────────
    st.markdown("**All Scores for This Address**")
    rows_html = ""
    for idx, h in enumerate(reversed(history)):
        sc      = h.get("total_score", 0)
        verdict = h.get("verdict", "")
        col     = (
            "#1D9E75" if sc >= 65
            else "#BA7517" if sc >= 45
            else "#C0392B"
        )
        scores  = h.get("scores", {})
        is_latest = idx == 0

        rows_html += (
            f"<tr style='background:{'#0d1f1a' if is_latest else 'transparent'}'>"
            f"<td style='padding:8px 12px;color:#9ecfc0;font-size:11px'>"
            f"{'⭐ Latest' if is_latest else f'#{len(history)-idx}'}</td>"
            f"<td style='padding:8px 12px;color:#888;font-size:11px'>"
            f"{h.get('timestamp','')}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:{col};font-weight:700;font-size:15px'>{sc}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:{col};font-size:11px'>{verdict}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:#9ecfc0;font-size:11px'>"
            f"{scores.get('demand','-')}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:#9ecfc0;font-size:11px'>"
            f"{scores.get('footfall','-')}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:#9ecfc0;font-size:11px'>"
            f"{scores.get('competition','-')}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:#9ecfc0;font-size:11px'>"
            f"{scores.get('accessibility','-')}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:#9ecfc0;font-size:11px'>"
            f"{scores.get('catchment','-')}</td>"
            f"<td style='padding:8px 12px;text-align:center;"
            f"color:#9ecfc0;font-size:11px'>"
            f"{scores.get('spending_power','-')}</td>"
            f"</tr>"
        )

    table_html = f"""<!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      body{{margin:0;background:transparent;font-family:sans-serif}}
      .wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;
             border-radius:8px;border:1px solid #1a1a1a}}
      table{{width:100%;min-width:700px;border-collapse:collapse;
             font-size:12px}}
      thead tr{{background:#0A2E26}}
      th{{padding:10px 12px;color:#9ecfc0;font-size:10px;
          letter-spacing:.5px;text-align:center;font-weight:600;
          white-space:nowrap}}
      th:nth-child(2){{text-align:left}}
      tbody tr{{border-bottom:1px solid #1a1a1a}}
    </style></head><body>
    <div class="wrap"><table>
      <thead><tr>
        <th>#</th><th style='text-align:left'>DATE</th>
        <th>TOTAL</th><th>VERDICT</th>
        <th>DEMAND</th><th>FOOTFALL</th><th>COMP</th>
        <th>ACCESS</th><th>CATCH</th><th>SPEND</th>
      </tr></thead>
      <tbody style='color:white'>{rows_html}</tbody>
    </table></div></body></html>"""

    import streamlit.components.v1 as components
    components.html(
        table_html,
        height=60 + len(history) * 50
    )

def render_score_breakdown(result: Dict[str, Any], brand_type: str) -> None:
    scores = result.get("scores", {})
    total = result["total_score"]
    verdict = result["verdict"]
    lat, lng = result["lat"], result["lng"]
    vc = (
        "#1D9E75"
        if verdict == "Strong"
        else "#BA7517" if verdict == "Moderate" else "#C0392B"
    )

    benchmark = get_category_context(total, brand_type)
    stats = benchmark["stats"]
    percentile = benchmark["percentile"]
    bar_color = (
        "#1D9E75" if percentile >= 65 else "#BA7517" if percentile >= 40 else "#C0392B"
    )

    st.markdown("---")

    st.markdown(
        f"""
    <div style='background:#0A2E26;border-radius:12px;
                padding:20px 28px;margin-bottom:16px;
                display:flex;align-items:center;
                justify-content:space-between;flex-wrap:wrap;gap:16px'>
      <div>
        <div style='font-size:11px;color:#9ecfc0;
                    letter-spacing:1px;margin-bottom:4px'>SITE SCORE</div>
        <div style='font-size:52px;font-weight:700;
                    color:{vc};line-height:1'>{total}</div>
        <div style='font-size:12px;color:#9ecfc0;margin-top:2px'>
          out of 100</div>
      </div>
      <div style='text-align:center'>
        <div style='font-size:18px;font-weight:700;
                    color:{vc}'>{verdict.upper()} SITE</div>
        <div style='font-size:12px;color:#9ecfc0;margin-top:4px'>
          {result['address'][:60]}</div>
      </div>
      <div style='text-align:right;min-width:160px'>
        <div style='font-size:11px;color:#9ecfc0;margin-bottom:6px'>
          BETTER THAN {percentile}% OF SIMILAR SITES
        </div>
        <div style='background:#1a4a3a;border-radius:4px;height:8px'>
          <div style='width:{min(percentile,100)}%;
                      background:{bar_color};
                      height:8px;border-radius:4px'></div>
        </div>
        <div style='display:flex;justify-content:space-between;
                    font-size:10px;color:#9ecfc0;margin-top:4px'>
          <span>Avg {stats['average']}</span>
          <span>Top {stats['top_sites_avg']}</span>
        </div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Score pills
    score_items = [
        ("Demand", scores["demand"]),
        ("Footfall", scores["footfall"]),
        ("Competition", scores["competition"]),
        ("Accessibility", scores["accessibility"]),
        ("Catchment", scores["catchment"]),
        ("Spending Power", scores["spending_power"]),
    ]
    pills = ""
    for label, s in score_items:
        col = "#1D9E75" if s >= 65 else "#BA7517" if s >= 45 else "#C0392B"
        pills += f"""
        <div style='flex:1;min-width:80px;background:#111;
                    border:1px solid #222;border-radius:8px;
                    padding:10px 8px;text-align:center'>
          <div style='font-size:20px;font-weight:700;color:{col}'>{s}</div>
          <div style='font-size:10px;color:#888;margin-top:2px'>{label}</div>
        </div>"""

    components.html(
        f"""
    <div style='display:flex;gap:8px;flex-wrap:wrap;
                font-family:sans-serif'>
      {pills}
    </div>
    """,
        height=80,
    )

    # Radar chart
    st.markdown("### Score Breakdown")
    col_left, col_chart, col_right = st.columns([1, 6, 1])
    with col_chart:
        cats = [
            "Demand",
            "Footfall",
            "Competition",
            "Accessibility",
            "Catchment",
            "Spending Power",
        ]
        vals = [
            scores["demand"],
            scores["footfall"],
            scores["competition"],
            scores["accessibility"],
            scores["catchment"],
            scores["spending_power"],
        ]
        fig = go.Figure(
            go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(29,158,117,0.15)",
                line=dict(color="#1D9E75", width=2),
                marker=dict(color="#1D9E75", size=7),
            )
        )
        fig.update_layout(
            polar=dict(
                bgcolor="#0d1f1a",
                radialaxis=dict(visible=True, range=[0, 100]),
                angularaxis=dict(tickfont=dict(size=12, color="#ccc")),
            ),
            showlegend=False,
            height=380,
            margin=dict(l=60, r=60, t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Map
    st.markdown("### Location Map")
    col_left, col_map, col_right = st.columns([1, 10, 1])
    with col_map:
        m = folium.Map(location=[lat, lng], zoom_start=15, tiles="CartoDB positron")
        folium.CircleMarker(
            location=[lat, lng],
            radius=14,
            color="#0A2E26",
            fill=True,
            fill_color=vc,
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>{result['address']}</b><br>Score: {total}/100", max_width=220
            ),
        ).add_to(m)
        folium.Circle(
            location=[lat, lng],
            radius=500,
            color="#1D9E75",
            fill=True,
            fill_color="#1D9E75",
            fill_opacity=0.05,
        ).add_to(m)
        folium.Circle(
            location=[lat, lng], radius=1000, color="#BA7517", fill=False
        ).add_to(m)
        st_folium(m, width="100%", height=400, returned_objects=[])

    # ── Score Explainability ──────────────────────────────
    st.markdown("### Why This Score?")

    explanation = explain_scores(
        scores=scores,
        brand_type=brand_type,
        total_score=total,
    )

    # Narrative summary
    if explanation["narrative"]:
        st.markdown(
            f"<div style='background:#111;border-left:3px solid #1D9E75;"
            f"padding:12px 16px;border-radius:0 8px 8px 0;"
            f"font-size:13px;color:#ccc;margin-bottom:16px'>"
            f"{explanation['narrative']}</div>",
            unsafe_allow_html=True,
        )

    # Contribution table
    contribs = explanation["contributions"]

    # Build HTML table
    rows_html = ""
    for c in contribs:
        score_col = (
            "#1D9E75" if c["score"] >= 65
            else "#BA7517" if c["score"] >= 45
            else "#C0392B"
        )
        delta_col = "#1D9E75" if c["delta"] >= 0 else "#C0392B"
        delta_str = (
            f"+{c['delta']}" if c["delta"] >= 0
            else str(c["delta"])
        )
        vs_avg_str = (
            f"+{c['vs_avg']}" if c["vs_avg"] >= 0
            else str(c["vs_avg"])
        )
        vs_avg_col = "#1D9E75" if c["vs_avg"] >= 0 else "#C0392B"

        # Bar showing score vs average
        bar_score_w = int(c["score"])
        bar_avg_w   = int(c["avg_score"])

        rows_html += f"""
        <tr>
          <td style='padding:10px 12px;color:white;
                     font-weight:500;min-width:130px'>
            {c['label']}
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:{score_col};font-weight:700;
                     font-size:15px'>
            {c['score']}
          </td>
          <td style='padding:10px 24px;min-width:160px'>
            <div style='position:relative;height:8px;
                        background:#222;border-radius:4px'>
              <div style='position:absolute;left:0;top:0;
                          width:{bar_avg_w}%;height:8px;
                          background:#333;border-radius:4px'></div>
              <div style='position:absolute;left:0;top:0;
                          width:{bar_score_w}%;height:8px;
                          background:{score_col};border-radius:4px;
                          opacity:0.85'></div>
              <div style='position:absolute;left:{bar_avg_w}%;
                          top:-3px;width:2px;height:14px;
                          background:#888'></div>
            </div>
            <div style='font-size:9px;color:#555;margin-top:3px'>
              avg {c['avg_score']}
            </div>
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:#888;font-size:12px'>
            {c['weight_pct']}%
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:{delta_col};font-weight:600'>
            {delta_str}
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:{vs_avg_col};font-size:12px'>
            {vs_avg_str} vs avg
          </td>
          <td style='padding:10px 12px;font-size:11px;
                     color:#666;max-width:180px'>
            {c['insight']}
          </td>
        </tr>"""

    explainer_html = f"""
    <!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body{{margin:0;background:transparent;font-family:sans-serif}}
      .wrap{{overflow-x:auto;overflow-y:auto;-webkit-overflow-scrolling:touch}}
      html,body{{height:100%;margin:0;padding:0}}
      table{{width:100%;min-width:600px;border-collapse:collapse;font-size:13px}}
      thead tr{{background:#0A2E26}}
      th{{padding:10px 12px;color:#9ecfc0;font-size:10px;
          letter-spacing:.5px;text-align:center;font-weight:600}}
      th:first-child{{text-align:left}}
      tbody tr{{border-bottom:1px solid #1a1a1a}}
      tbody tr:hover{{background:#0d1f1a}}
    </style></head><body>
    <div class="wrap" style="height:100%;width:100%">
    <table>
      <thead><tr>
        <th style='text-align:left'>VARIABLE</th>
        <th>SCORE</th>
        <th style='text-align:left;padding-left:24px'>
          SCORE vs AVERAGE
        </th>
        <th>WEIGHT</th>
        <th>CONTRIBUTION</th>
        <th>VS AVG</th>
        <th style='text-align:left'>INSIGHT</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    </body></html>"""

    components.html(
        explainer_html,
        height=20 + len(contribs) * 50
    )

    # Risk + boost highlights
    col_boost, col_drag = st.columns(2)

    with col_boost:
        if explanation["biggest_boost"]:
            b = explanation["biggest_boost"]
            st.markdown(
                f"<div style='background:#0d1f1a;border:1px solid #1D9E75;"
                f"border-radius:8px;padding:14px'>"
                f"<div style='font-size:10px;color:#9ecfc0;"
                f"letter-spacing:1px;margin-bottom:4px'>"
                f"BIGGEST STRENGTH</div>"
                f"<div style='font-size:16px;font-weight:700;"
                f"color:#1D9E75'>{b['label']}</div>"
                f"<div style='font-size:13px;color:#ccc;margin-top:4px'>"
                f"Score {b['score']} — "
                f"{abs(b['vs_avg']):.0f} pts above average</div>"
                f"<div style='font-size:11px;color:#888;margin-top:6px'>"
                f"{b['insight']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with col_drag:
        if explanation["biggest_drag"]:
            d = explanation["biggest_drag"]
            st.markdown(
                f"<div style='background:#1a0e0e;border:1px solid #C0392B;"
                f"border-radius:8px;padding:14px'>"
                f"<div style='font-size:10px;color:#e08080;"
                f"letter-spacing:1px;margin-bottom:4px'>"
                f"BIGGEST DRAG</div>"
                f"<div style='font-size:16px;font-weight:700;"
                f"color:#C0392B'>{d['label']}</div>"
                f"<div style='font-size:13px;color:#ccc;margin-top:4px'>"
                f"Score {d['score']} — "
                f"{abs(d['vs_avg']):.0f} pts below average</div>"
                f"<div style='font-size:11px;color:#888;margin-top:6px'>"
                f"{d['insight']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Nearby Competitors ────────────────────────────────
    if result.get("competitor_details"):
        st.markdown("### Nearby Competitors")

        # ── Known brand flags ─────────────────────────────
        known_brands = detect_known_brands(
            result["competitor_details"], brand_type
        )
        if known_brands:
            threat_colors = {
                "high":   "#C0392B",
                "medium": "#BA7517",
                "low":    "#1D9E75",
            }
            threat_labels = {
                "high":   "HIGH THREAT",
                "medium": "MEDIUM THREAT",
                "low":    "LOW THREAT",
            }
            threat_icons = {
                "high":   "🔴",
                "medium": "🟡",
                "low":    "🟢",
            }

            st.markdown(
                "<div style='background:#1a0e0e;border:1px solid #C0392B;"
                "border-radius:10px;padding:14px 16px;margin-bottom:16px'>"
                "<div style='font-size:11px;font-weight:700;color:#e08080;"
                "letter-spacing:1px;margin-bottom:10px'>⚠️ KNOWN BRANDS DETECTED NEARBY</div>"
                + "".join([
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;padding:8px 10px;margin-bottom:6px;"
                    f"background:#111;border-radius:6px;"
                    f"border-left:3px solid {threat_colors[b['threat']]}'>"
                    f"<div>"
                    f"<span style='font-size:13px;font-weight:700;color:white'>"
                    f"{threat_icons[b['threat']]} {b['brand']}</span>"
                    f"<span style='font-size:11px;color:#666;margin-left:10px'>"
                    f"{b['distance_m']}m away</span>"
                    f"</div>"
                    f"<div style='text-align:right'>"
                    f"<div style='font-size:10px;font-weight:700;"
                    f"color:{threat_colors[b['threat']]};"
                    f"letter-spacing:0.5px'>{threat_labels[b['threat']]}</div>"
                    f"<div style='font-size:10px;color:#666'>"
                    f"★ {b['rating']} · {b['reviews']:,} reviews</div>"
                    f"</div></div>"
                    for b in known_brands
                ])
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#0d1f1a;border:1px solid #1D9E75;"
                "border-radius:8px;padding:10px 14px;margin-bottom:16px;"
                "font-size:12px;color:#9ecfc0'>"
                "✅ No major national/regional chains detected nearby</div>",
                unsafe_allow_html=True,
            )

        competitors = sorted(
            result["competitor_details"],
            key=lambda x: x.get("strength", 0),
            reverse=True,
        )[:8]

        col_left, col_comp, col_right = st.columns([1, 10, 1])
        with col_comp:
            for comp in competitors:
                strength   = comp.get("strength", 0)
                dist_m     = comp.get("distance_m", 0)
                bar_col    = (
                    "#C0392B" if strength > 0.6
                    else "#BA7517" if strength > 0.3
                    else "#1D9E75"
                )
                bar_w      = int(min(strength * 100, 100))
                stars      = (
                    "★" * int(round(comp.get("rating", 0))) +
                    "☆" * (5 - int(round(comp.get("rating", 0))))
                )
                rev_label  = (
                    f"{comp.get('reviews', 0):,} reviews"
                    if comp.get("reviews", 0) > 0
                    else "No reviews"
                )
                label_text = (
                    "Strong" if strength > 0.6
                    else "Moderate" if strength > 0.3
                    else "Weak"
                )
                dist_label = (
                    f"{dist_m}m away"
                    if dist_m > 0 else ""
                )
                dist_color = (
                    "#C0392B" if dist_m <= 100
                    else "#BA7517" if dist_m <= 250
                    else "#888"
                )

                st.markdown(
                    f"<div style='background:#111;border:1px solid #222;"
                    f"border-radius:8px;padding:10px 14px;"
                    f"margin-bottom:6px'>"
                    f"<div style='display:flex;justify-content:"
                    f"space-between;align-items:center;margin-bottom:6px'>"
                    f"<div>"
                    f"<span style='font-size:13px;font-weight:600;"
                    f"color:white'>{comp['name']}</span>"
                    f"<span style='font-size:11px;color:{dist_color};"
                    f"margin-left:10px'>{dist_label}</span>"
                    f"</div>"
                    f"<span style='font-size:11px;color:#888'>"
                    f"{stars} &nbsp;{rev_label}</span>"
                    f"</div>"
                    f"<div style='display:flex;align-items:center;"
                    f"gap:10px'>"
                    f"<div style='flex:1;background:#333;"
                    f"border-radius:4px;height:6px'>"
                    f"<div style='width:{bar_w}%;background:{bar_col};"
                    f"height:6px;border-radius:4px'></div></div>"
                    f"<span style='font-size:11px;color:{bar_col};"
                    f"min-width:100px;text-align:right'>"
                    f"{label_text} competitor</span>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )


    # Risk assessment below
    st.markdown("### Risk Assessment")
    risks = []
    if scores.get("competition", 100)   < 30:
        risks.append("High competitor density within 500m — market may be saturated")
    if scores.get("demand", 100)        < 40:
        risks.append("Low residential population density — walk-in base limited")
    if scores.get("footfall", 100)      < 40:
        risks.append("Few anchor stores within 500m")
    if scores.get("accessibility", 100) < 40:
        risks.append("Limited road connectivity")

    if risks:
        for r in risks:
            st.markdown(
                f"<div style='background:#1a0e0e;border-left:3px solid "
                f"#C0392B;padding:8px 12px;border-radius:0 6px 6px 0;"
                f"font-size:12px;color:#ccc;margin-bottom:6px'>"
                f"! {r}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='background:#0d1f1a;border-left:3px solid #1D9E75;"
            "padding:8px 12px;border-radius:0 6px 6px 0;"
            "font-size:12px;color:#9ecfc0'>"
            "No significant risk flags at this location</div>",
            unsafe_allow_html=True,
        )

    # ── ROI Calculator ────────────────────────────────────
    st.markdown("### ROI Analysis")
    st.markdown(
        "<div style='font-size:12px;color:#888;margin-bottom:12px'>"
        "Enter monthly rent to calculate return on investment. "
        "Revenue estimates use Gujarat market benchmarks.</div>",
        unsafe_allow_html=True,
    )

    col_rent, col_setup = st.columns(2)
    with col_rent:
        monthly_rent = st.number_input(
            "Monthly Rent (Rs.)",
            min_value=0,
            max_value=2000000,
            value=0,
            step=5000,
            help="Enter the monthly rent quoted for this site",
            key=f"rent_{result['address'][:15]}",
        )
    with col_setup:
        setup_cost = st.number_input(
            "Setup / Fit-out Cost (Rs.)",
            min_value=0,
            max_value=10000000,
            value=0,
            step=50000,
            help="One-time setup cost — leave 0 to use category benchmark",
            key=f"setup_{result['address'][:15]}",
        )

    if monthly_rent > 0:
        roi = calculate_roi(
            total_score=result["total_score"],
            monthly_rent=monthly_rent,
            brand_type=result.get("brand_type", "restaurant"),
            setup_cost=setup_cost if setup_cost > 0 else None,
        )

        # ROI summary banner
        st.markdown(f"""
        <div style='background:#0A2E26;border-radius:12px;
                    padding:20px 24px;margin:12px 0'>
          <div style='display:flex;justify-content:space-between;
                      align-items:center;flex-wrap:wrap;gap:12px'>
            <div>
              <div style='font-size:10px;color:#9ecfc0;
                          letter-spacing:1px'>COMBINED SCORE</div>
              <div style='font-size:42px;font-weight:700;
                          color:{roi["verdict_color"]};line-height:1'>
                {roi["combined_score"]}</div>
              <div style='font-size:11px;color:#9ecfc0'>
                Location {roi["location_score"]} × 70% + 
                ROI {roi["roi_score"]} × 30%</div>
            </div>
            <div style='text-align:center'>
              <div style='font-size:16px;font-weight:700;
                          color:{roi["verdict_color"]}'>
                {roi["verdict"]}</div>
              <div style='font-size:11px;color:#9ecfc0;margin-top:4px'>
                {roi["recommendation"]}</div>
            </div>
            <div style='text-align:right'>
              <div style='font-size:10px;color:#9ecfc0'>RENT RATING</div>
              <div style='font-size:20px;font-weight:700;
                          color:{roi["rent_color"]}'>
                {roi["rent_label"]}</div>
              <div style='font-size:11px;color:#9ecfc0'>
                {roi["rent_pct_of_revenue"]}% of est. revenue</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        def fmt_inr(amount):
            if amount >= 100000:
                return f"Rs. {amount/100000:.1f}L"
            return f"Rs. {amount:,.0f}"

        col1.metric(
            "Est. Monthly Revenue",
            fmt_inr(roi["est_monthly_revenue"]),
            help="Based on site score and Gujarat category benchmarks"
        )
        col2.metric(
            "Monthly Profit",
            fmt_inr(roi["monthly_profit"]),
            delta=fmt_inr(roi["monthly_profit"]),
            delta_color="normal"
        )
        col3.metric(
            "Annual Profit",
            fmt_inr(roi["annual_profit"]),
        )
        col4.metric(
            "Payback Period",
            f"{roi['payback_months']:.0f} months"
            if roi["payback_months"] < 999
            else "Not viable",
            help="Months to recover total setup cost"
        )

        # Rent sensitivity table
        st.markdown("**Rent Sensitivity — what different rent levels mean**")

        rent_levels = [
            monthly_rent * 0.6,
            monthly_rent * 0.8,
            monthly_rent,
            monthly_rent * 1.2,
            monthly_rent * 1.4,
        ]
        labels = ["-40%", "-20%", "Current", "+20%", "+40%"]

        rows = ""
        for label, rent in zip(labels, rent_levels):
            r = calculate_roi(
                result["total_score"], rent,
                result.get("brand_type", "restaurant"),
                setup_cost if setup_cost > 0 else None
            )
            is_current = label == "Current"
            bg = "#1a3a2a" if is_current else "transparent"
            rows += (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:8px 12px;color:#9ecfc0;"
                f"font-weight:{'700' if is_current else '400'}'>"
                f"{label}</td>"
                f"<td style='padding:8px 12px;color:white'>"
                f"Rs. {rent:,.0f}</td>"
                f"<td style='padding:8px 12px;"
                f"color:{r['rent_color']};font-weight:600'>"
                f"{r['rent_label']}</td>"
                f"<td style='padding:8px 12px;color:white'>"
                f"Rs. {r['monthly_profit']:,.0f}</td>"
                f"<td style='padding:8px 12px;color:white'>"
                f"{r['payback_months']:.0f} mo"
                if r['payback_months'] < 999
                else "<td style='padding:8px 12px;color:#C0392B'>Not viable"
                f"</td></tr>"
            )

        sensitivity_html = f"""
        <!DOCTYPE html><html><head>
        <style>
          body{{margin:0;background:transparent;font-family:sans-serif}}
          table{{width:100%;border-collapse:collapse;font-size:13px}}
          th{{padding:10px 12px;background:#0A2E26;color:#9ecfc0;
              font-size:11px;text-align:left;letter-spacing:.5px}}
          tr{{border-bottom:1px solid #1a2a1a}}
        </style></head><body>
        <table>
          <thead><tr>
            <th>SCENARIO</th><th>MONTHLY RENT</th>
            <th>RATING</th><th>MONTHLY PROFIT</th>
            <th>PAYBACK</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></body></html>"""

        components.html(sensitivity_html, height=240)

        # Store ROI in result for PDF
        result["roi"] = roi

    else:
        st.info(
            "Enter monthly rent above to see ROI analysis, "
            "profit estimates, and payback period."
        )

    # ── Address trend ─────────────────────────────────────
    render_address_trend(result["address"])

    # PDF
    st.markdown("---")
    with st.spinner("Preparing PDF report..."):
        import tempfile
        safe_name = "".join(
            c for c in result["address"][:20]
            if c.isalnum() or c in (" ", "-", "_")
        ).strip().replace(" ", "_")
        path = os.path.join(tempfile.gettempdir(),
                            f"{safe_name}_report.pdf")
        generate_report(result, path)
        with open(path, "rb") as f:
            pdf_bytes = f.read()
    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="SiteIQ_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption("SiteScore Analytics · Gujarat · " "OpenStreetMap + Google Places API")
