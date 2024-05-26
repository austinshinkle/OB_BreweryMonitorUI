# system imports
from time import sleep
import threading
import socket
import json

# display imports
from nicegui import run, ui, app
import requests
import json

# debugging 2= MAX; 1 = MIN; 0 = OFF
DEBUG = 1

# socket connection information
server_ip = "ashinkl-rpi4"
server_port = 12345

# styles for CSS formatting
CSS_HEADING_H1 = 'margin: auto; padding: 0px; text-align: center; color: #111111; font-variant: small-caps; font-size: xxx-large; font-weight: 500; font-family: Optima, sans-serif'
CSS_HEADING_H2 = 'margin: auto; padding: 0px; color: #222222; font-variant: small-caps; font-size: xx-large; font-weight: 500; font-family: Optima, sans-serif'
CSS_HEADING_H3 = 'margin: auto; padding: 0px; color: #222222; font-variant: small-caps; font-size: x-large; font-weight: 500; font-family: Optima, sans-serif'
CSS_LABEL = 'margin: auto; color: #333333; font-variant: small-caps; font-size: x-large; font-family: Optima, sans-serif'
CSS_LABEL_SMALL = 'margin: auto; color: #333333; font-variant: small-caps; font-size: medium; font-family: Optima, sans-serif'

FAVICON = '../media/favicon-32x32.png'

# Global variables to communicate between threads
terminate_thread = False
keg_level_1 = 0
keg_level_2 = 0
fermentation_chamber_temp_1 = 0
fermentation_chamber_temp_2 = 0
kegerator_temp = 0

# global variables for web site api calls
# On Tap - Tap 1
tap1_beer_name = ''
tap1_abv = ''
tap1_ibu = ''
tap1_image_url = ''
tap1_page_url = ''
tap1_style = ''

# On Tap - Tap 2
tap2_beer_name = ''
tap2_abv = ''
tap2_ibu = ''
tap2_image_url = ''
tap2_page_url = ''
tap2_style = ''

# In Production - Fermentation Chamber 1
ferm_chamber_1_beer_name = ''
ferm_chamber_1_image_url = ''
ferm_chamber_1_expected_OG = ''
ferm_chamber_1_actual_OG = ''
ferm_chamber_1_expected_FG = ''

# In Production - Fermentation Chamber 2
ferm_chamber_2_beer_name = ''
ferm_chamber_2_image_url = ''
ferm_chamber_2_expected_OG = ''
ferm_chamber_2_actual_OG = ''
ferm_chamber_2_expected_FG = ''


# function that gets the values of the data
# and stores the values in global variables
# designed to be run in a thread 
def get_sensor_data():
	
	global terminate_thread
	global keg_level_1
	global keg_level_2
	global fermentation_chamber_temp_1
	global fermentation_chamber_temp_2
	global kegerator_temp
	
	while not terminate_thread:
		
		# connect to the server which has the data
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client_socket.connect((server_ip,server_port))

		# get the data from the socket
		data = client_socket.recv(1024)
		
		if DEBUG > 0:
			print("Received from server:", data.decode())
		
		# get sensor data from server
		sensor_data = json.loads(data.decode())
		
		if DEBUG > 0:
			print(sensor_data)
		
		# parse dictionary data
		# dictionary elements: 
			# FermentationChamberTemp1_F
			# FermentationChamberTemp2_F
			# KegeratorTemp_F
			# KegWeightSensor1_PCT
			# KegWeightSensor2_PCT

		keg_level_1 = sensor_data["KegWeightSensor1_PCT"]
		keg_level_2 = sensor_data["KegWeightSensor2_PCT"]
		fermentation_chamber_temp_1 = sensor_data["FermentationChamberTemp1_F"]
		fermentation_chamber_temp_2 = sensor_data["FermentationChamberTemp2_F"]
		kegerator_temp = sensor_data["KegeratorTemp_F"]

		client_socket.close()

		sleep(1)

