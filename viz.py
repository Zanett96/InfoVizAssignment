# Libraries
import plotly
import dash
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
from pathlib import Path

def get_other(co2):
    """
    Input: co2 value for trip
    Output: 'approximated' mode of travel
    Reformat the mode when 'other' is used as a placeholder.
    We use the co2 to get the mode so we can save one lookup in the 'places' table
    """
    if co2 == 0.075:
        mode = "public"
    elif co2 == 0.20033:
        mode = "car"
    elif co2 == 0.01214:
        mode = "train"
    else:
        mode = "plane"
    return mode

def get_emission(placeid, co2km):
    """
    Input: Place ID, Co2 per km
    Output: total emission of the trip
    Here we retrieve from the places dataframe the distance and we
    return the total emissions as km*co2
    """
    for index, row in places.iterrows():
        if(places.at[index, '#place_id']) == placeid:
            return places.at[index, 'distance']*co2km
    print('Distance not found!')
    return 0


def get_region(userid):
    """
    Input: userID
    Output: Region of the user
    Here we retrieve from the users dataframe the region
    of the user #user_id
    """
    for index, row in users.iterrows():
        if(users.at[index, '#user_id']) == userid:
            return users.at[index, 'region']
    print('Region not found!')
    return 0

def get_dataset(missions):
    """
    Input: Missions dataset
    Output: total emissions and regions for each users
    Here we use the previously built methods to retrieve the
    total emissions and the regions
    """
    emissions, regions = [], []
    
    for index, row in missions.iterrows():
        # Retrieve total emissions
        emissions.append(get_emission(missions.at[index, 'place_id'], missions.at[index, 'co2']))
        # Retrieve Houses for users
        regions.append(get_region(missions.at[index, 'user_id']))
        # Retrieve mode of travel when 'other' is selected -- design chioce explained in report, uncomment if displaying 'other'
        if(missions.at[index, 'mode'] == 'other'): 
            missions.at[index, 'mode'] = get_other(missions.at[index, 'co2']) 
            
    return emissions, regions

def build_dataset(missions):
    """
    Input: Missions dataset
    Output: updated missions dataframe
    Here we build the updated dataset and we save it on disk 
    """
    # Retrieve the total emissions and users regions and add them to the missions dataset
    emissions, regions = get_dataset(missions)
    missions['emissions'] = emissions
    missions['regions'] = regions
    
    # Sort the dataset by date -- needed by the visualization
    missions['date'] = pd.to_datetime(missions.date) 
    missions = missions.sort_values(by='date')
    
    # save the dataset
    missions.to_csv (r'Data/missions.csv', index = False, header=True)
    return missions
    
def _main():
    
    p = Path('Data/missions.csv')

    if p.is_file(): # If the updated dataset exits
        countries = pd.read_csv('Data/missions.csv', sep='\t', header=0)

    else: # If the dataset must be generated
        # Load the 4 datasets using the .read_csv function from pandas, sep = '\t' for tsv files, don't load the header
        # The files are assumed to be in the 'Data' folder
        countries = pd.read_csv('Data/countries.tsv', sep='\t', header=0)
        missions = pd.read_csv('Data/missions.tsv', sep='\t', header=0)
        places = pd.read_csv('Data/places.tsv', sep='\t', header=0)
        users = pd.read_csv('Data/users.tsv', sep='\t', header=0)
        missions = build_dataset(missions)
        
    # Go to http://127.0.0.1:8050/ in the browser to run the visualization
    # or run it in JupyterNotebook using Jupyter Dash.
    modes = ['public', 'car', 'train', 'plane'] # Transportation modes

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] # Modify text Css

    #app = JupyterDash(__name__, external_stylesheets=external_stylesheets) #Uncomment if running on jupyter
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets) #Uncomment if running normally

    # Layout of the visualization
    app.layout = html.Div([
            html.H1('InfoViz assignment: Visualizing emission per region'), # Title
            # Build a checklist for each transportation mode
            dcc.Checklist(
                id="transports",
                options=[{"label": x, "value": x} 
                         for x in modes],
                value=modes[0:], # All selected at the init
                labelStyle={'display': 'inline-block'} # Display in a single line
            ),
            dcc.Graph(id="emission-chart"), 
            ])

    # Interactivity of the visualization: takes as input the trasportation modes and output the graph
    @app.callback(Output("emission-chart", "figure"), [Input("transports", "value")])

    def update_line_chart(modes):

        # Fixed color palette
        color_discrete_map = {'North': '#D55E00', 'Reach': '#0072B2', 'Dorne': '#CC79A7', 'Westerlands': '#E69F00', 'Riverlands': '#009E73', 'Vale': '#19D3F3','Crownlands': '#F0E442'}
        # Gets all the rows from the selected modes in the checklist
        mask = missions['mode'].isin(modes)
        # Get the cumulative sums of the emissions for the visualization
        missions['cumsum'] = missions[mask].groupby('regions')['emissions'].transform(pd.Series.cumsum)

        #Display the visualization. X axis is the date, Y axis is the cumulative emissions. We rename the labels and apply a fixed color palette
        fig = px.line(missions[mask], x='date', y=missions[mask]['cumsum'], color='regions', labels={'date': 'Date', 'y':'Total emissions'}, color_discrete_map=color_discrete_map)
        return fig


    #app.run_server(mode='inline') #Uncomment if running on jupyter
    app.run_server(debug=True) # Uncomment if running normally
        