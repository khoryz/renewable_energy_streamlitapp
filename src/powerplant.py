
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from copy import deepcopy

# Wide-mode display for the app
st.set_page_config(layout="wide")

# Colors used in this project
colors = px.colors.sequential.PuBu  # sequential
colors2 = px.colors.sequential.Purples  # sequential
colors3 = px.colors.qualitative.Bold  # discrete

# Create cache for data loading (save time)
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

df_raw = load_data(path="./data/raw/renewable_power_plants_CH.csv")
df = deepcopy(df_raw)

with open(
    "./data/raw/georef-switzerland-kanton.geojson"
) as json_file:
    geojson = json.load(json_file)

cantons_dict = {
    "TG": "Thurgau",
    "GR": "Graubünden",
    "LU": "Luzern",
    "BE": "Bern",
    "VS": "Valais",
    "BL": "Basel-Landschaft",
    "SO": "Solothurn",
    "VD": "Vaud",
    "SH": "Schaffhausen",
    "ZH": "Zürich",
    "AG": "Aargau",
    "UR": "Uri",
    "NE": "Neuchâtel",
    "TI": "Ticino",
    "SG": "St. Gallen",
    "GE": "Genève",
    "GL": "Glarus",
    "JU": "Jura",
    "ZG": "Zug",
    "OW": "Obwalden",
    "FR": "Fribourg",
    "SZ": "Schwyz",
    "AR": "Appenzell Ausserrhoden",
    "AI": "Appenzell Innerrhoden",
    "NW": "Nidwalden",
    "BS": "Basel-Stadt",
}

# Map full name to abbreviation so that it can be matched with the geojson file
df["kan_name"] = df["canton"].map(cantons_dict)

# Group by canton
df_sum = (
    df.groupby("kan_name")
    .agg(
        cap_sum=("electrical_capacity", "sum"),
        tariff_sum=("tariff", "sum"),
        plant_count=("company", "count"),
        prod_sum=("production", "sum"),
    )
    .reset_index()
)

# Group by energy source
df_ener = (
    df.groupby("energy_source_level_2")
    .agg(
        cap_sum=("electrical_capacity", "sum"),
        cap_mean=("electrical_capacity", "mean"),
        plant_count=("company", "count"),
    )
    .reset_index()
)

# Group by energ source and canton
df_capsum = (
    df.groupby(["energy_source_level_2", "kan_name"])
    .agg(
        cap_sum=("electrical_capacity", "sum"),
    )
    .reset_index()
)

# Add title and checkbox for data source
st.title("Renewable Energy in Switzerland")
if st.checkbox("Show Data Source"):
    url = "https://open-power-system-data.org/"
    st.write("Open Power System Data, ", url)

# Add header
st.header("Distribution of Renewable Power Plants")
################### Choices ###################
# Radio button for Figure 1 and 2
map_types = ["Annual production by renewable power plants", "Number of renewable power plants"]
map_type = st.radio("Choose the canton-level data to be displayed on the country map:", map_types)



################### Figure 1 or 2 ###################
# Map 1 on production
fig1_prod_map = px.choropleth_mapbox(
    df_sum,
    geojson=geojson,
    color="prod_sum",
    locations="kan_name",
    featureidkey="properties.kan_name",
    color_continuous_scale="PuBu",
    center={"lat": 46.8, "lon": 8.3},
    labels={"prod_sum": "Production (MWh)"},
    hover_name=df_sum["kan_name"],
    hover_data={"kan_name": False, "prod_sum": ":,.2f"},
    mapbox_style="carto-positron",
    zoom=7,
    width=1200,
    height=800,
)
fig1_prod_map.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

# Map 2 on the number of plants
fig2_num_map = px.choropleth_mapbox(
    df_sum,
    geojson=geojson,
    color="plant_count",
    locations="kan_name",
    featureidkey="properties.kan_name",
    color_continuous_scale="PuBu",
    center={"lat": 46.8, "lon": 8.3},
    labels={"plant_count": "Number of Plants"},
    hover_name=df_sum["kan_name"],
    hover_data={"kan_name": False},
    mapbox_style="carto-positron",
    zoom=7,
    width=1200,
    height=800,
)
fig2_num_map.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

# Select which map to show
if map_type == "Annual production by renewable power plants":
    st.plotly_chart(fig1_prod_map)
else:
    st.plotly_chart(fig2_num_map)



################### More choices ###################
st.header("Total Capacity by Energy Source and Canton")

left_col, right_col = st.columns([2, 8])

# Select box for Figure 3
sources = df_ener.sort_values(by="cap_sum", ascending=False)["energy_source_level_2"]
source = left_col.selectbox("Choose an energy source:", sources)



