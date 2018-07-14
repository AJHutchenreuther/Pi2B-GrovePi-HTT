'''
 HTT<program n ame>.py
 Adapted from Home_Weather_Display.py and HTThermometer.py

 This is a project for using the Grove RGB LCD Display and the Grove DHT Sensor from the GrovePi starter kit
 
 In this project, the Temperature and humidity from the DHT sensor is printed on the RGB-LCD Display

 Note the dht_sensor_type below may need to be changed depending on which DHT sensor you have:
  0 - DHT11 - blue one  - lower precision and accuracy (+/- 2degC, 5% RH) than DHT22.  Comes with the GrovePi+ Starter Kit
  1 - DHT22 - white one, aka DHT Pro or AM2303.  Accuracy +- .5degC, 2-5% RH)
              AM2303 sensor uses the DS18B20 temperature sensor.
              AM2302 sensor is the 'wired' version of the AM2303.
  2 - DHT21 - black one, aka AM2301
 
 For more info please see: http://www.dexterindustries.com/topic/537-6c-displayed-in-home-weather-project/

  Issues:  In Python3,  'No module named 'grovepi' and 'grove_rgb_lcd'
           Workaround: copy to my development folder these files:
               grovepi.py and grove_rgb_lcd.py in
               /home/pi/Desktop/GrovePi/Software/Python/  & ./grove_rgb_lcd 
           Future: try reinstalling GrovePi software, Forum indicates this workaround
                   means software was not installed correctly.   Also rerun setup.py
                   in /home/pi/Desktop/GrovePi/Software/Python folder.

           In Python 3, import error: ISStreamer.  Import works in Python2.
           In Python2, import error:  No module named request.
           Workaround: revise program to use "requests" and import requests.
           See minimal code demonstration in GetForecast.py

           Similar projects could use same base code?
           - HTT_GrovePi.py: This project provides indoor T&RH using the DHT22 sensor.
           - HTT_RPiPixel.py: A very similar project provides indoor T (not RH) using the DS18B20 sensor.
           Approach: 'refactor' the code to separate common code from the unique features.
           Main program file call:  HTT_Unified.py
'''
'''
The MIT License (MIT)

GrovePi for the Raspberry Pi: an open source platform for connecting Grove Sensors to the Raspberry Pi.
Copyright (C) 2015  Dexter Industries

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

"""
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

Revisions:
20161222
- Store APIkey in external file:  APIcodes.py
- Reconfigure LCD display to show indoor and outdoor Temperature and Humidity
- Limit queries to forecast.io independently of display update rate.
20161223
- Store weather data in daily file on disk at midnight local time.
- Catch and correct bad readings from indoor thermometer.
20161224
- Transfer daily file to DropBox. Done.  ALternate method using CLI in data directory:
  ~/Dropbox-Uploader/dropbox_uploader.sh upload HTT_Log_2016*.csv ./Apps/
- Dim the RGB LCD display during night time.
20161229
- Fix bug by eliminating unwanted copy of fnmatch.py in working directory.
    #pi@dex:~/Documents/PythonProjects/HTT $ sudo sh launcher.sh
    ##Traceback (most recent call last):
    ##  File "HTT.py", line 117, in <module>
    ##    import shutil
    ##  File "/usr/lib/python2.7/shutil.py", line 11, in <module>
    ##    import fnmatch
    ##  File "/home/pi/Documents/PythonProjects/HTT/fnmatch.py", line 41, in <module>
    ##    @functools.lru_cache(maxsize=256, typed=True)
    ##AttributeError: 'module' object has no attribute 'lru_cache'
- Fix bug by testing type of 'temp' from dht call.
    ##Traceback (most recent call last):
    ##  File "/home/pi/Documents/PythonProjects/HTT/HTT.py", line 202, in <module>
    ##    lcdText = lcdTemplate.format(temp, hum)
    ##ValueError: Unknown format code 'f' for object of type 'str'
    ##
- Complete headless shutdown and restart function.
- Add pilot light that shows activity.
20161230
- Change outdoor weather API to WeatherUnderground to get smooth outdoor data.
- Add subscription for InitialState to allow multiple sensors.

ToDo:
- Display temperature data graphically & store graph at end of day.
- Complete satellite without GrovePi using PiZero or Arduino.
- Integration test program long-term to identify and work-around possible causes of crashing.
- After integration tests, Refactor code to allow different sensors, data.
- Correct cause for permission denied errors on today.csv
    cd ~/Documents/PythonPRojects/HTT
    sudo chmod 777 today.csv
    ls -la today.csv
"""
# ***********************  Start-up  ************************************************
import requests
import json, datetime
import time
import os
import platform
import shutil
import math
import serial
from grovepi import *
from grove_rgb_lcd import *
from ISStreamer.Streamer import Streamer  # Needs Python2 at this time.
from subprocess import Popen
from subprocess import call
#from w1thermsensor import W1ThermSensor # To run on Pi3B

from APIcodes import *  # Keep value of API keys confidential!

sw_pin = 3                      # Pushbutton pin
pilot_pin = 2                   # Pilot light pin.  Normally slow blink.
dht_sensor_port = 7		# Connect the DHt sensor to port 7
dht_sensor_type = 1             # change this depending on your sensor type - see header comment
forecastInterval = 24*60*60/200 # About 432 seconds between queries for free WeatherUnderground.
infoUploadInterval = 180	# Seconds between updates
lastQueryTime = 0
oldLogFileTime = time.localtime()  # Prepare to restart the log at midnight
oldLogFileName = "today.csv"   # If permission error:  sudo chmod 777 today.csv
indoorTemp = 10.0
indoorHum = 50.0
travelerTemp = " "
travelerHum = " "
outdoorTemp = oldOutdoorTemp = "75"  # Added 25Jun18 for error handling.
outdoorHum = oldOutdoorHum = "30"

def getWunderground() :
    URLstart = 'http://api.wunderground.com/api/'
    URLend = '/geolookup/conditions/q/MI/Southfield.json'
    url = URLstart+Wundergroundkey+URLend
    
    response = requests.request('GET',url)
    return json.loads(response.text)

# Create streamer object for InitialState
## This error message has been seen for Streamer.  To be investigated.  Bullet proof by putting in loop until successs.
##ISStreamer failed to create or find bucket after a number of attempts
##Starting data logger loop
##Error ('Connection aborted.', gaierror(-2, 'Name or service not known'))
##
try:
    streamer = Streamer(bucket_name="Trial2", bucket_key=Trial2BucketKey, access_key=InitialStatekey) # Codes in APIcode.py
    print(type(streamer)) # <type 'instance'>  seen on successful start.
    time.sleep(3)
except Exception as e:
    print("Streamer error")
    print(str(e))

# Serial data port to receive remote satellite Arduino over USB: attic weather for this version.
##Comment out while disconnected
ser = serial.Serial(
    port = '/dev/ttyACM0', # find with dmesg | grep -I tty. ttyACM0 is the console.
    baudrate = 9600
    )
"""Changed to ttyACM1 to correct I/O error begun while away.
('Readline error ', '107, 17.50\r\n')
(5, 'Input/output error')
2017-08-02 16:30:37, 79.3, 61.3, 84.0, 49, 107.0,17.5
"""
            
# *********************** Main Program Loop  ************************************************
print('Starting data logger loop')
while True:
    try:    # 'except' block at end of page!.
        timeNow = time.time()
        if(( timeNow - lastQueryTime)>= forecastInterval):
            
            # Get outdoor conditions from a local weather station.
            
            # Add try to handle this kind of error:  ajh20180625
            ## Traceback (most recent call last):
            ##  File "/home/pi/Documents/PythonProjects/HTT/HTT_Unified.py", line 195, in <module>
            ##    forecast = getWunderground()
            ##  File "/home/pi/Documents/PythonProjects/HTT/HTT_Unified.py", line 159, in getWunderground
            ##    return json.loads(response.text)
            ##  File "/usr/lib/python2.7/json/__init__.py", line 338, in loads
            ##    return _default_decoder.decode(s)
            ##  File "/usr/lib/python2.7/json/decoder.py", line 366, in decode
            ##    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
            ##  File "/usr/lib/python2.7/json/decoder.py", line 384, in raw_decode
            ##    raise ValueError("No JSON object could be decoded")
            ##ValueError: No JSON object could be decoded
            try:  
                
                forecast = getWunderground()
                lastQueryTime = timeNow
                
                ## For debugging... pretty print the JSON data returned by getWunderground().
                #json.dump(forecast, fp=open('testjson.txt', 'w'), indent=4)
                #print("Forecast contents, of type ", type(forecast))
                #print(open('testjson.txt').read())

                # Weather Underground API
                try:
                    # Preserve last readings to aid with error recovery:
                    oldOutdoorTemp = outdoorTemp
                    oldOutdoorHum = outdoorHum
                    # New readings...
                    outdoorTemp = forecast['current_observation']['temp_f']
                    outdoorHum = forecast['current_observation']['relative_humidity']
                    # Remove % character from outdoorHum as reported by Wunderground API
                    outdoorHum = outdoorHum.rstrip('%')
                    # New 25Jun18 for debugging
                    json.dump(forecast, fp=open('lastforecast.txt', 'w'), indent = 2)

                except Exception as e:
                    print( "json.dump: " + str(e))
                    fp=open('badjson.txt', 'a')
                    fp.write(str(e)+'\n')
                    fp.close()
                    json.dump(forecast, fp=open('badjson.txt', 'a'), indent=4)
                    # Restore last readings to continue with script.
                    outdoorTemp = oldOutdoorTemp
                    outdoorHum = oldOutdoorHum
                    
            except Exception as e:  # getWunderground()
                print("getWunderground: " + str(e))

        # Indoor conditions
        oldIndoorTemp = indoorTemp
        oldIndoorHum = indoorHum
        [ indoorTemp, indoorHum ] = dht(dht_sensor_port,dht_sensor_type)
        #Get the temperature and Humidity from the DHT sensor
        indoorTemp = indoorTemp *9/5+32 # Convert temp to deg F
        # Remove known data glitches.
        if( indoorTemp == 32):  
           indoorTemp = oldIndoorTemp
           print( "Glitch for indoorTemp")
        if( indoorHum == 0):  # Indoor humidity change not exceeding limit.
           indoorHum = oldIndoorHum
           print( "Glitch for indoorHum")
           
##  Start of comment out while disconnected
        try:
        # Traveling sensor (attic) conditions       
            ser.flushInput()
            oldTravelerTemp = travelerTemp
            oldTravelerHum = travelerHum
            arduinoString = ser.readline()
            #print("Traveler: ", arduinoString)
            result = arduinoString.strip()
            [travelerTemp, travelerHum] = result.split(',')
            
##          print("Indoor ", type(indoorTemp), type(indoorHum))
##          print("Outdoor: ", type(outdoorTemp), type(outdoorHum))
##          print("Attic: ", type(travelerTemp), type(travelerHum))
##          ('Indoor ', <type 'float'>, <type 'float'>)
##          ('Outdoor: ', <type 'float'>, <type 'unicode'>)
##          ('Attic: ', <type 'str'>, <type 'str'>)
            
            # Retype traveling sensor readings and correct bad reading if necessary.
            atticTemp = float(travelerTemp)
            if (atticTemp == 0.0):
                atticTemp = float(oldTravelerTemp)
                print( "Glitch for atticTemp ")
                
            atticHum = float(travelerHum)
            if (atticHum == 0.0):
                atticHum = float(oldTravelerHum)
                print( "Glitch for atticHum")
            
        except Exception as e:
            print( "Readline error ", arduinoString)
            print( str(e))
##  End of comment out while disconnected

##            To avoid this error:
##            Traceback (most recent call last):
##            File "/home/pi/Documents/PythonProjects/HTT/HTT_Unified.py", line 221, in <module>
##            arduinoString = ser.readline()
##            ValueError: need more than 1 value to unpack
##
## Sample error with traveler data, and indoorTemp/Hum in close proximity.
## Both error types appear to be handled sufficiently.
##('Traveler: ', '\n')
##('Readline error ', '\n')
##need more than 1 value to unpack
##2017-07-13 14:35:01, 77.7, 69.6, 81.0, 60, 96.0,40.8
##
##('Traveler: ', '96, 41.00\r\n')
##2017-07-13 14:38:02, 77.7, 69.8, 81.0, 59, 96.0,41.0
##
##Glitch for indoorTemp
##Glitch for indoorHum
##('Traveler: ', '96, 41.30\r\n')
##2017-07-13 14:41:05, 77.7, 69.8, 81.0, 59, 96.0,41.3            

        # Send weather data to InitialState bucket.
        #TODO create time value to preface streamer log data.
        try:
            streamer.log("Indoor Temp", indoorTemp)
            streamer.log("Indoor Hum", indoorHum)
            streamer.log("Outdoor Temp", outdoorTemp)
            streamer.log("Outdoor Hum", outdoorHum)
##            streamer.log("Attic Temp", atticTemp)
##            streamer.log("Attic Hum", atticHum)
            
        except Exception as e:
            print('Streamer.log error')
            print( str(e))  # Catch 'gaierror( -2, Name or service not known)'
                     
        # Display data on LCD
        # Step 1: Determine desired LCD brightness level.
        t = time.localtime().tm_hour
        if t in range(7,21): # daytime hours.
            bright = 64  # brightness level for day
        else:
            bright = 7   # brightness level for night
        setRGB(bright, bright, bright)
        
        # Step 2: Write summary to LCD

        # Step 2a: Create indoor data string
        lcdTemplate = 'In:{0:5.1f}deg {1:3.0f}%'
        indoorTemp = indoorTemp * 1.0
        indoorHum = indoorHum * 1.0
        # to avoid occasional run-time error, verify we are working with correct type
        # Occasionally this happens on startup, one time.
        if( type(indoorTemp) is float):
            lcdText = lcdTemplate.format(indoorTemp, indoorHum)
        else:
            lcdText = "Conversion err."
            
        # Step 2b:  Create outdoor data string.
        # Remove % character from outdoorHum as reported by Wunderground API
        if "%" in(outdoorHum):
           outdoorHum = outdoorHum[:len(outdoorHum)-1]
        outdoorTemplate =  'Out:{0:5.1f}deg {1:s}%'
        if( type(outdoorTemp) is float):
            lcdText += outdoorTemplate.format(outdoorTemp, outdoorHum)
        else:
            lcdText += "Conversion err."

        # Step 3: Write data string to LCD
        setText(lcdText)
        
        # Add data string video screen.
        currentTime = datetime.datetime.fromtimestamp(timeNow).strftime('%Y-%m-%d %H:%M:%S')
        screenTemplate = '{0:s},{1:5.1f}, {2:4.1f},{3:5.1f},{4:s},{5:4.1f},{6:4.1f}'
        screenText = screenTemplate.format(
            #currentTime + lcdText + " " + str(atticTemp) + " " + str(atticHum)
            currentTime,
            indoorTemp,
            indoorHum,
            outdoorTemp,  
            outdoorHum,
            atticTemp,
            atticHum
            )
        print(screenText)

        # Write info to daily weather file.
        fileTemplate = screenTemplate + "\n" #'{0:s},{1:5.1f}, {2:4.1f},{3:5.1f}, {4:s}, {5:4.1f},{6:4.1f}\n'
        fileText = fileTemplate.format(
            currentTime,
            indoorTemp,
            indoorHum,
            outdoorTemp,  
            outdoorHum,
            atticTemp,
            atticHum
            )
        fp=open(oldLogFileName, 'a')
        fp.write(fileText)
        fp.close()
        
        # For debugging, write JSON data.
##        UNIXtime = int( forecast["currently"]["time"])
##        current_dict = {
##           "time":UNIXtime,
##           "indoorT": temp,
##           "indoorRH" : hum,
##           "outdoorT" : round(forecast["currently"]["temperature"]),
##           "outdoorRH" : round( forecast["currently"]["humidity"]),
##           "windSpeed" : forecast["currently"]["windSpeed"],
##           "summary" : forecast["currently"]["summary"]
##           }
##        today.append(current_dict)
##        json.dump(current_dict, fp=open('HTTrecord.txt', 'w'), indent = 4)
                
        # Lastly, at midnight, save the day's data in its own log file and upload weather data to DropBox
        newLogFileTime = time.localtime()
        if( oldLogFileTime[2] != newLogFileTime[2]): # day number compare.
            yr = oldLogFileTime.tm_year
            mon = oldLogFileTime.tm_mon
            day = oldLogFileTime.tm_mday
            
            node = platform.node() # Identify platform in log file name.
            fnTemplate = "HTT_" + node + "_{0:4d}{1:02d}{2:02d}.csv"
            backupLogFileName = fnTemplate.format(yr, mon, day)
            print( "Saving daily log as " + backupLogFileName)
            oldLogFileTime = newLogFileTime
            try:
                # Rename original copy
                os.rename(oldLogFileName, backupLogFileName)

                # Copy to Dropbox
                # The dropbox_uploader script is generated by Excel macro outside this program.
                Process=Popen('~/Dropbox-Uploader/dropbox_uploader.sh upload %s ./Apps/%s' % (str(backupLogFileName), str(backupLogFileName)), shell=True)

            except OSError as e:
                print("Daily log error: " + str(e))
   
# Allow shutdown with button press in a headless system.  Button port is defined above
# This is the launcher.sh script, placed in /etc/rc.local to start this program.
#!/bin/sh
#launcher.sh
#Navigate to home directory, then to this directory, then execute python script.
#cd  /
#cd home/pi/Documents/PythonProjects/HTT
#sudo python HTT<program name>.py
#
        time.sleep(infoUploadInterval)
        streamer.flush()
            
##                debounce_count = 0
##                pilotState = True
##                pinMode( pilot_pin, "OUTPUT")
##                pinMode( sw_pin, "INPUT")
##                for loop in range(30):
##                    button_status = digitalRead( sw_pin)
##                    if (button_status != 0) and (debounce_count >= 2):
##                        call( ["sudo","shutdown","-h","now"]) # turn RPi OFF gracefully
##                        digitalWrite( pilot_pin, False)       # Redundant!
##                    debounce_count += 1
##                    digitalWrite( pilot_pin, pilotState)
##                    pilotState = not pilotState                 # blink
##                    time.sleep(1)
                
    #   End of Main Program Loop ... handle exceptions.                  
    except (IOError,TypeError) as e:
        print("Error " + str(e))
        time.sleep(forecastInterval)
               
streamer.close()
ser.close()
