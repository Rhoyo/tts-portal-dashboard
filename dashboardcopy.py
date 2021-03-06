import dash
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

from dash import dcc
from dash import html
from dash.dependencies import Input, Output

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],  suppress_callback_exceptions=True)

###############
# Import Data #
###############

# Add a time-of-day column to dataframes so we can see peaks
def addTimeOfDay(df):
	dff = df.copy()
	dff = df['EntryTime']
	tempList = []
	# Go through each entry in the dataframe to find the hour
	for i in range(0, dff.size):
		string = dff[i]
		c1 = string[11]
		c2 = string[12]
		hour = c1 + c2
		hour = int(hour)
		if (hour >= 11 and hour <= 13):
			tempList.append('Midday')
		elif (hour >= 6 and hour <= 9):
			tempList.append('Morning')
		elif (hour >= 15 and hour <= 19):
			tempList.append('Evening')
		else:
			tempList.append('Other')
	return tempList

# Read all csv files in 
vehiclesDf3084 = pd.read_csv("../../data/raw/Broward 3084 Vehicles.csv", delimiter=",")
journeyDf3084 = pd.read_csv("../../data/raw/Broward 3084 Journeys.csv")

vehiclesDf1037 = pd.read_csv("../../data/raw/Broward 1037 Vehicles.csv", delimiter=",")
journeyDf1037 = pd.read_csv("../../data/raw/Broward 1037 Journeys.csv")

vehiclesDf1113 = pd.read_csv("../../data/raw/Broward 1113 Vehicles.csv", delimiter=",")
journeyDf1113 = pd.read_csv("../../data/raw/Broward 1113 Journeys.csv")

#Merge the journey and vehicle files
vehiclesDf3084 = pd.merge(vehiclesDf3084, journeyDf3084)
vehiclesDf1037 = pd.merge(vehiclesDf1037, journeyDf1037)
vehiclesDf1113 = pd.merge(vehiclesDf1113, journeyDf1113)

# Add a peak column to keep track of the time of day 
vehiclesDf3084['Peak'] = addTimeOfDay(vehiclesDf3084)
vehiclesDf1037['Peak'] = addTimeOfDay(vehiclesDf1037)
vehiclesDf1113['Peak'] = addTimeOfDay(vehiclesDf1113) 

##############
# App Layout #
##############

# padding for the page content so it can fit with the sidebar
CONTENT_STYLE = {
    "margin-left": "2rem"
}

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

# This defines the app layout
app.layout = html.Div([
    dcc.Location(id="url"),
    content
])

#############
# Callbacks #
#############

# Defines the page content for any given light
def pageContent(light, df):
	return [
		# Create Title And Dropdown
		html.H1("Broward " + str(light) + " Light", style={"text-align": 'center'}),
		html.Div([
			html.H2("Day #"),
			dcc.Dropdown(
				id='day',
				options=[
						{'label': x, 'value': x}
						for x in df['Day'].unique()],
				value=1
			)
		],
		style={"width": "5%"}),

		# Create Dropdown for Approach
		html.Div([
			html.H2("Approach"),
			dcc.Dropdown(
				id='approach',
				options=[
					{'label': 'Northbound', 'value': 'Northbound'},
					{'label': 'Eastbound', 'value': 'Eastbound'},
					{'label': 'Southbound', 'value': 'Southbound'},
					{'label': 'Westbound', 'value': 'Westbound'},
					{'label': 'ALL', 'value': 'ALL'},
				],
				value='ALL'
			)
		],
		style={"width": "10%"}),

		# Create dropdwon for travel direction
		html.H2("Travel Direction"),
		html.Div([
			dcc.Dropdown(
				id='tdirection',
				options=[
					{'label': 'Straight', 'value': 'Straight'},
					{'label': 'Left', 'value': 'Left'},
					{'label': 'Right', 'value': 'Right'},
					{'label': 'ALL', 'value': 'ALL'},
				],
				value='ALL'
			)
		],
		style={'width': '10%'}),

		# Create Total Delay Chart
		html.Div([
			dcc.Graph(id='total-delay-chart-'+str(light)),
			html.H5(id="avg-delay-"+str(light), style={'padding-left': '150px'}),
			html.H5(id="total-delay-"+str(light), style={'padding-left': '150px'}),
			html.H5(id="total-delay-crossings-"+str(light), style={'padding-left': '150px'}),
		], style={"display": "inline-block", "width": "30%", "vertical-align": "top"}),

		# Create Arrivals Chart
		html.Div([
			dcc.Graph(id='arrival-chart-'+str(light)),
			html.H5(id='green-Arrival-Rate-'+str(light), style={'padding-left': '150px'}),
			html.H5(id='arrival-Crossings-'+str(light), style={'padding-left': '150px'})
		], style={"width": "30%", "display": "inline-block"}),

		# Create Split Failure Chart
		html.Div([
			dcc.Graph(id='split-fail-'+str(light)),
			html.H5(id='Split-Rate-'+str(light), style={'padding-left': '150px'}),
			html.H5(id='Total-Split-Fail-'+str(light), style={'padding-left': '150px'}),
			html.H5(id='Split-Crossing-'+str(light), style={'padding-left': '150px'})
		], style={"display": "inline-block", "width": "30%", "vertical-align": "top"})

	]

