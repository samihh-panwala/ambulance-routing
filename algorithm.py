# algorithm.py - Greedy selection for single incident scenario
from routing import nearest_node, route_travel_time_seconds

def select_ambulance_and_hospital(G, ambulances, incident, hospitals_gdf):
    inc_node = nearest_node(G, incident["lon"], incident["lat"])
    best_amb = None
    best_time = float("inf")
    best_route_to_inc = None

    for amb in ambulances:
        try:
            t, route = route_travel_time_seconds(G, amb["node"], inc_node)
        except Exception:
            continue
        if t < best_time:
            best_time = t
            best_amb = amb
            best_route_to_inc = route

    best_hosp = None
    best_hosp_time = float("inf")
    best_route_inc_hosp = None
    for idx, row in hospitals_gdf.iterrows():
        try:
            hosp_node = nearest_node(G, row.geometry.x, row.geometry.y)
            t_h, route_h = route_travel_time_seconds(G, inc_node, hosp_node)
        except Exception:
            continue
        if t_h < best_hosp_time:
            best_hosp_time = t_h
            best_hosp = row
            best_route_inc_hosp = route_h

    return best_amb, best_hosp, best_route_to_inc, best_route_inc_hosp, best_time, best_hosp_time
