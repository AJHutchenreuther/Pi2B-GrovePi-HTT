# Pi2B-GrovePi-HTT
High Tech Thermometer implemented on Grove Pi using Python

HTT_GrovePi.py  - High Tech Thermometer using GrovePi hardware.
Get and display current outdoor weather provided by Weather Underground API calls.
Get local (indoor) weather using GrovePi+ hardware.
Display weather info on GrovePi+ LCD
List all weather info readings for the day on screen.
List all weather info readings for the day in a local text file.
Copy data file for the day on DropBox.   (Optionally Arduino.io ?)
Present graphical data on InitialState ($5/month)

API keys for outdoor weather provider, and InitialState display must be kept confidential.
Do this by defining the keys in APIkeys.py and do not post in GitHub remote repositories.
Observe data traffic limitations for outdoor weather provider, WeatherUnderground.
    Free access using Weather API for Developers limited to 500 calls/day, 10 calls/minute.  
    
As time permits enhancements are planned:  OOP design, bulletproofing, documentation.