# function that queries Ostentatious Brewing on Wix for the current
# items on tap and updates the NiceGui variables	
# designed to be run in a thread	
def get_on_tap_info():
	
	# varaiables for On Tap info
	global tap1_beer_name
	global tap1_abv
	global tap1_ibu
	global tap1_style
	global tap1_image_url	
	global tap1_page_url
	global tap2_beer_name
	global tap2_abv
	global tap2_ibu
	global tap2_style
	global tap2_image_url
	global tap2_page_url
	
	# variable for In Production info
	global ferm_chamber_1_beer_name
	global ferm_chamber_1_image_url
	global ferm_chamber_1_expected_OG
	global ferm_chamber_1_actual_OG
	global ferm_chamber_1_expected_FG
	global ferm_chamber_2_beer_name
	global ferm_chamber_2_image_url
	global ferm_chamber_2_expected_OG
	global ferm_chamber_2_actual_OG
	global ferm_chamber_2_expected_FG

	# variables for sensors
	global ui_ferm_chamber_temp_1
	global ui_ferm_chamber_temp_2
	global ui_kegerator_temp
	
	global terminate_thread
	
	# Wix API key
	api_key = "IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcIjI4ODk4OTNjLWEwNTgtNGYyZS1hZTljLWZkOTc4NTAyZTY1YVwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcImUyZWRlNzQ2LTk3NGItNGU5MC05YjViLThlMWFhMTgxOTcxM1wifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCJkM2E5MjY4YS1hYmNhLTRkMDEtOTg5MC05MmJjM2E5YThmZGZcIn19IiwiaWF0IjoxNzA4NzU2Mjc0fQ.RG1RtK-aujdflcHiLK7NZ8BjkjLrC8nuoDPayCkyZ0QE1ZPXCX3BsngKVEmGh6KOZ_Gb58bQJ-d-PUa9WtAwRf3oi756qWpwg8VhWurfJag795rj7qMdV39mbzEU3jIN_HvxZn-T6Lr0dLYQw1Wc1cUgrTDUovJ3EYkug0P8T7M5KMToRovz-fxRaqphGUY1WkuHWEpVAYu5xyVeKAmMkqdy5F3xoR-8nhSjWswtJvYYO5qKPvPfEW5G1HZCsZEWwnk-tlkU0EbC2v68hzZlJmJ3ChV2h4PfR00Y4ks12WuUinEaOoIxFVi2jM32i-7WDtvsB_TlVHKOhKKrsf7eMQ"

	# Wix account and site information
	account_id = "d3a9268a-abca-4d01-9890-92bc3a9a8fdf"
	site_id = "a8995e51-a20f-4a5b-88ca-720ed93eb1a7"

	# Wix API endpoint for getting collection items and base image URL
	query_endpoint = 'https://www.wixapis.com/wix-data/v2/items/query'
	image_base_url = 'https://static.wixstatic.com/media/'
	website_base_url = 'https://ostentatiousbrewing.wixsite.com/ostentatiousbrewing'
	
	# CMS database to query
	query_data_on_tap = {
	  "dataCollectionId": "BeerRecipes"
	}
	query_data_in_production = {
	  "dataCollectionId": "BeerRecipesOnTap" # NEED TO CHANGE THIS API NAME!!!
	}

	# define the header
	headers = {
		#'Content-Type': 'application/json',
		'Authorization': f'{api_key}',
		#'wix-account-id': f'{account_id}',
		'wix-site-id': f'{site_id}'  # Example content type
	}

	while not terminate_thread:
	
		# get On Tap data
		try:
			# send the HTTP query
			response = requests.post(query_endpoint, headers=headers, params=query_data_on_tap)
			print("Connecting to Ostentatious Brewing:  Getting On Tap Data...")

			# check if the request was successful (status code 200)
			if response.status_code == 200:
				
				print("SUCCESS!")
				
				# Parse the JSON response
				data = response.json()
				
				# determine how many elements exist
				element_count = data['pagingMetadata']['count']
				
				if DEBUG == 2:
					print(data['dataItems'])
				
				# access the parsed data (as a Python dictionary)
				num = 0
				while num < element_count:
					
					#find information for Tap 1
					if data['dataItems'][num]['data']['onTap'] == 'OnTap_Tap1':

						tap1_beer_name = data['dataItems'][num]['data']['title']            
						tap1_abv = data['dataItems'][num]['data']['actualAbv']
						tap1_ibu = data['dataItems'][num]['data']['calculatedIbu']
						tap1_style = data['dataItems'][num]['data']['style']
						tap1_page_url = website_base_url + data['dataItems'][num]['data']['link-beer-recipes-title']

						
						# get the image string and split the string by "/" and then put the full url together
						parts = data['dataItems'][num]['data']['image'].split("/")
						tap1_image_url = image_base_url + parts[3]
						
					#find information for Tap 2	Connecting to Ostentatious Brewing: Getting In Production Data...
					if data['dataItems'][num]['data']['onTap'] == 'OnTap_Tap2':

						#find information for Tap 2
						tap2_beer_name = data['dataItems'][num]['data']['title']            
						tap2_abv = data['dataItems'][num]['data']['actualAbv']
						tap2_ibu = data['dataItems'][num]['data']['calculatedIbu']
						tap2_style = data['dataItems'][num]['data']['style']
						tap2_page_url = 'target=' + website_base_url + data['dataItems'][num]['data']['link-beer-recipes-title']
						
						# get the image string and split the string by "/" and then put the full url together
						parts = data['dataItems'][num]['data']['image'].split("/")
						tap2_image_url = image_base_url + parts[3]
						
					num += 1
					
			else:
				print(f'Error: {response.status_code}')
		
		except:
			print("Could not connect to the server...will try again later")
			
		# get In Production data
		try:
			# send the HTTP query
			response = requests.post(query_endpoint, headers=headers, params=query_data_in_production)
			print("Connecting to Ostentatious Brewing: Getting In Production Data...")

			# check if the request was successful (status code 200)
			if response.status_code == 200:
				
				print("SUCCESS!")
				
				# Parse the JSON response
				data = response.json()
				
				# determine how many elements exist
				element_count = data['pagingMetadata']['count']
				
				if DEBUG == 2:
					print(data['dataItems'])
				
				# access the parsed data (as a Python dictionary)
				num = 0
				while num < element_count:
					
					#find information for Fermentation Chamber 1
					if data['dataItems'][num]['data']['onTap'] == 'FermChamber1':

						ferm_chamber_1_beer_name = data['dataItems'][num]['data']['title']            
						ferm_chamber_1_expected_OG = data['dataItems'][num]['data']['expectedOg']
						ferm_chamber_1_actual_OG = data['dataItems'][num]['data']['actualOg']
						ferm_chamber_1_expected_FG = data['dataItems'][num]['data']['expectedFg']
						#ferm_chamber_1_page_url = website_base_url + data['dataItems'][num]['data']['link-beer-recipes-title']

						
						# get the image string and split the string by "/" and then put the full url together
						parts = data['dataItems'][num]['data']['image'].split("/")
						ferm_chamber_1_image_url = image_base_url + parts[3]
						
					#find information for Fermentation Chamber 2
					if data['dataItems'][num]['data']['onTap'] == 'FermChamber2':

						ferm_chamber_2_beer_name = data['dataItems'][num]['data']['title']            
						ferm_chamber_2_expected_OG = data['dataItems'][num]['data']['expectedOg']
						ferm_chamber_2_actual_OG = data['dataItems'][num]['data']['actualOg']
						ferm_chamber_2_expected_FG = data['dataItems'][num]['data']['expectedFg']
						#ferm_chamber_2_page_url = website_base_url + data['dataItems'][num]['data']['link-beer-recipes-title']

						
						# get the image string and split the string by "/" and then put the full url together
						parts = data['dataItems'][num]['data']['image'].split("/")
						ferm_chamber_2_image_url = image_base_url + parts[3]
						
					num += 1
					
			else:
				print(f'Error: {response.status_code}')
		
		except:
			print("Could not connect to the server...will try again later")
				
		#HACK!!! only for debugging (you should probably switch this to a wait)
		x = 1
		while not terminate_thread and x < 60:
			x += 1
			sleep(1);

