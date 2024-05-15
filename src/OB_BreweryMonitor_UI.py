# system imports
from time import sleep
import threading
import socket
import json

# display imports
from nicegui import run, ui, app
import requests
import json

# socket connection information
server_ip = "ashinkl-rpi4"
server_port = 12345

# styles for CSS formatting
CSS_HEADING_H1 = 'color: #111111; font-variant: small-caps; font-size: xxx-large; font-weight: 500; font-family: Andale Mono, monospace'
CSS_HEADING_H2 = 'color: #222222; font-variant: small-caps; font-size: xx-large; font-weight: 500; font-family: Andale Mono, monospace'
CSS_LABEL = 'color: #333333; font-variant: small-caps; font-size: x-large; font-family: Andale Mono, monospace'
CSS_LABEL_SMALL = 'color: #333333; font-variant: small-caps; font-size: medium; font-family: Andale Mono, monospace'

FAVICON = '../media/favicon-32x32.png'

# Global variables to communicate between threads
terminate_thread = False
keg_level_1 = 0
keg_level_2 = 0
fermentation_chamber_temp_1 = 0
fermentation_chamber_temp_2 = 0
kegerator_temp = 0

# global variables for web site api calls
tap1_beer_name = ''
tap1_abv = ''
tap1_ibu = ''
tap1_image_url = ''
tap2_beer_name = ''
tap2_abv = ''
tap2_ibu = ''
tap2_image_url = ''


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
		
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client_socket.connect((server_ip,server_port))

		data = client_socket.recv(1024)
		print("Received from server:", data.decode())
		
		# get sensor data from server
		sensor_data = json.loads(data.decode())
		print(sensor_data)
		
		# parse dictionary data
		# dictionary elements: 
			# FermentationChamberTemp1_C
			# FermentationChamberTemp2_C
			# KegeratorTemp_C
			# KegWeightSensor1_PCT
			# KegWeightSensor2_PCT

		keg_level_1 = sensor_data["KegWeightSensor1_PCT"]
		keg_level_2 = sensor_data["KegWeightSensor2_PCT"]
		fermentation_chamber_temp_1 = sensor_data["FermentationChamberTemp1_C"]
		fermentation_chamber_temp_2 = sensor_data["FermentationChamberTemp2_C"]
		kegerator_temp = sensor_data["KegeratorTemp_C"]

		client_socket.close()

		sleep(1)

# function that queries Ostentatious Brewing on Wix for the current
# items on tap and updates the NiceGui variables	
# designed to be run in a thread	
def get_on_tap_info():
	
	global tap1_beer_name
	global tap1_abv
	global tap1_ibu
	global tap1_image_url
	global tap2_beer_name
	global tap2_abv
	global tap2_ibu
	global tap2_image_url
	
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
	
	# CMS database to query
	query_data = {
	  "dataCollectionId": "BeerRecipes"
	}

	# define the header
	headers = {
		#'Content-Type': 'application/json',
		'Authorization': f'{api_key}',
		#'wix-account-id': f'{account_id}',
		'wix-site-id': f'{site_id}'  # Example content type
	}

	while not terminate_thread:
	
		try:
			# send the HTTP query
			response = requests.post(query_endpoint, headers=headers, params=query_data)
			print("Getting HTTP data from Ostentatious Brewing!")

			# check if the request was successful (status code 200)
			if response.status_code == 200:
				
				# Parse the JSON response
				data = response.json()
				
				# determine how many elements exist
				element_count = data['pagingMetadata']['count']
				
				# access the parsed data (as a Python dictionary)
				num = 0
				while num < element_count:
					
					#find information for Tap 1
					if data['dataItems'][num]['data']['onTap'] == 'Tap1':

						tap1_beer_name = data['dataItems'][num]['data']['title']            
						tap1_abv = data['dataItems'][num]['data']['actualAbv']
						tap1_ibu = data['dataItems'][num]['data']['calculatedIbu']
						
						# get the image string and split the string by "/" and then put the full url together
						parts = data['dataItems'][num]['data']['image'].split("/")
						tap1_image_url = image_base_url + parts[3]
						
					#find information for Tap 2	
					if data['dataItems'][num]['data']['onTap'] == 'Tap2':

						#find information for Tap 2
						tap2_beer_name = data['dataItems'][num]['data']['title']            
						tap2_abv = data['dataItems'][num]['data']['actualAbv']
						tap2_ibu = data['dataItems'][num]['data']['calculatedIbu']
						
						# get the image string and split the string by "/" and then put the full url together
						parts = data['dataItems'][num]['data']['image'].split("/")
						tap2_image_url = image_base_url + parts[3]
						
					num += 1
					
			else:
				print(f'Error: {response.status_code}')
		
		except:
			print("Could not connect to the server...will try again later")
				
		sleep(60);