# This callback uses the above function to return what belongs on the page
@app.callback(
	Output("page-content", "children"),
	[Input("url", "pathname")]
)
def page_content(pathname):
	# Different page content depending on which page we are pn
	if pathname == "/":
		return pageContent(3084, vehiclesDf3084)

def movementBarChart(light, df, approachD, day):
	dff = df.copy()
	dff = dff[dff["Day"] == day]
	dff = dff[dff["ApproachDirection"].isin(["Northbound","Eastbound","Southbound","Westbound"])]
	#dff = dff[dff["TravelDirection"].isin(["Straight", "Right", "Left"])]

	moveM=px.histogram(
		data_frame=dff,
		x= 'ApproachDirection',
		y= 'Delay',
		title= "Day " + str(day) + " Broward "+ light + " Delay by Movement",
		facet_col="TravelDirection",
		color="Peak",
	)

	return moveM			

# Makes a pie chart for any given light
def arrivalPieChart(light, df, day, approach, tdirection):
	# Set up df according to days
	dff = df.copy()
	dff = dff[dff["Day"] == day]
	dff = dff[dff["RedArrival"].isin(["Yes", "No"])]

	# Set up df according to approach
	if (approach != "ALL"):
		dff = dff[dff["ApproachDirection"] == approach]

	# Set up df according to travel direction
	if (tdirection != "ALL"):
		dff = dff[dff["TravelDirection"] == tdirection]
	

	# Calculate Arrival Crossings
	arrivalCrossings = dff.shape[0]
	arrivalCrossingsStr = "Arrival Crossings: {}".format(arrivalCrossings)
	
	# Calculate number of green crossings
	tempDf = dff[dff["RedArrival"].isin(["No"])]

	greenArrivalRate = int((tempDf.size / dff.size)*100)
	
	# Make strings
	greenArrivalRateStr = "Green Arrival Rate: {}%".format(greenArrivalRate) 

	arrivalRates=px.pie(
		data_frame=dff,
		names="RedArrival",
		color="RedArrival",
		hole=.5,
		title="Broward " + light + " Arrival Rates",
		color_discrete_map={'Yes':'Red', 'No':'#90ee90'}
	)

	return arrivalRates, greenArrivalRateStr, arrivalCrossingsStr

# Makes a split failure pie chart for any given light
def splitPieChart(light, df, day, approach, tdirection):
	# Get dataframe with only values we care about
	dff = df.copy()
	dff = dff[dff["Day"] == day]
	dff = dff[dff["SplitFailure"].isin(["Yes", "No"])]

	# Set up df according to approach
	if (approach != "ALL"):
		dff = dff[dff["ApproachDirection"] == approach]

	# Set up df according to travel direction
	if (tdirection != "ALL"):
		dff = dff[dff["TravelDirection"] == tdirection]

	# Calculate Split Failure Rate, Total Split Failures, And Crossings
	splitCrossings = dff.shape[0]
	splitCrossingStr = "Split Failure Crossings: {}".format(splitCrossings)

	tempDf = dff[dff["SplitFailure"].isin(["Yes"])]
	totalSplitFailure = tempDf.shape[0]
	SplitRate = int((totalSplitFailure/dff.shape[0])*100)

	totalSplitFailureStr = "Total Split Failures: {}".format(totalSplitFailure)
	SplitRateStr = "Split Failure Rate: {}%".format(SplitRate)

	# Create pie chart for light
	splitFailure=px.pie(
		data_frame=dff,
		names="Peak",
		color="Peak",
		hole=.5,
		title="Broward " + light + " Split Failure By Peak",
		color_discrete_map={'Morning':"#90ee90", 'Midday':'#ffd700', "Evening":'red', 'Other':'#808080'}
	)

	return splitFailure, splitCrossingStr, totalSplitFailureStr, SplitRateStr