# function run on a timer to update the NiceGui
# colection of calls that don't fit in a single lambda call
def update_ui():

	# update all the variables from global variables
	
	# On Tap - Tap 1
	ui_tap1_image.set_source(tap1_image_url)
	ui_tap1_abv.set_text(f"{tap1_abv} ABV")
	ui_tap1_ibu.set_text(f"{tap1_ibu} IBU")		
	ui_tap1_style.set_text(tap1_style)
	ui_tap1_beer_name.set_text(tap1_beer_name)
	
	# On Tap - Tap 2		
	ui_tap2_image.set_source(tap2_image_url) 
	ui_tap2_abv.set_text(f"{tap2_abv} ABV") 
	ui_tap2_ibu.set_text(f"{tap2_ibu} IBU")
	ui_tap2_style.set_text(tap2_style)
	ui_tap2_beer_name.set_text(tap2_beer_name)
	
# main program
try:

	# start the thread to measure the kegs
	thread_get_sensor_data = threading.Thread(target=get_sensor_data)
	thread_get_sensor_data.start()
	
	# start the thread to query the web site for new data
	thread_get_on_tap_info = threading.Thread(target=get_on_tap_info)
	thread_get_on_tap_info.start()

	# setup up the UI for the web page
	with ui.link(target='https://ostentatiousbrewing.wixsite.com/ostentatiousbrewing', new_tab=True).style("margin: auto"):
		ui.image('../media/Ostentatious Brewing - Robot 2.jpeg').style("width: 250px; margin: auto")
	ui.label('CSS').style(CSS_HEADING_H1).set_text("Ostentatious Brewing")

	# create the overall page with two tabs
	with ui.tabs().classes('w-full') as tabs:
		one = ui.tab('On Tap')
		two = ui.tab('Production Monitor')
	with ui.tab_panels(tabs, value=two).classes('w-full'):
		# On Tap tab
		with ui.tab_panel(one):
			with ui.column().style("margin: auto"):
				with ui.row().style("margin: auto"):
					# create the card for the first beer on tap
					with ui.card().style("margin: auto"):
						ui.label('CSS').style(CSS_HEADING_H2).set_text("Tap 1")
						# add the beer image and style
						ui_tap1_beer_name = ui.label('CSS').style(CSS_HEADING_H3)	
						with ui.link(target=tap1_page_url, new_tab=True).style("margin: auto"):
							ui_tap1_image = ui.image(tap1_image_url).style("width: 300px;")
						ui_tap1_style = ui.label('CSS').style(CSS_HEADING_H3)	
						
						# show beer statistics
						with ui.grid(columns=2).style("margin: auto"):
							ui_tap1_abv = ui.label('CSS').style(CSS_LABEL_SMALL)
							ui_tap1_ibu = ui.label('CSS').style(CSS_LABEL_SMALL)
						
						# show the remaining beer	
						ui_tap1_pct_beer = ui.label('CSS').style(CSS_LABEL)
					
					# create the card for the second beer on tap	
					with ui.card().style("margin: auto"):
						ui.label('CSS').style(CSS_HEADING_H2).set_text("Tap 2")		
						# add the beer image and style
						ui_tap2_beer_name = ui.label('CSS').style(CSS_HEADING_H3)	
						with ui.link(tap2_page_url, new_tab=True).style("margin: auto"): 
							ui_tap2_image = ui.image(tap2_image_url).style("width: 300px;")
						ui_tap2_style = ui.label('CSS').style(CSS_HEADING_H3)
						
						# show beer statistics
						with ui.grid(columns=2).style("margin: auto"):
							ui_tap2_abv = ui.label('CSS').style(CSS_LABEL_SMALL)
							ui_tap2_ibu = ui.label('CSS').style(CSS_LABEL_SMALL)
						# show the remaining beer	
						ui_tap2_pct_beer = ui.label('CSS').style(CSS_LABEL)
				
				# show the kegerator temperature						
				with ui.card().style("width: 100%"):
					ui.label('CSS').style(CSS_HEADING_H2).set_text("Kegerator")						
					ui.label('CSS').style(CSS_LABEL_SMALL).set_text("Temperature")	
					ui_kegerator_temp = ui.label('CSS').style(CSS_LABEL)			
						
		# In Production tab
		with ui.tab_panel(two):		
			with ui.row().style("margin: auto"):
				# show fermentation chamber 1 temperature
				with ui.card():
					ui.label('CSS').style(CSS_HEADING_H2).set_text("Fermentation Chamber 1")	
					ui.label('CSS').style(CSS_LABEL_SMALL).set_text("Temperature")	
					ui_ferm_chamber_temp_1 = ui.label('CSS').style(CSS_LABEL)	
				# show fermentation chamber 2 temperature
				with ui.card():
					ui.label('CSS').style(CSS_HEADING_H2).set_text("Fermentation Chamber 2")				
					ui.label('CSS').style(CSS_LABEL_SMALL).set_text("Temperature")		
					ui_ferm_chamber_temp_2 = ui.label('CSS').style(CSS_LABEL)				
					
		tabs.set_value('On Tap')
	
	# update UI elements on timers
	ui.timer(1.0, lambda: ui_tap1_pct_beer.set_text(f'{keg_level_1}% Beer Remaining'))
	ui.timer(1.0, lambda: ui_tap2_pct_beer.set_text(f'{keg_level_2}% Beer Remaining'))
	ui.timer(1.0, lambda: update_ui()) 

	ui.timer(1.0, lambda: ui_ferm_chamber_temp_1.set_text(f'{fermentation_chamber_temp_1} F'))
	ui.timer(1.0, lambda: ui_ferm_chamber_temp_2.set_text(f'{fermentation_chamber_temp_2} F'))
	ui.timer(1.0, lambda: ui_kegerator_temp.set_text(f'{kegerator_temp} F'))



	# run the UI   192.168.178.74
	ui.run(reload=False, native=False, title='Ostentatious Brewing', favicon=FAVICON, host='192.168.178.74')
	
	# Wait for keyboard input to terminate the thread
	input("Press Enter to stop the program..\n")
	terminate_thread = True
	
	# wait for the measure keg thread to complete
	# note: terminate other threads immediately
	thread_get_sensor_data.join()

finally:
	print("Script terminated!")
