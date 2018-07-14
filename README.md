# Pi2B-GrovePi-HTT
High Tech Thermometer implemented on Grove Pi using Python

HTT_GrovePi.py  - High Tech Thermometer using GrovePi hardware.  This program is intended to 
demonstrate a variety of communiction interfaces as much as it collects weather data.

- Get and display current outdoor weather provided by Weather Underground API calls over Internet.

- Get local (indoor) weather using GrovePi+ hardware.

- Use separate Arduino 'traveler' hardware to measure remote temperature and humidity.   Uses serial 
connection over ethernet cable.   

- Display weather info on GrovePi+ two line LCD.

- List all weather info readings for the day on video monitor.

- List all weather info readings for the day in a local text file.

- Copy data file for the day on DropBox. 

- Present graphical data on InitialState website.  ($5/month)

API keys for outdoor weather provider, and InitialState display must be kept confidential.
Do this by defining the keys in APIkeys.py and do not post in GitHub remote repositories.
Observe data traffic limitations for outdoor weather provider, WeatherUnderground.
    Free access using Weather API for Developers limited to 500 calls/day, 10 calls/minute.  
    
As time permits enhancements are planned:  OOP design, improved code error resistance, documentation.
