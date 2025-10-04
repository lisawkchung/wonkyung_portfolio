import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ------------------------------------------------------------------------------
# Load data from API
# ------------------------------------------------------------------------------
resource_id = "bd41992a-987a-4cca-8798-fbe1cd946b07"
url = "https://data.wprdc.org/api/action/datastore_search"

all_records = []
offset = 0
limit = 1000

while True:
    params = {"resource_id": resource_id, "limit": limit, "offset": offset}
    r = requests.get(url, params=params).json()
    records = r["result"]["records"]
    if not records:
        break
    all_records.extend(records)
    offset += limit

df_crime = pd.DataFrame(all_records)

# Clean columns
df_crime['ReportedDateTime'] = pd.to_datetime(
    df_crime['ReportedDate'].astype(str) + " " + df_crime['ReportedTime'].astype(str),
    errors='coerce'
)
df_crime['Year'] = df_crime['ReportedDateTime'].dt.year
df_crime['XCOORD'] = pd.to_numeric(df_crime['XCOORD'], errors='coerce')
df_crime['YCOORD'] = pd.to_numeric(df_crime['YCOORD'], errors='coerce')

# ------------------------------------------------------------------------------
# Map crimes to student-relevant categories
# ------------------------------------------------------------------------------
mapping = {
    "09A MURDER & NON-NEGLIGENT MANSLAUGHTER": "High Threat Crimes",
    "09B MANSLAUGHTER BY NEGLIGENCE": "High Threat Crimes",
    "11A FORCIBLE RAPE": "High Threat Crimes",
    "11B FORCIBLE SODOMY": "High Threat Crimes",
    "11C SEXUAL ASSAULT WITH AN OBJECT": "High Threat Crimes",
    "11D FORCIBLE FONDLING": "High Threat Crimes",
    "36A INCEST": "High Threat Crimes",
    "36B STATUTORY RAPE": "High Threat Crimes",
    "64A COMMERCIAL SEX ACTS": "High Threat Crimes",
    "64B INVOLUNTARY SERVITUDE": "High Threat Crimes",
    "100 KIDNAPPING/ABDUCTION": "High Threat Crimes",
    "120 ROBBERY": "High Threat Crimes",
    "520 WEAPON LAW VIOLATIONS": "High Threat Crimes",
    "13A AGGRAVATED ASSAULT": "Everyday Risks",
    "13B SIMPLE ASSAULT": "Everyday Risks",
    "13C INTIMIDATION": "Everyday Risks",
    "23A POCKET PICKING": "Everyday Risks",
    "23B PURSE SNATCHING": "Everyday Risks",
    "90C DISORDERLY CONDUCT": "Everyday Risks",
    "90E DRUNKENNESS": "Everyday Risks",
    "240 MOTOR VEHICLE THEFT": "Auto & Parking Risks",
    "23G THEFT OF MOTOR VEHICLE PARTS OR ACCESSORIES": "Auto & Parking Risks",
    "23F THEFT FROM MOTOR VEHICLE": "Auto & Parking Risks",
}
df_crime["Risk_Category"] = df_crime["NIBRS_Coded_Offense"].map(mapping).fillna("Other")

# ------------------------------------------------------------------------------
# Filter for CMU neighborhoods and night time
# ------------------------------------------------------------------------------
neighborhoods = [
    "Central Oakland", "East Liberty", "North Oakland", "Oakland",
    "Shadyside", "Squirrel Hill North", "Squirrel Hill South"
]

df_filtered = df_crime[
    (df_crime["Neighborhood"].isin(neighborhoods)) &
    ((df_crime["Hour"].between(17,23)) | (df_crime["Hour"].between(0,2)))
].copy()

df_filtered["Hour_fixed"] = df_filtered["Hour"].apply(lambda x: x+24 if x in [0,1,2] else x)
custom_order = list(range(17,27))
df_filtered = df_filtered.sort_values("Hour_fixed")
df_filtered["Hour_fixed"] = pd.Categorical(df_filtered["Hour_fixed"], categories=custom_order, ordered=True)

# ------------------------------------------------------------------------------
# Create scatter map (student risks per hour)
# ------------------------------------------------------------------------------
fig_scatter = px.scatter_mapbox(
    df_filtered,
    lat="YCOORD", lon="XCOORD",
    color="Risk_Category",
    hover_name="NIBRS_Offense_Type",
    hover_data={
        "Neighborhood": True,
        "ReportedDate": True,
        "ReportedTime": True,
        "YCOORD": False,
        "XCOORD": False
    },
    animation_frame="Hour_fixed",
    category_orders={"Hour_fixed": custom_order},
    zoom=13,
    height=600,
    width=900,
    title="Student Risk by Hour in CMU Neighborhoods"
)

fig_scatter.update_layout(
    mapbox_style="carto-positron",
    mapbox_center={"lat": 40.4477, "lon": -79.9370},
    legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center", yanchor="bottom")
)

# ------------------------------------------------------------------------------
# Create choropleth map (crime density by neighborhood)
# ------------------------------------------------------------------------------
url_geojson = "https://data.wprdc.org/dataset/e672f13d-71c4-4a66-8f38-710e75ed80a4/resource/4af8e160-57e9-4ebf-a501-76ca1b42fc99/download/pittsburghpaneighborhoods-.geojson"
geojson_data = requests.get(url_geojson).json()

df_high_threat = df_crime[
    (df_crime["Risk_Category"] == "High Threat Crimes")
]

df_counts = df_high_threat.groupby("Neighborhood").size().reset_index(name="crime_count")

fig_choro = px.choropleth_mapbox(
    df_counts,
    geojson=geojson_data,
    locations="Neighborhood",
    featureidkey="properties.hood",
    color="crime_count",
    color_continuous_scale="Reds",
    mapbox_style="carto-positron",
    center={"lat": 40.44, "lon": -79.95},
    zoom=12,
    opacity=0.8,
    title="High-Threat Crime Density by Neighborhood"
)

# ------------------------------------------------------------------------------
# Streamlit App Layout
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Wonkyung Portfolio", layout="wide")

# Intro Section
st.title("Lisa Chung")
st.subheader("Future Data Scientist & Leader")

st.markdown("""
Welcome! This is a collection of my projects in data analysis, visualization, and machine learning as a master's student at CMU.
""")

# Projects Section
st.header("📊 Projects")
st.markdown("- **Pittsburgh Crime Dashboard**: Interactive analysis of crime risks around CMU neighborhoods")
st.plotly_chart(fig_scatter, use_container_width=True)
st.plotly_chart(fig_choro, use_container_width=True)

st.markdown("- (More projects coming soon!)")

# Contact Section
st.header("📬 Contact")
st.markdown("""
Feel free to reach out via  
- [GitHub](https://https://github.com/lisawkchung)  
- [LinkedIn](https://www.linkedin.com/in/lisawonkyungchung/)  
- [Email](mailto:lisa.wk.chung@gmail.com)  
""")