################### Figure 3 ###################
colors3 = [
    px.colors.qualitative.Bold[x] for x in [6, 2, 5, 0]
]  # rearrange the colors chosen

ener_list=[]
for i, en in enumerate(sources):
    ener_list.append((i, en))

fig_ener = go.Figure()
for j in range(4):
    if ener_list[j][1] == source:
        df_aux = df_capsum[df_capsum["energy_source_level_2"] == source].sort_values(
            by="cap_sum", ascending=False)
        fig_ener.add_trace(
            go.Bar(
                x=df_aux["kan_name"], y=df_aux["cap_sum"], name=source, marker_color=colors3[j]
            )
        )
        fig_ener.update_layout(
            width=1200,
            height=800,
            margin=dict(l=75, r=75, b=75, t=75),
            xaxis={"title": {"text": "Swiss Canton", "font": {"size": 18}}},
            yaxis={"title": {"text": "Total Capacity (MW)", "font": {"size": 18}}},
            paper_bgcolor=colors2[1],
            plot_bgcolor=colors2[0],
        )
        st.plotly_chart(fig_ener)



################### Even more choices ###################
st.header("More Information")

left_col2, _, mid_col2, right_col2 = st.columns([4, 2, 2, 4])
mid_col2.text("")

# Select box for Figure 4 and/or 5
others = ["All", "Feed-in Tariff and Production", "Total Capacity and Number of Plants by Energy Source"]
other = left_col2.selectbox("Choose more information to view:", others)

# Add checkbox for marker type (but not if the third choice is selected)
if other == others[2]:
    mark_dict = {
        "color": colors[-2],
        "size": 15,
    }
elif mid_col2.checkbox("Make marker size proportionate to the number of power plants"):
    mark_dict = {
        "color": colors[-2],
        "size": df_sum["plant_count"],
        "sizemode": "area",
        "sizeref": 2 * max(df_sum["plant_count"] / 15000),
    }
else:
    mark_dict = {
        "color": colors[-2],
        "size": 15,
    }



################### Figure 4 ###################
fig_tar = go.Figure()

fig_tar.add_trace(
    go.Scatter(
        y=df_sum["tariff_sum"],
        x=df_sum["prod_sum"],
        mode="markers",
        marker=mark_dict,
        name="tariff",
        text=df_sum["kan_name"],
        hovertemplate="<b>%{text}</b><br><br>"
        + "Feed-in Tariff: %{y:,.2f} CHF<br>"
        + "Production: %{x:,.2f} MWh<br>"
        + "Number of Plants: %{marker.size}<br>"
        + "<extra></extra>",
        showlegend=False,
    )
)
fig_tar.update_layout(
    width=1200,
    height=800,
    margin=dict(l=75, r=75, b=75, t=75),
    title={"text": "Feed-in Tariff and Production", "font": {"size": 24}},
    xaxis={"title": {"text": "Annual Production (MWh)", "font": {"size": 18}}},
    yaxis={"title": {"text": "Feed-in Tariff of 2018 (CHF)", "font": {"size": 18}}},
    paper_bgcolor=colors2[1],
    plot_bgcolor=colors2[0],
)
fig_tar.update_yaxes(type="log")



################### Figure 5 ###################
colors3 = [
    px.colors.qualitative.Bold[x] for x in [5, 2, 6, 0]
]  # rearrange the colors chosen

fig_pie = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=(
        "Total Capacity by Energy Source",
        "Total Number of Plants by Energy Source",
    ),
    specs=[[{"type": "pie"}, {"type": "pie"}]],
)

fig_pie.add_trace(
    go.Pie(
        labels=df_ener["energy_source_level_2"],
        values=df_ener["cap_sum"],
        rotation=180,
        marker_colors=colors3,
    ),
    row=1,
    col=1,
)
fig_pie.add_trace(
    go.Pie(
        labels=df_ener["energy_source_level_2"],
        values=df_ener["plant_count"],
        rotation=180,
        marker_colors=colors3,
    ),
    row=1,
    col=2,
)
fig_pie.update_layout(
    width=1200,
    height=700,
    margin=dict(l=75, r=75, b=75, t=75),
    uniformtext_minsize=20,
    uniformtext_mode="hide",
    paper_bgcolor=colors2[1],
)
fig_pie.update_annotations(
    font_size=24
)

# Select which plot to show
if other == "All":
    st.plotly_chart(fig_tar)
    st.plotly_chart(fig_pie)
elif other == "Feed-in Tariff and Production":
    st.plotly_chart(fig_tar)
else:
    st.plotly_chart(fig_pie)
