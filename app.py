import pandas as pd
import plotly.express as px
import warnings

warnings.filterwarnings("ignore")

df_MYE1 = pd.read_excel(
    "mye22final.xlsx",
    sheet_name="MYE1",
    header=6
)
# Data Cleaning
df_MYE1 = (
    df_MYE1
    .replace("No data", pd.NA)        # make “No data” into missing
    .dropna(how="all")                # drop fully empty rows
    .loc[lambda d: d["Groups/codes"] != "Age Groups"]  # remove that filler label row
)


print(df_MYE1.head())
from dash import Dash, html, dcc, Input, Output
import plotly.express as px

# ── Load & clean MYE1 ───────────────────────────────────────────────
df = (
    pd.read_excel("mye22final.xlsx", sheet_name="MYE1", header=6) 
      .replace("No data", pd.NA)
      .dropna(how="all")
      .loc[lambda d: ~d["Groups/codes"].isin(["Country Code", "Age Groups"])]
)

# pull region names from the columns (skip the first “Groups/codes” col)
regions = df.columns[1:].tolist()

app = Dash(__name__)

region_dropdown = dcc.Dropdown(
    id="region-dd",
    options=[{"label": r, "value": r} for r in regions],
    placeholder="Select region",
    value= regions[0],
    clearable=False
)

app.layout = html.Div([
    html.H1("Population by Group & Region"),
    region_dropdown,
    dcc.Graph(id="pop-bar")
])

@app.callback(
    Output("pop-bar", "figure"),
    Input("region-dd", "value")
)
def update_graph(selected_region):
    # melt or just filter columns: we want Groups/codes on x, and selected_region on y
    dff = df[["Groups/codes", selected_region]].rename(
        columns={"Groups/codes": "Group", selected_region: "Population"}
    )
    fig = px.bar(
        dff,
        x="Group",
        y="Population",
        title=f"{selected_region} population by group"
    )
    fig.update_layout(xaxis_title="", yaxis_title="Count", hovermode="x unified")
    return fig

if __name__ == "__main__":
    app.run(debug=True, port=1222)
# ── 1) Load & clean MYE5 ───────────────────────────────────────────────
df_MYE5 = pd.read_excel(
    "mye22final.xlsx",
    sheet_name="MYE5",
    header=6
).replace("No data", pd.NA).dropna(how="all")

df_MYE5 = df_MYE5.rename(columns={
    df_MYE5.columns[1]: "Region",
    df_MYE5.columns[2]: "GeogType",
    df_MYE5.columns[5]: "Density"
})

df_den = df_MYE5[["Region", "GeogType", "Density"]].copy()
all_types = list(df_den["GeogType"].unique())
geog_types = all_types[1:]  # drop header

app = Dash(__name__)

app.layout = html.Div([
    html.H1("UK mid-2022 Population Density"),
    dcc.Dropdown(
        id="type-dd",
        options=[{"label": t, "value": t} for t in geog_types],
        value="Country",
        clearable=False
    ),
    dcc.Graph(id="density-bar")
])

@app.callback(
    Output("density-bar", "figure"),
    Input("type-dd", "value")
)
def update_density_chart(selected_type):
    dff = df_den[df_den["GeogType"] == selected_type].sort_values("Density", ascending=True)
    
    fig = px.bar(
        dff,
        x="Density",
        y="Region",
        orientation="h",
        title=f"Population Density (people/km²) — {selected_type}",
        hover_data={"Density":":.0f"},
        color_discrete_sequence=["#0072B2"]  # ocean blue, color-blind safe
    )
    fig.update_layout(
        xaxis_title="People per sq. km",
        yaxis_title="",
        margin={"l":150, "r":20, "t":50, "b":50}
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True, port=1222)

import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.express as px

def load_age_sheet(sheet_name, gender_label):
    df = (
        pd.read_excel("mye22final.xlsx", sheet_name=sheet_name, header=7)
          .replace("No data", pd.NA)
          .dropna(how="all")
    )
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        df.columns[0]: "Code",
        df.columns[1]: "Region",
        df.columns[2]: "Geog_Type"
    })
    # drop aggregate & open-ended bins
    df = df.drop(columns=["All ages", "90+"], errors="ignore")
    # pick only numeric age columns
    age_cols = [c for c in df.columns[3:] if c.isdigit()]
    df[age_cols] = df[age_cols].astype(int)
    long = df.melt(
        id_vars=["Region"],
        value_vars=age_cols,
        var_name="Age",
        value_name="Population"
    )
    long["Gender"] = gender_label
    long["Age"] = long["Age"].astype(int)
    return long

