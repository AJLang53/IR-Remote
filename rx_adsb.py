import RPi.GPIO as GPIO
from datetime import datetime
import time, math
from CPR import CPR
import argparse

def crc(msg, encode = False):
    GENERATOR = '1111111111111010000001001'
    msgbin = list(msg)
    
    if encode:
        msgbin[-24:] = ['0']*24

    for i in range(len(msgbin)-24):
        if msgbin[i] == '1':
            for j in range(len(GENERATOR)):
                msgbin[i+j] = str((int(msgbin[i+j])^int(GENERATOR[j])))

    reminder = ''.join(msgbin[-24:])
    return reminder

if __name__ == '__main__':
    # Handle the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('--local',help='Reference Position: Lat,Lon')
    args = vars(ap.parse_args())
    if args['local']:
        localLoc = True
        myLoc = args['local']
        myLoc = myLoc.split(',')
        myLoc = (float(myLoc[0]),float(myLoc[1]))
        print("Using locally unambiguous locating with reference "+str(myLoc)+'\n')

    else:
        localLoc = False
        print("Using globally unambiguous locating\n")

    # Set up the receiver pins and bit size
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.IN)
    bitSize = 225

    # Start the loop
    while True:
        lvl = 1

        # The receiver will drop its input to 0 when it receives
        while lvl:
            lvl = GPIO.input(18)

        startTime = datetime.now()

        raw = []
        received = ''

        nomOnes = 0
        previousLvl = 0
        started = False
        toggle = False

        while True:
            # If the lvl has changed, determine the pulse length
            if lvl != previousLvl:
                now = datetime.now()
                pulseLength = now - startTime
                startTime = now

                raw.append((previousLvl, pulseLength.microseconds))

                # Process the pulse to determine its bit representation
                if abs(pulseLength.microseconds - bitSize) < bitSize/2:
                    started = True

                if started:
                    if abs(pulseLength.microseconds - bitSize) < bitSize/2:
                        if previousLvl == 0 and toggle == False:
                            received+='1'
                        elif previousLvl == 1 and toggle == True:
                            received+='0'
                    elif abs(pulseLength.microseconds - (2*bitSize)) < bitSize/2:
                        if previousLvl == 1:
                            received+='0'
                            toggle = True
                        else:
                            received+='1'
                            toggle = False

            if lvl:
                numOnes = numOnes + 1

            else:
                numOnes = 0

            if numOnes > 10000:
                break

            # Update for the next loop
            previousLvl = lvl
            lvl = GPIO.input(18)

        # After each timeout or complete transmission, output results
        transTime = 0
        print "Raw:"
        for (lvl, pulse) in raw:
            print lvl, pulse
            transTime += pulse

        received=received[1:]

        # Parse the binary
        try:
            DF = int(received[0:5],2)
            EC = int(received[5:8],2)
            ICA024 = hex(int(received[8:32],2))
            data = received[32:88]
            TC = int(data[0:4],2)
            SS = int(data[4:5],2)
            NICsb = int(data[6],2)
            altCPR = data[7:19]
            T = int(data[20],2)
            cprOddEven = int(data[21],2)
            latCPR = int(data[22:39],2)*1.0     # Make lat and lon floats
            lonCPR = int(data[39:56],2)*1.0
            parity = received[88:]
        except:
            print("Error with received binary")

        checksum = crc(parity)
        if checksum != parity:  # Compare the checksums
            print("CORRUPTION")
        else:
            if DF == 17:
                if TC ==11:
                    if localLoc:    # If using local location, find immediately
                        # Get the Lat and Lon in degrees
                        loc = cpr.decodeLocal(myLoc, (latCPR,lonCPR),T)
                        altFeet = cpr.decodeAlt(altCPR)
                        print("Received Lat: "+str(loc[0]))
                        print("Received Lon: "+str(loc[1]))
                        print("Received Alt: "+str(altFeet))
                    else:   # Otherwise wait for both odd and even messages
                        if not (evenReady and oddReady):
                            if T:
                                evenLoc = (latCPR, lonCPR)
                                altCPR = cpr.decodeAlt(altCPR)
                                evenReady = True
                            else:
                                oddLoc = (latCPR, lonCPR)
                                altCPR = cpr.decodeAlt(altCPR)
                                oddReady = True
                        else:
                            loc = cpr.decodeGlobal(evenLoc, oddLoc)

                            print("Received Lat: "+str(loc[0]))
                            print("Received Lon: "+str(loc[1]))
                            print("Received Alt: "+str(altFeet))
                else:
                    print("Wrong Type Code")
            else:
                print("Wrong data format")
        