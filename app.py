import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from scorer import score_site

st.set_page_config(
    page_title="SiteScore — Retail Site Intelligence",
    page_icon="📍",
    layout="wide"
)

st.markdown("""
<style>
  .score-box {
    background: #0A2E26; border-radius: 12px;
    padding: 28px; text-align: center; color: white;
  }
  .metric-card {
    background: white; border-radius: 10px;
    padding: 16px; border: 1px solid #EEEEEE;
    text-align: center; margin-bottom: 10px;
  }
  .metric-val { font-size: 28px; font-weight: 700; }
  .metric-lbl { font-size: 11px; color: #888; margin-top: 2px; }
  .risk-box {
    background: #FFF8F0; border-left: 4px solid #BA7517;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    font-size: 13px; color: #555; margin-bottom: 8px;
  }
  .ok-box {
    background: #F0FAF6; border-left: 4px solid #1D9E75;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    font-size: 13px; color: #0A6E50; margin-bottom: 8px;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────
st.markdown("""
<div style='background:#0A2E26;padding:20px 28px;border-radius:10px;margin-bottom:24px'>
  <div style='color:#9ecfc0;font-size:11px;letter-spacing:2px'>RETAIL SITE INTELLIGENCE</div>
  <div style='color:white;font-size:24px;font-weight:700;margin-top:4px'>SiteScore</div>
  <div style='color:#9ecfc0;font-size:13px;margin-top:2px'>Score any retail location in Gujarat — instantly</div>
</div>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "loading" not in st.session_state:
    st.session_state.loading = False

# ── Input ─────────────────────────────────────────────────
col_input, col_type = st.columns([3, 1])
with col_input:
    address = st.text_input(
        "Address",
        placeholder="e.g. CG Road, Ahmedabad, Gujarat",
        label_visibility="collapsed",
        key="address_input"
    )
with col_type:
    brand_type = st.selectbox(
        "Type",
        ["restaurant", "pharmacy", "supermarket", "bank", "school"],
        label_visibility="collapsed",
        key="brand_type_input"
    )

if st.button("Score This Site", type="primary", use_container_width=True):
    if address.strip():
        with st.spinner("Analysing location — this takes 20–30 seconds..."):
            result = score_site(address.strip(), brand_type)
        if result:
            st.session_state.result = result
        else:
            st.error("Could not geocode that address. Try adding 'Ahmedabad, Gujarat'.")

# ── Display results from session state ───────────────────
if st.session_state.result:
    result  = st.session_state.result
    scores  = result["scores"]
    total   = result["total_score"]
    verdict = result["verdict"]
    lat, lng = result["lat"], result["lng"]

    verdict_color = "#1D9E75" if verdict == "Strong" else \
                    "#BA7517" if verdict == "Moderate" else "#C0392B"

    st.markdown("---")

    # ── Score box + radar ─────────────────────────────────
    col_score, col_radar = st.columns([1, 2])

    with col_score:
        st.markdown(f"""
        <div class='score-box'>
          <div style='font-size:72px;font-weight:700;color:{verdict_color};line-height:1'>
            {total}
          </div>
          <div style='font-size:13px;color:#9ecfc0;margin-top:4px'>out of 100</div>
          <hr style='border-color:#1a4a3a;margin:14px 0'>
          <div style='color:{verdict_color};font-size:18px;font-weight:700'>
            {verdict.upper()} SITE
          </div>
          <div style='color:#9ecfc0;font-size:11px;margin-top:8px'>
            {result["address"][:55]}
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        for label, key in [
            ("Demand",        "demand"),
            ("Footfall",      "footfall"),
            ("Competition",   "competition"),
            ("Accessibility", "accessibility"),
            ("Catchment",     "catchment"),
        ]:
            s = scores[key]
            col = "#1D9E75" if s >= 65 else "#BA7517" if s >= 45 else "#C0392B"
            st.markdown(f"""
            <div class='metric-card'>
              <div class='metric-val' style='color:{col}'>{s}</div>
              <div class='metric-lbl'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_radar:
        categories = ["Demand","Footfall","Competition","Accessibility","Catchment"]
        values     = [scores["demand"], scores["footfall"], scores["competition"],
                      scores["accessibility"], scores["catchment"]]

        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(29,158,117,0.15)",
            line=dict(color="#1D9E75", width=2),
            marker=dict(color="#1D9E75", size=7),
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="#F0FAF6",
                radialaxis=dict(visible=True, range=[0,100],
                                tickfont=dict(size=9), gridcolor="#DDDDDD"),
                angularaxis=dict(tickfont=dict(size=12, color="#333"))
            ),
            showlegend=False,
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Map ───────────────────────────────────────────────
    st.markdown("### Location Map")
    m = folium.Map(location=[lat, lng], zoom_start=15,
                   tiles="CartoDB positron")

    folium.CircleMarker(
        location=[lat, lng], radius=14,
        color="#0A2E26", fill=True,
        fill_color=verdict_color, fill_opacity=0.9,
        popup=folium.Popup(
            f"<b>{result['address']}</b><br>Score: {total}/100",
            max_width=220)
    ).add_to(m)

    folium.Circle(
        location=[lat, lng], radius=500,
        color="#1D9E75", fill=True,
        fill_color="#1D9E75", fill_opacity=0.05,
        dash_array="6", weight=1.5,
        tooltip="500m radius"
    ).add_to(m)

    folium.Circle(
        location=[lat, lng], radius=1000,
        color="#BA7517", fill=False,
        dash_array="4", weight=1,
        tooltip="1km radius"
    ).add_to(m)

    st_folium(m, width="100%", height=420, returned_objects=[])

    # ── Risk flags ────────────────────────────────────────
    st.markdown("### Risk Assessment")
    risks = []
    if scores["competition"]   < 30: risks.append("High competitor density within 500m — market may be saturated")
    if scores["demand"]        < 40: risks.append("Low residential population density — walk-in customer base limited")
    if scores["footfall"]      < 40: risks.append("Few anchor stores nearby — footfall dependent on destination visits")
    if scores["accessibility"] < 40: risks.append("Limited road connectivity — may reduce customer convenience")

    if risks:
        for r in risks:
            st.markdown(f"<div class='risk-box'>! {r}</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='ok-box'>No significant risk flags at this location</div>",
            unsafe_allow_html=True)

    st.markdown("---")
    st.caption("SiteScore Analytics · Ahmedabad, Gujarat · Data: OpenStreetMap + Google Places API")