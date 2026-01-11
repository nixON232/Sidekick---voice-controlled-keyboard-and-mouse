'''
Sidekick
Copyright (C) 2021 UT-Battelle - Created by Sean Oesch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from vosk import Model, KaldiRecognizer
import os
import json
import audioop
import string
import math
from parsepackage import *

if not os.path.exists("model"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)

import pyaudio

parser = parser.Parser() 

def listToList(words):
    wordlist = '['
    for word in words:
        wordlist = wordlist + "\"" + word + "\"" + ","
    wordlist = wordlist.strip(",") + "]"    
    return wordlist

def setRec(state,crec,trec,arec):
    if state == "text":
        return trec
    elif state == "command" or state == "mouse":
        return crec
    else:
        return arec 

def clearRec(crec,trec,arec):
    crec.Result()
    trec.Result()
    arec.Result()

def stateSwap(nextstate,crec,trec,arec):
    rec = setRec(nextstate,crec,trec,arec)
    res = json.loads(rec.Result())
    swap = False
    if res["text"] != "":
        if swap:
            parser.ingest(res["text"]) 

        if res["text"] == nextstate:
            swap = True
    
    clearRec(crec,trec,arec)

def ingest(currentstate,crec,trec,arec):
    rec = setRec(currentstate,crec,trec,arec)
    res = json.loads(rec.Result()) # this not only returns the most accurate result, but also flushes the list of words stored internally
    if res["text"] != "":
        for text in res["text"].split(" "):
            if text in ["text","alpha","command"] and text != currentstate:
                parser.ingest(text)
                stateSwap(text,crec,trec,arec)
            else:
                parser.ingest(text) 
        
    clearRec(crec,trec,arec)

# create wordlist for our command model so that commands will be more accurately detected
commandwords = listToList(parser.nontextcommands)
alphavals = listToList(parser.alphavalues)

DEBUG = False  # Set to True for debug output including command buffer

def get_current_wordlist():
    if parser.state == "text":
        return []
    elif parser.state == "command" or parser.state == "mouse":
        return parser.nontextcommands
    else:
        return parser.alphavalues

def get_adaptive_buffer_size():
    if wait:
        return 400
    else:
        return 800

model = Model("model")
current_words = None
main_rec = None

def get_main_recognizer():
    global current_words, main_rec
    words = get_current_wordlist()
    if words != current_words or main_rec is None:
        if main_rec is not None:
            main_rec.Result()
        wordlist_str = listToList(words) if words else "[]"
        main_rec = KaldiRecognizer(model, 16000, wordlist_str)
        main_rec.SetPartialWords(True)
        current_words = words
    return main_rec

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=800)
stream.start_stream()

print("\nSidekick at your service. Please wait silently for the threshold to be set based on ambient noise before use.")

threshold_buffer = 1 # how many dB above ambient noise threshold will be set
thresholdset = False # whether or not threshold has been set
threshcount = 0 # count that determines when threshold is set
ambientvals = [] # Ambient noise level in dB is used to calculate appropriate threshold at which to send audio to vosk
wait = False # after threshold breached, need to process the next 5-10 audio samples through the model even if they don't breach threshold 
waittime = 0 # when to toggle wait from True to False 
while True:
    buffer_size = get_adaptive_buffer_size()
    data = stream.read(buffer_size, exception_on_overflow=False)

    # calculate decibels
    dB = 20 * math.log10(audioop.rms(data,2))

    # we want to set threshold based on ambient noise prior to processing audio data
    if not thresholdset: 
        ambientvals.append(int(dB))
        threshcount += 1
        if threshcount >= 10:
            thresholdset = True
            print("Your sidekick now awaits your command.")
            threshold = sum(ambientvals) / len(ambientvals) + threshold_buffer
            print("Threshold is now set at " + str(round(threshold,2)) + " dB.")
    
    # send audio data to model for processing when threshold breached and shortly afterward
    elif dB > threshold or wait == True:

        waittime += 1
        if dB > threshold:
            waittime = 0
            wait = True

        if waittime >= 5:
            wait = False

        rec = get_main_recognizer()
        rec_result = rec.AcceptWaveform(data)

        if len(data) == 0:
            break
        if rec_result:
            res = json.loads(rec.Result())
            if res["text"] != "":
                for text in res["text"].split(" "):
                    parser.ingest(text)
        else:
            partial_result = json.loads(rec.PartialResult())
            partial_text = partial_result.get("partial", "")
            if partial_text:
                print(f"\r[Partial] {partial_text}", end="", flush=True)



