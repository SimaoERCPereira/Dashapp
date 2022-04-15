import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import numpy as np
import pandas as pd
import plotly.graph_objs as go

# https://htmlcheatsheet.com/css/

######################################################Data##############################################################

data = pd.read_excel("Data.xlsx")

energy_types = ['Total Renewable', 'Total Not Renewable']

sectors = ['Biofuels Production - TWh - Total', 'Electricity from hydro (TWh)', 'Electricity from solar (TWh)', 'Electricity from wind (TWh)',"Coal Consumption - TWh", "Oil Consumption - TWh","Gas Consumption - TWh","Nuclear Consumption - TWh"]

######################################################Interactive Components############################################

country_options = [dict(label=country, value=country) for country in data['Entity'].unique()]

energy_options = [dict(label=energy.replace('_', ' '), value=energy) for energy in energy_types]

sector_options = [dict(label=sector.replace('_', ' '), value=sector) for sector in sectors]


dropdown_country = dcc.Dropdown(
        id='country_drop',
        options=country_options,
        value=['Portugal'],
        multi=True
    )

dropdown_energy_types = dcc.Dropdown(
        id='energy_options',
        options=energy_options,
        value='Total Renewable',
    )

dropdown_sector = dcc.Dropdown(
        id='sector_option',
        options=sector_options,
        value=['Biofuels Production - TWh - Total', 'Coal Consumption - TWh'],
        multi=True
    )

slider_year = dcc.Slider(
        id='year_slider',
        min=data['Year'].min(),
        max=data['Year'].max(),
        marks={str(i): '{}'.format(str(i)) for i in
               [1965, 1970, 1975, 1980, 1985,1990, 1995, 2000, 2005, 2010, 2015, 2020]},
        value=data['Year'].min(),
        step=1
    )

radio_lin_log = dcc.RadioItems(
        id='lin_log',
        options=[dict(label='Linear', value=0), dict(label='log', value=1)],
        value=0
    )

radio_projection = dcc.RadioItems(
        id='projection',
        options=[dict(label='Equirectangular', value=0),
                 dict(label='Orthographic', value=1)],
        value=0
    )


##################################################APP###################################################################

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div([

    html.H1('Energy production Dashboard'),

    html.Label('Country Choice'),
    dropdown_country,

    html.Br(),

    html.Label('Energy Choice'),
    dropdown_energy_types,

    html.Br(),

    html.Label('Sector Choice'),
    dropdown_sector,

    html.Br(),

    html.Label('Year Slider'),
    slider_year,

    html.Br(),

    html.Label('Linear Log'),
    radio_lin_log,

    html.Br(),

    html.Label('Projection'),
    radio_projection,

    html.Br(),

    html.Label(id='energy_1'),
    html.Br(),
    html.Label(id='energy_2'),
    html.Br(),


    dcc.Graph(id='bar_graph'),

    dcc.Graph(id='choropleth'),

    dcc.Graph(id='aggregate_graph')
])


######################################################Callbacks#########################################################


@app.callback(
    [
        Output("bar_graph", "figure"),
        Output("choropleth", "figure"),
        Output("aggregate_graph", "figure"),
    ],
    [
        Input("year_slider", "value"),
        Input("country_drop", "value"),
        Input("energy_options", "value"),
        Input("lin_log", "value"),
        Input("projection", "value"),
        Input('sector_option', 'value')
    ]
)



def plots(year, countries, energy, scale, projection, sector):
    ############################################First Bar Plot##########################################################
    data_bar = []
    for country in countries:
        df_bar = data.loc[(data['Entity'] == country)]

        x_bar = df_bar['Year']
        y_bar = df_bar[energy]

        data_bar.append(dict(type='bar', x=x_bar, y=y_bar, name=country))

    layout_bar = dict(title=dict(text= str(
                                            energy) + " energy production from 1965 until 2020"),
                      yaxis=dict(title='Energy production', type=['linear', 'log'][scale]),
                      paper_bgcolor='rgba(0,0,0,0)',
                      font_color="white"
                      )

    #############################################Second Choropleth######################################################

    df_emission_0 = data.loc[data['Year'] == year]

    z = np.log(df_emission_0[energy])

    data_choropleth = dict(type='choropleth',
                           locations=df_emission_0['Entity'],
                           # There are three ways to 'merge' your data with the data pre embedded in the map
                           locationmode='country names',
                           z=z,
                           text=df_emission_0['Entity'],
                           colorscale='mint',
                           colorbar=dict(title=str(energy.replace('_', ' ')) + ' (log scaled)'),

                           hovertemplate='Country: %{text} <br>' + str(energy.replace('_', ' ')) + ': %{z}',
                           name=''
                           )

    layout_choropleth = dict(geo=dict(scope='world',  # default
                                      projection=dict(type=['equirectangular', 'orthographic'][projection]
                                                      ),
                                      # showland=True,   # default = True
                                      landcolor='white',
                                      lakecolor='white',
                                      showocean=True,  # default = False
                                      oceancolor='azure',
                                      bgcolor='#f9f9f9'
                                      ),

                             title=dict(
                                 text='World ' + str(energy.replace('_', ' ')) + ' Choropleth Map on the year ' + str(
                                     year),
                                 x=.5,
                                 font_color = "white",# Title relative position according to the xaxis, range (0,1)


                             ),
                             paper_bgcolor='rgba(0,0,0,0)'
                             )


    ############################################Third Scatter Plot######################################################

    df_loc = data.loc[data['Entity'].isin(countries)].groupby('Year').sum().reset_index()

    data_agg = []

    for place in sector:
        data_agg.append(dict(type='scatter',
                             x=df_loc['Year'].unique(),
                             y=df_loc[place],
                             name=place.replace('_', ' '),
                             mode='markers'
                             )
                        )

    layout_agg = dict(title=dict(text='Aggregate energy production by Sector'),
                      yaxis=dict(title=['Total energy', 'Total energy(log scaled)'][scale],
                                 type=['linear', 'log'][scale]),
                      xaxis=dict(title='Year'),
                      paper_bgcolor='rgba(0,0,0,0)',
                      font_color="white",
                      )

    return go.Figure(data=data_bar, layout=layout_bar), \
           go.Figure(data=data_choropleth, layout=layout_choropleth), \
           go.Figure(data=data_agg, layout=layout_agg)


def indicator(countries, year):
    df_loc = data.loc[data["Entity"].isin(countries)].groupby('Year').sum().reset_index()

    value_1 = round(df_loc.loc[df_loc['Year'] == year][energy_types[0]].values[0], 2)
    value_2 = round(df_loc.loc[df_loc['Year'] == year][energy_types[1]].values[0], 2)

    return str(energy_types[0]).replace('_', ' ') + ': ' + str(value_1), \
           str(energy_types[1]).replace('_', ' ') + ': ' + str(value_2), \




if __name__ == '__main__':
    app.run_server(debug=True)


