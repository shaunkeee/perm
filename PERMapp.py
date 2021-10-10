#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  4 22:38:43 2021

@author: AutumnTalon
"""

"""
This is Trial #4. Trial #3 became a mess and I haven't touched it for a few
months now, so might as well get back to things.
"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

import numpy as np
import pandas as pd

url = "https://raw.githubusercontent.com/shaunkeee/perm/main/Country%20ISO%20Mapping.csv"
countries = pd.read_csv(url, sep=",", dtype="string", index_col=0)
countries.loc[countries["ISO"].isnull()] = ""


def perm_grouper():
    df = pd.read_csv('permtest.csv', sep=",")

    # makes df_country_counts for world-map-with-slider
    df_country_counts = df.groupby(["YEAR", "COUNTRY_ISO",
                                    "COUNTRY_OF_CITIZENSHIP"]).size()
    df_country_counts = df_country_counts.to_frame(name="COUNT")
    df_country_counts["PERCENT"] = df_country_counts.groupby(level=0).\
        apply(lambda x: 100 * x / float(x.sum())).round(2)
    df_country_counts.reset_index(inplace=True)

    # makes df_state_counts for state-map-with-slider
    df_state_counts = df.groupby(["WORKSITE_STATE", "YEAR",
                                  "COUNTRY_ISO"]).size()
    df_state_counts = df_state_counts.to_frame(name="COUNT")
    df_state_counts["PERCENT"] = df_state_counts.groupby(level=[1, 2]).\
        apply(lambda x: 100 * x / float(x.sum())).round(2)
    df_state_counts.reset_index(inplace=True)

    # makes df_wage_mean
    df_wage_mean = df.groupby(["YEAR", "COUNTRY_ISO"])\
        [["PW_ANNUAL", "WAGE_MEAN_ANNUAL"]].mean().reset_index()

    df_grad_years = df.groupby(
        ["YEAR", "COUNTRY_ISO", "FOREIGN_WORKER_YRS_ED_COMP"]).size()
    df_grad_years = df_grad_years.to_frame(name="COUNT")
    df_grad_years.reset_index(inplace=True)
    df_grad_years = df_grad_years.loc[
        (df_grad_years["FOREIGN_WORKER_YRS_ED_COMP"] > 1970) &
        (df_grad_years["FOREIGN_WORKER_YRS_ED_COMP"] < 2020)]

    # makes df_NAICS_counts for parallel categories graph and STEM facets
    df_NAICS_counts = df[["YEAR", "COUNTRY_ISO", "NAICS_4D_ID", "EMPLOYER_NAME",
                          "PW_SOC_ISSTEM", "FOREIGN_WORKER_EDUCATION"]]
    
    topcount = {"COUNTRY_ISO": 10,
                "NAICS_4D_ID": 25,
                "EMPLOYER_NAME": 300}
    for field in ["COUNTRY_ISO", "NAICS_4D_ID", "EMPLOYER_NAME"]:
        tempcount = df_NAICS_counts.groupby(field).size().rename("COUNT")
        tempcount.sort_values(ascending=False, inplace=True)
        tempcount = tempcount.head(topcount[field])
        # note to self: need to clean employer names of ".", " ", "LLC" etc.
        df_NAICS_counts.loc[~df_NAICS_counts[field].isin(tempcount.index),
                            field] = "OTHERS"
        print(tempcount)
    df_NAICS_counts = df_NAICS_counts.groupby(list(df_NAICS_counts.columns),
                                              dropna=False).size()
    df_NAICS_counts = df_NAICS_counts.to_frame(name="COUNT")
    df_NAICS_counts.reset_index(inplace=True)

    return df_country_counts, df_state_counts, df_NAICS_counts, df_wage_mean,\
        df_grad_years


df_country_counts, df_state_counts, df_NAICS_counts, df_wage_mean,\
    df_grad_years = perm_grouper()

df_country_counts_no_yrs = \
    df_country_counts.groupby(["COUNTRY_ISO", "COUNTRY_OF_CITIZENSHIP"])\
    .sum().reset_index()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