# load & combine
df_persons = load_age_sheet("MYE2 - Persons", "All")
df_females = load_age_sheet("MYE2 - Females", "Female")
df_males   = load_age_sheet("MYE2 - Males",   "Male")
df_all = pd.concat([df_persons, df_females, df_males], ignore_index=True)

# load area & compute density
df_area = (
    pd.read_excel("mye22final.xlsx", sheet_name="MYE5", header=6)
      .replace("No data", pd.NA)
      .dropna(how="all")
)
df_area.columns = df_area.columns.str.strip()
df_area = df_area.rename(columns={
    df_area.columns[1]: "Region",
    df_area.columns[3]: "Area_sq_km"
})[["Region", "Area_sq_km"]]

df_all = df_all.merge(df_area, on="Region", how="left")
df_all["Density"] = df_all["Population"] / df_all["Area_sq_km"]

# Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Population Density by Age & Gender"),
    html.Div([
        dcc.Dropdown(
            id="region-dd",
            options=[{"label": r, "value": r} for r in sorted(df_all["Region"].unique())],
            value="UNITED KINGDOM",
            clearable=False,
            style={"flex": "1"}
        ),
        dcc.Dropdown(
            id="gender-dd",
            options=[{"label": g, "value": g} for g in ["All", "Female", "Male"]],
            value="All",
            clearable=False,
            style={"flex": "0 0 150px"}
        ),
    ], style={"display": "flex", "gap": "20px", "margin-bottom": "20px"}),
    dcc.Graph(id="density-age-plot")
])

@app.callback(
    Output("density-age-plot", "figure"),
    Input("region-dd", "value"),
    Input("gender-dd", "value")
)
def update_plot(region, gender):
    dff = df_all[(df_all["Region"] == region) & (df_all["Gender"] == gender)]
    fig = px.line(
        dff.sort_values("Age"),
        x="Age", y="Density",
        markers=True,
        title=f"{gender} density by age in {region}",
        color_discrete_sequence=["#009E73"]  # dark green, color-blind friendly
    )
    fig.update_layout(
        xaxis_title="Age",
        yaxis_title="Density (people/km²)",
        hovermode="x unified",
        margin={"l":50, "r":20, "t":50, "b":50}
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True, port=1222)

from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

# ── Load & clean MYE5 ─────────────────────────────────────────────────────
df_MYE5 = pd.read_excel("mye22final.xlsx", sheet_name="MYE5", header=6)
df_MYE5 = (
    df_MYE5
    .replace("No data", pd.NA)
    .dropna(how="all")
)
df_MYE5 = df_MYE5.rename(columns={
    df_MYE5.columns[0]: "Code",
    df_MYE5.columns[1]: "Name",
    df_MYE5.columns[2]: "Geog_Type",
    df_MYE5.columns[3]: "Area_sq_km",
    df_MYE5.columns[4]: "Pop_2022",
    df_MYE5.columns[5]: "Density_2022",
    df_MYE5.columns[6]: "Pop_2011",
    df_MYE5.columns[7]: "Density_2011"
})

# ── Melt to long form for comparison ──────────────────────────────────────
df_long = df_MYE5.melt(
    id_vars=["Name", "Geog_Type"],
    value_vars=["Density_2011", "Density_2022"],
    var_name="Year",
    value_name="Density"
)
df_long["Year"] = df_long["Year"].str[-4:]

# ── Prepare geography types, excluding the unwanted placeholder ──────────
geog_types = [t for t in df_long["Geog_Type"].unique() if t != "Geography"]

# ── Choose a color-blind-friendly two-color palette (blue & green) ───────
color_map = {
    "2011": "#8E44AD",  # rich purple
    "2022": "#F4D03F"   # vivid yellow
}


app = Dash(__name__)

app.layout = html.Div([
    html.H1("Population Density: 2011 vs 2022"),
    dcc.Dropdown(
        id="type-dd",
        options=[{"label": t, "value": t} for t in geog_types],
        value=geog_types[0],
        clearable=False,
        placeholder="Select geography type",
        style={"width": "50%"}
    ),
    dcc.Graph(id="density-comparison")
])

@app.callback(
    Output("density-comparison", "figure"),
    Input("type-dd", "value")
)
def update_comparison(selected_type):
    dff = df_long[df_long["Geog_Type"] == selected_type]
    fig = px.bar(
        dff,
        x="Name",
        y="Density",
        color="Year",
        barmode="group",
        color_discrete_map=color_map,
        title=f"{selected_type}: Density 2011 vs 2022",
        hover_data={"Density":":.0f"}
    )
    fig.update_layout(
        xaxis_title="Location",
        yaxis_title="People per sq. km",
        margin={"l": 50, "r": 20, "t": 50, "b": 150},
        hovermode="x unified"
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True, port=1222)