# function run on a timer to update the NiceGui
# colection of calls that don't fit in a single lambda call
def update_ui():

	# update all the variables from global variables
	ui_tap1_image.set_source(tap1_image_url)
	ui_tap1_abv.set_text(f"{tap1_abv} ABV")
	ui_tap1_ibu.set_text(f"{tap1_ibu} IBU")
	ui_tap2_image.set_source(tap2_image_url) 
	ui_tap2_abv.set_text(f"{tap2_abv} ABV") 
	ui_tap2_ibu.set_text(f"{tap2_ibu} IBU") 
	
# main program
try:

	# start the thread to measure the kegs
	thread_get_sensor_data = threading.Thread(target=get_sensor_data)
	thread_get_sensor_data.start()
	
	# start the thread to query the web site for new data
	thread_get_on_tap_info = threading.Thread(target=get_on_tap_info)
	thread_get_on_tap_info.start()
	
	### FIX THIS LATER!!!! (not a good implementation)
#	sleep(5)
	
	# setup up the UI for the web page
	with ui.row():
		ui.image('../media/Ostentatious Brewing - Robot 2.jpeg').style("width: 100px")
		ui.link('Ostentatious Brewing Brewery Monitor', 'https://ostentatiousbrewing.wixsite.com/ostentatiousbrewing', new_tab=True).style(CSS_HEADING_H1)
	ui.label('CSS').style(CSS_HEADING_H2).set_text("Tap List")
	with ui.row():
		with ui.card():
			ui.label('CSS').style(CSS_HEADING_H2).set_text("Tap 1")
			ui_tap1_image = ui.image(tap1_image_url).style("width: 250px")
			ui_tap1_abv = ui.label('CSS').style(CSS_LABEL_SMALL)
			ui_tap1_ibu = ui.label('CSS').style(CSS_LABEL_SMALL)
			ui_tap1_pct_beer = ui.label('CSS').style(CSS_LABEL)
		with ui.card():
			ui.label('CSS').style(CSS_HEADING_H2).set_text("Tap 2")		
			ui_tap2_image = ui.image(tap2_image_url).style("width: 250px")
			ui_tap2_abv = ui.label('CSS').style(CSS_LABEL_SMALL)
			ui_tap2_ibu = ui.label('CSS').style(CSS_LABEL_SMALL)
			ui_tap2_pct_beer = ui.label('CSS').style(CSS_LABEL)
	with ui.row():
		with ui.card():
			ui.label('CSS').style(CSS_HEADING_H2).set_text("Ferm Chamber 1 Temp")		
			ui_ferm_chamber_temp_1 = ui.label('CSS').style(CSS_LABEL)
		with ui.card():
			ui.label('CSS').style(CSS_HEADING_H2).set_text("Ferm Chamber 2 Temp")		
			ui_ferm_chamber_temp_2 = ui.label('CSS').style(CSS_LABEL)
		with ui.card():
			ui.label('CSS').style(CSS_HEADING_H2).set_text("Kegerator Temp")		
			ui_kegerator_temp = ui.label('CSS').style(CSS_LABEL)
			
	
	# update UI elements on timers
	ui.timer(1.0, lambda: ui_tap1_pct_beer.set_text(f'{keg_level_1}% Beer Remaining'))
	ui.timer(1.0, lambda: ui_tap2_pct_beer.set_text(f'{keg_level_2}% Beer Remaining'))
	ui.timer(15, lambda: update_ui()) 

	ui.timer(1.0, lambda: ui_ferm_chamber_temp_1.set_text(f'{fermentation_chamber_temp_1} C'))
	ui.timer(1.0, lambda: ui_ferm_chamber_temp_2.set_text(f'{fermentation_chamber_temp_2} C'))
	ui.timer(1.0, lambda: ui_kegerator_temp.set_text(f'{kegerator_temp} C'))



	# run the UI
	ui.run(reload = False, title="Ostentatious Brewing", favicon=FAVICON)
	
	# Wait for keyboard input to terminate the thread
	input("Press Enter to stop the program..\n")
	terminate_thread = True
	
	# wait for the measure keg thread to complete
	# note: terminate other threads immediately
	thread_get_sensor_data.join()

finally:
	print("Script terminated!")