app.layout = html.Div([
    html.H1("Employment-Based Immigration to the United States"),
    dcc.Markdown('''
        
        ### Welcome to our PERM data app!
        
        This app visualizes the US Department of Labor's Permanent Employment
        Certification (PERM) filings from 2008 to 2020. For immigrants who
        seek long-term residency in the United States (i.e., a green card)
        through certain employment-based routes (specifically, EB-2 or EB-3),
        the PERM application is the first major step in their application.
        
        The US DOL releases the PERM dataset online in considerable detail,
        making it a valuable resource for anyone interested in understanding
        patterns in immigration to the US. We hope you enjoy!
        
        #### Global Overview of PERM Applicants
        
        The map below lets you view the distribution of PERM applicants for
        a given year between 2008-20 (use the slider below). Hover over any
        given country to see how the number of applicants from that country
        and their average wage changes over time.
        
        '''),
    html.Div([
        html.Div([
            dcc.RadioItems(
                id="map-projection-radio",
                options=[{"label": "Globe", "value": "orthographic"},
                         {"label": "Flat", "value": "natural earth"}],
                value="natural earth"
                ),
            ],
            style={
            }),
        html.Div([
            dcc.Dropdown(
                id="map-color-scheme",
                options=[{"value": x, "label": x}
                         for x in ["burgyl", "deep", "matter", "tempo",
                                   "sunsetDark"]],
                value="sunsetDark"  # from px.colors.named_colorscales()
                ),
            ],
            style={
            }),
        ]),
    
    html.Div([
        
        html.Div([
            dcc.Graph(
                id='world-map-with-slider',
                clickData={'points': [{'location': 'IND'}]},
                hoverData={'points': [{'location': 'IND'}]}
                ),
            ],
            style={
                'height': '100%', 'width': '74%',
                'float': 'left', 'display': 'inline-block'
            }),
        html.Div([
            dcc.Graph(
                id='sidebar-hover-map-1')
            ],
            style={
                'width': '24%',
                'float': 'upper-right', 'display': 'inline-block'
            }),
        html.Div([
            dcc.Graph(
                id='sidebar-hover-map-2')
            ],
            style={
                'width': '24%',
                'float': 'lower-right', 'display': 'inline-block'})
        
    ], style={}),
    
    dcc.Slider(
        id="year-slider-world-map",
        min=df_country_counts["YEAR"].min(),
        max=df_country_counts["YEAR"].max(),
        value=df_country_counts["YEAR"].min(),
        marks={str(year): str(year) for year in 
               df_country_counts["YEAR"].unique()},
        step=None
    ),

    dcc.Markdown('''
        #### Distribution of PERM Applicants Within the US
        
        The map below provides an overview of where PERM applicants are likely
        to end up within the US, for a given country and year.
        
        To select the country, click on the adjacent table, which shows total
        PERM applicants for FY2008-20 by country. For the year, you'll need
        to select using the slider above - sorry!
        '''),
    html.Div([
        
        html.Div([
            dash_table.DataTable(
                id='total-applicants-table',
                columns=[{"name": i, "id": i} for i in 
                         ["COUNTRY_ISO", "COUNTRY_OF_CITIZENSHIP", "COUNT"]],
                data=df_country_counts_no_yrs.to_dict('records'),
                fixed_rows={'headers': True},
                style_table={'height': '450px', 'overflowY': 'auto'}
                )],
            style={'width': '24%', 'float': 'left'}),
            
        html.Div([
            html.Div([
                dcc.Graph(id='state-map-with-slider')]
            ),
            html.Div([
                dcc.Slider(
                    id="year-slider-state-map",
                    min=df_country_counts["YEAR"].min(),  # fix - shouldn't be country_counts
                    max=df_country_counts["YEAR"].max(),
                    value=df_country_counts["YEAR"].min(),
                    marks={str(year): str(year) for year in 
                           df_country_counts["YEAR"].unique()},
                    step=None
                )])
            ],
            style={'width': '74%', 'float': 'right'}),
    ]),

    dcc.Markdown('''
        #### Distribution of STEM/Non-STEM Applicants for Top Countries
        
        The below set of facet maps shows how STEM/Non-STEM applicants change
        over time for the top 10 countries (all other countries under
        'Others.' By default, this shows all industries, but you can change
        it to select one of the top 25 industries.)
        '''),
    dcc.Dropdown(
        id="NAICS-dropdown-for-facet-map",
        options=[{"label": "ALL", "value": "ALL"}] + 
                [{"label": i, "value": i} for i in
                df_NAICS_counts["NAICS_4D_ID"].unique()],
        value="ALL"
        ),
    dcc.Graph(id='STEM-facet-map'),

    dcc.Markdown('''
        #### Sankey Diagram
        
        This is an overly complicated Sankey diagram. 'Nuff said.
        
        Note that there is no education data from 2008-15 or so.
        '''),
    dcc.Dropdown(
        id="NAICS-sankey-dropdown",
        options=[{"value": x, "label": x}
                 for x in ["COUNTRY_ISO", "PW_SOC_ISSTEM",
                           "FOREIGN_WORKER_EDUCATION", "NAICS_4D_ID",
                           "EMPLOYER_NAME"]],
        value=["COUNTRY_ISO", "PW_SOC_ISSTEM", "FOREIGN_WORKER_EDUCATION",
               "NAICS_4D_ID"],
        multi=True
        ),
    dcc.Graph(id='NAICS-sankey'),
    dcc.Slider(
        id="year-slider-NAICS-sankey",
        min=df_country_counts["YEAR"].min(),  # fix - shouldn't be country_counts
        max=df_country_counts["YEAR"].max(),
        value=df_country_counts["YEAR"].min(),
        marks={str(year): str(year) for year in 
               df_country_counts["YEAR"].unique()},
        step=None
    ),

    dcc.Markdown('''
        #### Distribution by Graduation Year
        
        This shows how folks are distributed by graduation year.
        '''),
    html.Div([
        
        dcc.Dropdown(
            id="country-dropdown",
            options=[{"label": i[0], "value": i[1]} for i in
                     zip(countries.index, countries["ISO"])],
            value="IND"
        ),
        
        html.Div([
            dash_table.DataTable(
                id='grad-yr-table',
                columns=[{"name": i, "id": i} for i in 
                         ["YEAR", "FOREIGN_WORKER_YRS_ED_COMP", "COUNT"]],
                # fix below, hardwired to India right now
                data=df_grad_years.loc[
                    df_grad_years["COUNTRY_ISO"] == "IND",
                    ["YEAR", "FOREIGN_WORKER_YRS_ED_COMP", "COUNT"]].to_dict('records'),
                fixed_rows={'headers': True},
                style_table={'height': '300px', 'overflowY': 'auto'}
                )],
            style={'width': '19%', 'float': 'left'}),
        html.Div([
            dcc.Graph(id='grad-yr-histogram')],
            style={'width': '79%', 'float': 'right'})
        
    ])
])


