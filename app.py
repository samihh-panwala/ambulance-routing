# app.py - Streamlit app v3 (Surat fixed): 1 incident, 3 ambulances, 5 hospitals
import streamlit as st
from routing import load_graph, nearest_node, nodes_to_latlon, load_hospitals_with_fallback
from algorithm import select_ambulance_and_hospital
import folium
from streamlit_folium import st_folium
import random

st.set_page_config(layout="wide", page_title="Emergency Ambulance Dispatch - Surat (v3)")
st.title("Emergency Ambulance Dispatch - Surat (v3)")
st.markdown("Fixed scenario: 1 incident in Surat, 3 ambulances at random locations, 5 hospitals (real or fallback). Assignment: choose ambulance with min ETA then send victim to nearest hospital.")

PLACE = "Surat, India"

# initialize once
if "initialized" not in st.session_state:
    st.session_state["G"] = load_graph(PLACE)
    G = st.session_state["G"]
    nodes = list(G.nodes)
    random_nodes = random.sample(nodes, 3)
    ambulances = [{"id": f"A{i+1}", "node": random_nodes[i], "status": "available"} for i in range(3)]
    st.session_state["ambulances"] = ambulances
    xs = [G.nodes[n]['x'] for n in G.nodes]
    ys = [G.nodes[n]['y'] for n in G.nodes]
    center_lon = sum(xs)/len(xs)
    center_lat = sum(ys)/len(ys)
    inc_lon = center_lon + 0.002
    inc_lat = center_lat - 0.0015
    st.session_state["incident"] = {"id":"I1","lon":inc_lon,"lat":inc_lat,"status":"unassigned"}
    st.session_state["hospitals"] = load_hospitals_with_fallback(PLACE, G, min_count=5)
    st.session_state["initialized"] = True

# run selection
if "assigned" not in st.session_state:
    G = st.session_state["G"]
    best_amb, best_hosp, route_to_inc, route_inc_hosp, t_amb, t_hosp = select_ambulance_and_hospital(G, st.session_state["ambulances"], st.session_state["incident"], st.session_state["hospitals"])
    if best_amb is not None:
        best_amb["status"] = "dispatched"
        best_amb["route_to_inc"] = route_to_inc
        best_amb["route_to_hosp"] = route_inc_hosp
        best_amb["eta_to_inc_s"] = t_amb
        best_amb["hospital_name"] = best_hosp.get("name","Hospital") if best_hosp is not None else "Hospital"
        st.session_state["incident"]["status"] = "assigned"
        st.session_state["incident"]["assigned_to"] = best_amb["id"]
        st.session_state["assigned"] = True
        st.success(f"Ambulance {best_amb['id']} assigned (ETA {int(t_amb)}s) -> hospital {best_amb['hospital_name']} (ETA from incident {int(t_hosp)}s)")
    else:
        st.error("Assignment failed (unexpected)")

# Map
col1, col2 = st.columns([3,1])
with col1:
    G = st.session_state["G"]
    xs = [G.nodes[n]['x'] for n in G.nodes]
    ys = [G.nodes[n]['y'] for n in G.nodes]
    mean_lat = sum(ys)/len(ys)
    mean_lon = sum(xs)/len(xs)
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)

    for idx, row in st.session_state["hospitals"].iterrows():
        folium.Marker([row.geometry.y, row.geometry.x], popup=str(row.get("name","Hospital")), icon=folium.Icon(color="green", icon="plus")).add_to(m)

    for amb in st.session_state["ambulances"]:
        n = amb["node"]
        folium.CircleMarker([G.nodes[n]["y"], G.nodes[n]["x"]], radius=8, popup=f'{amb["id"]} ({amb["status"]})', color="blue" if amb.get("status")=="available" else "red").add_to(m)
        if amb.get("status")=="dispatched" and "route_to_inc" in amb and amb["route_to_inc"] is not None:
            coords = nodes_to_latlon(G, amb["route_to_inc"])
            folium.PolyLine(coords, weight=5, color="red").add_to(m)
        if amb.get("status")=="dispatched" and "route_to_hosp" in amb and amb["route_to_hosp"] is not None:
            coords = nodes_to_latlon(G, amb["route_to_hosp"])
            folium.PolyLine(coords, weight=4, color="green", dash_array="5").add_to(m)

    inc = st.session_state["incident"]
    folium.Marker([inc["lat"], inc["lon"]], popup=f'{inc["id"]} ({inc["status"]})', icon=folium.Icon(color="orange", icon="info-sign")).add_to(m)

    st_folium(m, width=900, height=700)

with col2:
    st.header("Details")
    inc = st.session_state["incident"]
    st.markdown("**Incident**")
    st.write(f'ID: {inc["id"]}')
    st.write(f'Location (lon,lat): ({inc["lon"]:.6f}, {inc["lat"]:.6f})')
    st.markdown("**Ambulances**")
    for amb in st.session_state["ambulances"]:
        st.write(f'{amb["id"]}: status={amb["status"]}, node={amb["node"]}')
        if amb.get("status")=="dispatched":
            st.write(f'  assigned hospital: {amb.get("hospital_name","-")}, ETA to incident: {int(amb.get("eta_to_inc_s",0))}s')
    st.markdown("**Hospitals (5 selected)**")
    for idx, row in st.session_state["hospitals"].iterrows():
        st.write(f'{idx+1}. {row.get("name","Hospital")} — ({row.geometry.x:.6f}, {row.geometry.y:.6f})')

st.markdown("---")
st.markdown("**Algorithm choice**: Greedy algorithm — select ambulance with smallest ETA (argmin). This is suitable for single-incident, real-time dispatch.")