def totalDelayChart(light, df, day, approach, tdirection):
	# Get dataframe with only values we care about
	dff = df.copy()
	dff = dff[dff["Day"] == day]

	# Set up df according to approach
	if (approach != "ALL"):
		dff = dff[dff["ApproachDirection"] == approach]

	# Set up df according to travel direction
	if (tdirection != "ALL"):
		dff = dff[dff["TravelDirection"] == tdirection]
	
	# Get total crossings
	delayCrossingsStr = "Total Crossings: {}".format(dff.shape[0])

	# Get average delay
	avgDelayStr = "Average Delay: {} (sec/veh)".format(int(dff['Delay'].mean()))

	# Get total delay in hours (3600 seconds per hour)
	totalDelay = int(dff['Delay'].sum()/3600)
	totalDelayStr = "Total Delay: {} (hours)".format(totalDelay)

	# Make pie chart for total delay (in hours) by peak
	# Going to combine delay times by peak and convert them to hours into a new df
	morningDf = dff[dff['Peak'] == 'Morning']
	middayDf = dff[dff['Peak'] == 'Midday']
	eveningDf = dff[dff['Peak'] == 'Evening']
	otherDf = dff[dff['Peak'] == 'Other']

	# Have to delay in hours
	morningDelay = int(morningDf['Delay'].sum()/3600)
	middayDelay = int(middayDf['Delay'].sum()/3600)
	eveningDelay = int(eveningDf['Delay'].sum()/3600)
	otherDelay = int(otherDf['Delay'].sum()/3600)

	# Now combine all into a new dataframe
	d = {'Delay': [morningDelay, middayDelay, eveningDelay, otherDelay], 'Peak': ['Morning', 'Midday', 'Evening', 'Other']}
	newDf = pd.DataFrame(data=d)
	
	# Create delay pie chart
	fig=px.pie(
		data_frame=newDf,
		values='Delay',
		names="Peak",
		color="Peak",
		hole=.5,
		title="Broward " + light + " Total Delay (hours) By Peak",
		color_discrete_map={'Morning':"#90ee90", 'Midday':'#ffd700', "Evening":'red', 'Other':'#808080'}
	)
	return fig, delayCrossingsStr, avgDelayStr, totalDelayStr


# Callback for 3084 charts 
@app.callback(
	[Output(component_id='arrival-chart-3084', component_property='figure'),
	Output(component_id='split-fail-3084', component_property='figure'),
	Output(component_id='green-Arrival-Rate-3084', component_property='children'),
	Output(component_id='arrival-Crossings-3084', component_property='children'),
	Output(component_id='Split-Crossing-3084', component_property='children'),
	Output(component_id='Total-Split-Fail-3084', component_property='children'),
	Output(component_id='Split-Rate-3084', component_property='children'),
	Output(component_id='total-delay-chart-3084', component_property='figure'),
	Output(component_id='avg-delay-3084', component_property='children'),
	Output(component_id='total-delay-3084', component_property='children'),
	Output(component_id='total-delay-crossings-3084', component_property='children')],
	[Input(component_id='day', component_property='value'),
	Input(component_id='approach', component_property='value'),
	Input(component_id='tdirection', component_property='value')]
)
def generate_chart(day, approach, tdirection):
	arrivalRates = arrivalPieChart('3084', vehiclesDf3084, day, approach, tdirection)
	splitFailure = splitPieChart('3084', vehiclesDf3084, day, approach, tdirection)
	totalDelay = totalDelayChart('3084', vehiclesDf3084 , day, approach, tdirection)
	return arrivalRates[0], splitFailure[0], arrivalRates[1], arrivalRates[2], splitFailure[1], splitFailure[2], splitFailure[3], totalDelay[0], totalDelay[2], totalDelay[3], totalDelay[1]



#######
# Run #
#######

if __name__ == '__main__':
	app.run_server(debug=True, port=8300)