@app.callback(
    Output('world-map-with-slider', 'figure'),
    Input('map-projection-radio', 'value'),
    Input('map-color-scheme', 'value'),
    Input('year-slider-world-map', 'value'))
def update_world_map(map_option, map_color, selected_year):
    # need to tweak multi so it doesn't throw error when only one selected
    filtered_df = df_country_counts[df_country_counts["YEAR"] == selected_year]
#    filtered_df = filtered_df.loc[~filtered_df["COUNTRY_ISO"].isin(selected_countries)]

    # haven't fixed the hovertip.
    fig = px.choropleth(data_frame=filtered_df, locations="COUNTRY_ISO",
                        color="COUNT", hover_name="COUNTRY_ISO",
                        hover_data=["COUNT", "PERCENT"],
                        locationmode="ISO-3",
                        # sets upper bound as 20% of that year's total entries
                        color_continuous_midpoint=filtered_df["COUNT"].sum() * 0.1,
                        range_color=[0, filtered_df["COUNT"].sum() * 0.2],
                        color_continuous_scale=map_color,
                        height=600,
                        projection=map_option,
                        title="PERM Applicants by Country and Year")

    return fig


@app.callback(
    Output('sidebar-hover-map-1', 'figure'),
    Input('world-map-with-slider', 'hoverData'))
def update_sidebar_hover_map(world_hoverData):
    selected_country = world_hoverData['points'][0]['location']
    filtered_df = df_country_counts[
        df_country_counts["COUNTRY_ISO"] == selected_country]
    
    fig = px.bar(filtered_df, x="YEAR", y="COUNT", height=300)
    
    fig.update_layout(title_text="No. of PERM applicants from " +
                      selected_country)
    
    return fig


