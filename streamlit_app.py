from __future__ import annotations

import io
import random
from datetime import datetime

import pandas as pd
import pydeck as pdk
import streamlit as st

from routeiq.engine import NODES, plan_fleet, shortest_path

st.set_page_config(page_title="RouteIQ | Intelligent Logistics", page_icon="🚚", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:#f5f7fb;color:#1c2941}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e7ebf2}
.brand{font:800 26px Manrope;letter-spacing:-1.3px;color:#1c2941;margin:4px 0 20px}
.brand span{color:#6759e8}
.hero{background:linear-gradient(112deg,#19213c,#30336c);border-radius:16px;padding:26px 30px;color:#fff;margin:7px 0 17px}
.hero .eyebrow{color:#c2bcff;font-size:9px;font-weight:800;letter-spacing:1.7px;margin-bottom:11px}
.hero h1{font:800 32px Manrope;letter-spacing:-1.6px;color:white;margin:0 0 7px}
.hero p{font-size:12px;line-height:1.65;color:#d0d1e5;max-width:720px;margin:0}
.section-title{font:800 19px Manrope;letter-spacing:-.4px;color:#202c44;margin:10px 0 3px}
.section-sub{font-size:10px;color:#8c97a9;margin-bottom:13px}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e7ebf2;border-radius:11px;padding:13px 15px;box-shadow:0 3px 14px #15213a08}
div[data-testid="stMetricLabel"]{font-size:10px;color:#8792a5}
div[data-testid="stMetricValue"]{font:800 23px Manrope;color:#202c44}
.route-card{background:#fff;border:1px solid #e7ebf2;border-radius:11px;padding:13px 15px;margin:0 0 9px}
.route-card strong{font-size:12px;color:#24314a}
.muted{font-size:10px;color:#8e99ab}
.pill-good{color:#279672;background:#e9f8f1;padding:4px 7px;border-radius:18px;font-size:9px;font-weight:700}
.pill-warn{color:#b77c30;background:#fff5e8;padding:4px 7px;border-radius:18px;font-size:9px;font-weight:700}
.insight{background:#efedff;border:1px solid #e5e1ff;border-radius:10px;padding:12px 15px;color:#5146bd;font-size:11px;line-height:1.6;margin:10px 0 15px}
.smallcaps{font-size:8px;letter-spacing:1.1px;color:#9ca5b3;font-weight:800}
.stButton>button{border-radius:8px;font-weight:600}
.stButton>button[kind="primary"]{background:#6759e8;border-color:#6759e8}
div[data-testid="stDataFrame"]{border:1px solid #e7ebf2;border-radius:10px;overflow:hidden}
.footer{font-size:9px;color:#9aa4b3;text-align:center;padding:20px 0 6px}
hr{border-color:#e8ecf2}
</style>
""", unsafe_allow_html=True)

def demo_orders():
    return [
        {"id":"ORD-1042","customer":"Northstar Labs","destination":"anna_nagar","load":2,"priority":5,"deadline":"10:30","status":"Ready"},
        {"id":"ORD-1043","customer":"Cedar & Co.","destination":"tnagar","load":1,"priority":4,"deadline":"11:00","status":"Ready"},
        {"id":"ORD-1044","customer":"Bluebird Health","destination":"adyar","load":2,"priority":5,"deadline":"10:45","status":"Ready"},
        {"id":"ORD-1045","customer":"Urban Market","destination":"velachery","load":1,"priority":3,"deadline":"12:00","status":"Ready"},
        {"id":"ORD-1046","customer":"Meridian Office","destination":"porur","load":2,"priority":2,"deadline":"13:00","status":"Ready"},
        {"id":"ORD-1047","customer":"Green Basket","destination":"tambaram","load":1,"priority":3,"deadline":"12:15","status":"Ready"},
        {"id":"ORD-1048","customer":"Harbour Books","destination":"perungudi","load":1,"priority":2,"deadline":"14:00","status":"Ready"},
    ]

def demo_vehicles():
    return [
        {"id":"VAN-01","driver":"Maya Nair","capacity":5,"type":"Electric van"},
        {"id":"VAN-02","driver":"Arun Kumar","capacity":4,"type":"Cargo van"},
        {"id":"BIKE-03","driver":"Ravi Das","capacity":2,"type":"Cargo bike"},
    ]

if "orders" not in st.session_state:
    st.session_state.orders = demo_orders()
if "vehicles" not in st.session_state:
    st.session_state.vehicles = demo_vehicles()
if "plans" not in st.session_state:
    st.session_state.plans = []
if "traffic" not in st.session_state:
    st.session_state.traffic = 1.2

with st.sidebar:
    st.markdown('<div class="brand">route<span>iq</span></div>',unsafe_allow_html=True)
    st.caption("LOGISTICS CONTROL TOWER · DEMO")
    page=st.radio("WORKSPACE",["Overview","Orders & dispatch","Network explorer"])
    st.divider()
    st.markdown("**DISPATCH SETTINGS**")
    traffic=st.slider("Traffic multiplier",1.0,2.5,st.session_state.traffic,0.1,help="Illustrative multiplier applied to estimated journey time.")
    speed=st.slider("Average vehicle speed (km/h)",10,60,28)
    st.session_state.traffic=traffic
    st.divider()
    if st.button("↻ Reset demo scenario",use_container_width=True):
        st.session_state.orders=demo_orders()
        st.session_state.vehicles=demo_vehicles()
        st.session_state.plans=[]
        st.rerun()
    st.caption("Demo road graph · Not live traffic or navigation")

orders=st.session_state.orders
vehicles=st.session_state.vehicles
ready_orders=[order for order in orders if order["status"]=="Ready"]

try:
    plans=plan_fleet(ready_orders,vehicles,traffic_factor=traffic,average_speed_kmh=speed)
    planning_error=None
except ValueError as exc:
    plans=[]
    planning_error=str(exc)

st.markdown('<div class="hero"><div class="eyebrow">PLAN · DISPATCH · DELIVER</div><h1>Every delivery, on a smarter route.</h1><p>Coordinate orders and drivers, compare shortest paths and understand the impact of traffic and vehicle capacity. Explore the routing decisions behind a modern logistics operation.</p></div>',unsafe_allow_html=True)

if page in ("Overview","Orders & dispatch"):
    total_distance=sum(item["distance_km"] for item in plans)
    total_eta=sum(item["estimated_minutes"] for item in plans)
    total_capacity=sum(v["capacity"] for v in vehicles)
    assigned_count=sum(len(p["order_ids"]) for p in plans)
    utilization=(sum(p["used_capacity"] for p in plans)/total_capacity*100) if total_capacity else 0
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Ready orders",len(ready_orders),"Awaiting dispatch")
    m2.metric("Planned distance",f"{total_distance:.1f} km","Depot round trips")
    m3.metric("Estimated drive time",f"{total_eta:.0f} min",f"Traffic ×{traffic:.1f}")
    m4.metric("Fleet capacity used",f"{utilization:.0f}%",f"{len(plans)} vehicles assigned")

    if planning_error:
        st.error("Dispatch planner: "+planning_error)
    else:
        st.markdown(f'<div class="insight"><b>✳ Dispatch insight</b><br/>The current plan assigns <b>{assigned_count} orders</b> across <b>{len(plans)} vehicles</b>. The greedy dispatcher considers priority, deadline, shortest incremental route and remaining carrying capacity.</div>',unsafe_allow_html=True)

    left,right=st.columns([1.55,1])
    with left:
        st.markdown('<div class="section-title">Fleet route map</div><div class="section-sub">Illustrative Chennai-inspired coordinates and road edges. Lines show the planned graph path, not turn-by-turn street geometry.</div>',unsafe_allow_html=True)
        map_points=[]
        for key,node in NODES.items():
            map_points.append({"name":node["name"],"position":[node["lon"],node["lat"],0],"kind":"Depot" if key=="depot" else "Location"})
        paths=[]
        palettes=[[104,89,232],[43,145,121],[225,146,79]]
        for index,plan in enumerate(plans):
            coords=[[NODES[node]["lon"],NODES[node]["lat"]] for node in plan["route_nodes"]]
            paths.append({"vehicle":plan["vehicle_id"],"path":coords,"color":palettes[index%len(palettes)]})
        layers=[
            pdk.Layer("PathLayer",data=paths,get_path="path",get_color="color",width_scale=18,width_min_pixels=4,pickable=True),
            pdk.Layer("ScatterplotLayer",data=map_points,get_position="position",get_radius=150,get_fill_color=[63,83,128],get_line_color=[255,255,255],line_width_min_pixels=1,pickable=True),
            pdk.Layer("TextLayer",data=map_points,get_position="position",get_text="name",get_size=11,get_color=[45,55,80],get_pixel_offset=[0,14],get_alignment_baseline="'top'",pickable=False),
        ]
        view=pdk.ViewState(latitude=13.035,longitude=80.215,zoom=9.7,pitch=25,bearing=0)
        st.pydeck_chart(pdk.Deck(layers=layers,initial_view_state=view,tooltip={"text":"{name}"} if not paths else {"text":"{vehicle}"}),use_container_width=True,height=410)
        st.caption("Map positions are illustrative. Use a licensed routing provider and current road network before operational use.")

    with right:
        st.markdown('<div class="section-title">Vehicle assignments</div>',unsafe_allow_html=True)
        if not plans:
            st.info("No routes to display. Add orders and vehicles to create a plan.")
        for plan in plans:
            with st.container(border=True):
                st.markdown(f"**{plan['vehicle_id']} · {plan['driver']}**")
                st.caption(f"{len(plan['order_ids'])} orders · {plan['used_capacity']}/{plan['capacity']} capacity")
                st.progress(plan["used_capacity"]/plan["capacity"],text=f"Capacity utilisation {plan['used_capacity']/plan['capacity']*100:.0f}%")
                a,b=st.columns(2)
                a.metric("Distance",f"{plan['distance_km']:.1f} km")
                b.metric("ETA",f"{plan['estimated_minutes']:.0f} min")
                st.caption(" → ".join(NODES[node]["name"] for node in plan["stops"]))
        st.markdown('<div class="section-title">Fleet composition</div>',unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"Vehicle":v["id"],"Driver":v["driver"],"Type":v.get("type","Vehicle"),"Capacity":v["capacity"]} for v in vehicles]),use_container_width=True,hide_index=True)

    if page=="Orders & dispatch":
        st.markdown('<div class="section-title">Delivery orders</div>',unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([{"Order":o["id"],"Customer":o["customer"],"Destination":NODES[o["destination"]]["name"],"Load":o["load"],"Priority":o["priority"],"Deadline":o["deadline"],"Status":o["status"]} for o in orders]),use_container_width=True,hide_index=True)
        with st.expander("＋ Add delivery order"):
            with st.form("add_order",clear_on_submit=True):
                a,b=st.columns(2)
                order_id=a.text_input("Order ID",placeholder="ORD-1050")
                customer=b.text_input("Customer",placeholder="Customer name")
                destination=st.selectbox("Destination",[(key,NODES[key]["name"]) for key in NODES if key!="depot"],format_func=lambda item:item[1])
                x,y,z=st.columns(3)
                load=x.number_input("Load units",1,10,1)
                priority=y.slider("Priority",1,5,3)
                deadline=z.text_input("Deadline",value="12:00")
                submitted=st.form_submit_button("Add to dispatch board",type="primary")
                if submitted:
                    if not order_id.strip() or not customer.strip():
                        st.error("Enter an order ID and customer.")
                    elif any(o["id"]==order_id.strip() for o in orders):
                        st.warning("Order ID already exists.")
                    else:
                        st.session_state.orders.append({"id":order_id.strip(),"customer":customer.strip(),"destination":destination[0],"load":int(load),"priority":priority,"deadline":deadline,"status":"Ready"})
                        st.success("Order added.")
                        st.rerun()
        if st.button("🚚 Recalculate dispatch plan",type="primary"):
            st.session_state.plans=plans
            st.success("Dispatch plan recalculated for the current scenario.")
        if plans:
            export=pd.DataFrame([{"Vehicle":p["vehicle_id"],"Driver":p["driver"],"Orders":", ".join(p["order_ids"]),"Stops":" → ".join(NODES[n]["name"] for n in p["stops"]),"Distance km":p["distance_km"],"Estimated minutes":p["estimated_minutes"]} for p in plans])
            st.download_button("⬇ Download dispatch plan CSV",export.to_csv(index=False),"routeiq-dispatch-plan.csv","text/csv")

elif page=="Network explorer":
    st.markdown('<div class="section-title">Shortest-path explorer</div><div class="section-sub">Choose two locations and inspect the Dijkstra route through the sample road graph.</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    options=list(NODES.keys())
    start=a.selectbox("Start location",options,index=0,format_func=lambda key:NODES[key]["name"])
    destination=b.selectbox("Destination",options,index=7,format_func=lambda key:NODES[key]["name"])
    if st.button("Find shortest route",type="primary"):
        result=shortest_path(start,destination)
        st.success(f"Shortest graph path: {result['distance_km']:.2f} km")
        names=[NODES[node]["name"] for node in result["path"]]
        st.markdown(" → ".join(f"**{name}**" for name in names))
        coordinates=[{"lat":NODES[node]["lat"],"lon":NODES[node]["lon"],"place":NODES[node]["name"]} for node in result["path"]]
        st.map(pd.DataFrame(coordinates),latitude="lat",longitude="lon",size=80,color="#6759e8")
        st.caption("Dijkstra finds the least-cost path on the configured graph. The graph is a demo abstraction and is not a live road network.")
    st.markdown('<div class="section-title">Road network nodes</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"Node":key,"Location":node["name"],"Latitude":node["lat"],"Longitude":node["lon"]} for key,node in NODES.items()]),use_container_width=True,hide_index=True)

st.divider()
st.markdown('<div class="smallcaps">DISPATCH API</div>',unsafe_allow_html=True)
st.caption("The FastAPI service exposes /health, /api/v1/locations, /api/v1/route and /api/v1/dispatch. See README for local API startup instructions.")
st.markdown('<div class="footer">RouteIQ · Independent portfolio demo · Illustrative road graph and traffic multiplier · Not live navigation or guaranteed ETAs.</div>',unsafe_allow_html=True)