@app.callback(
    Output('sidebar-hover-map-2', 'figure'),
    Input('world-map-with-slider', 'hoverData'))
def update_sidebar_hover_map(world_hoverData):
    selected_country = world_hoverData['points'][0]['location']
    filtered_df = df_wage_mean[df_wage_mean["COUNTRY_ISO"] == selected_country]
    
    fig = px.line(
        filtered_df, x="YEAR", y=["PW_ANNUAL", "WAGE_MEAN_ANNUAL"], height=300)

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.65,
                    xanchor="right", x=1),
        title_text="Wages of PERM applicants from " + selected_country
    )

    return fig


@app.callback(
    Output('state-map-with-slider', 'figure'),
    Input('total-applicants-table', 'active_cell'),
    Input('year-slider-state-map', 'value'))
def update_state_map(active_cell, selected_year):
    filtered_df = df_state_counts[df_state_counts["YEAR"] == selected_year]
    if active_cell:
        selected_country = \
            df_country_counts_no_yrs.iloc[active_cell['row']]["COUNTRY_ISO"]
    else:
        selected_country = "IND"
                                                
    filtered_df = filtered_df[filtered_df["COUNTRY_ISO"] == selected_country]

    # haven't fixed the hovertip.
    fig = px.choropleth(
        data_frame=filtered_df, locations="WORKSITE_STATE", color="COUNT",
        hover_name="WORKSITE_STATE", hover_data=["COUNT", "PERCENT"],
        locationmode="USA-states", scope="usa")

    fig.update_layout(transition_duration=500,
                      title_text="Distribution of PERM Applicants From " +
                      selected_country + " in " + str(selected_year))

    return fig


@app.callback(
    Output('STEM-facet-map', 'figure'),
    Input('NAICS-dropdown-for-facet-map', 'value'))
def update_STEM_facet(selected_NAICS_ID):
    if selected_NAICS_ID == "ALL":
        STEM_grouper = df_NAICS_counts.copy()
    else:
        STEM_grouper = df_NAICS_counts[df_NAICS_counts["NAICS_4D_ID"] ==
                                       selected_NAICS_ID]
    STEM_grouper = STEM_grouper.groupby(["COUNTRY_ISO", "YEAR",
                                         "PW_SOC_ISSTEM"]).sum()
    STEM_grouper["PERCENT"] = STEM_grouper["COUNT"].groupby(level = 0).\
        apply(lambda x: 100 * x / float(x.sum())).round(2)
    STEM_grouper.reset_index(inplace=True)

    fig = px.bar(STEM_grouper, x="YEAR", y="PERCENT", color="PW_SOC_ISSTEM",
                 facet_col="COUNTRY_ISO", facet_col_wrap=4,
                 hover_name="COUNTRY_ISO",
                 hover_data=["YEAR", "COUNT", "PERCENT"])

    return fig


@app.callback(
    Output('NAICS-sankey', 'figure'),
    Input('NAICS-sankey-dropdown', 'value'),
    Input('year-slider-NAICS-sankey', 'value'))
def update_sankey(selected_dimensions, selected_year):
    filtered_df = df_NAICS_counts[df_NAICS_counts["YEAR"] == selected_year]
    if selected_year <= 2014:
        try:
            selected_dimensions.remove("FOREIGN_WORKER_EDUCATION")
        except:
            pass
    
    dims=[]
    for dim in selected_dimensions:
        dims.append({'label': dim, 'values': filtered_df[dim]})
        
    fig = go.Figure(go.Parcats(dimensions=dims, counts=filtered_df["COUNT"]))
    
    fig.update_layout(height=1200)

    fig.update_layout(transition_duration=500)
 
    return fig


@app.callback(
    Output('grad-yr-histogram', 'figure'),
    Input('country-dropdown', 'value'))
def update_grad_yr_histogram(selected_country):
    filtered_df = df_grad_years[df_grad_years["COUNTRY_ISO"] ==
                                selected_country]
    maxyr = df_grad_years["YEAR"].max()

    fig = px.density_heatmap(filtered_df, 
                             x="FOREIGN_WORKER_YRS_ED_COMP",
                             y="YEAR", z="COUNT",
                             range_x=[1980, maxyr])
    fig.update_traces(xbins_size=1)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
