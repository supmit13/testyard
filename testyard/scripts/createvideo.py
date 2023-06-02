import os, sys, re, time
import datetime
import glob
import shutil
import random
import argparse

import simplejson as json
import subprocess
import numpy as np
import urllib, requests
import httplib2
from urllib.parse import urlencode
from fractions import Fraction
import math

import googleapiclient.discovery
from pytube import YouTube
from google.cloud import texttospeech
from google_auth_oauthlib.flow import InstalledAppFlow

# Libraries for Youtube video upload
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from oauth2client import client

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getcwd() + os.path.sep + "storymerge-775cc31bde1f.json"
#DEVELOPER_KEY = 'AIzaSyDK0xlWEzAf3IkE7WuKJYZnL-UWnDfHALw'
DEVELOPER_KEY = 'AIzaSyCjOk1a5NH26Qg-VYaFZW0RLJmDyVCnGQ8'

"""
Dependencies: ffmpeg, python3, GOOGLE_APPLICATION_CREDENTIALS, pytube, googleapiclient, api.video
Check requirements.txt for other python modules used.
"""



def v_concatmp4streams(mp4file_1, mp4file_2, mp4outfile):
    cmd = "ffmpeg -y -i %s -i %s -filter_complex \"[0:v] [1:v] concat=n=2:v=1 [v]\" -map \"[v]\" -pix_fmt yuv420p %s"%(mp4file_1, mp4file_2, mp4outfile)
    subprocess.call(cmd, shell=True)
    return mp4outfile


def va_concatmp4streams(mp4file_1, mp4file_2, mp4outfile):
    tmpfile1 = mp4file_1.split(".")[0] + "_concat.mp4"
    fi = open(mp4file_1, "rb")
    file1content = fi.read()
    fi.close()
    fo = open(tmpfile1, "wb")
    fo.write(file1content)
    fo.close()
    #cmd = "ffmpeg -y -i %s -i %s -filter_complex \"[0]scale=ceil(iw/2)*2:ceil(ih/2)*2[a];[1]scale=ceil(iw/2)*2:ceil(ih/2)*2[b]; [a][0:a][b][1:a]concat=n=2:v=1:a=1 [v] [a]\" -map \"[v]\" -map \"[a]\" -strict -2 -preset slow -pix_fmt yuv420p %s"%(tmpfile1, mp4file_2, mp4outfile)
    cmd = "ffmpeg -y -i %s -i %s -filter_complex \"[0]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v0];[1]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];[v0][0:a:0][v1][1:a:0]concat=n=2:v=1:a=1[v][a]\" -map \"[v]\" -map \"[a]\" -strict -2 -preset slow -pix_fmt yuv420p %s"%(tmpfile1, mp4file_2, mp4outfile)
    errcode = subprocess.call(cmd, shell=True)
    if errcode > 0: # Some error occurred during execution of the command
        return None
    # If mp4outfile exists and it size is > 0, then remove tmpfile1. Else, rename mp4file_1 to mp4outfile and remove tmpfile1.
    if os.path.exists(mp4outfile) and os.path.getsize(mp4outfile) > 0:
        os.unlink(tmpfile1)
    else:
        try:
            os.rename(mp4file_1, mp4outfile)
            os.unlink(tmpfile1)
        except:
            print("Error: %s"%sys.exc_info()[1].__str__())
            print("You will have temporary files in the system after this operation. Please remove them manually.")
    return mp4outfile


def getaudioduration(audfile):
    cmd = "ffprobe -v error -select_streams a:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 %s"%audfile
    try:
        outstr = subprocess.check_output(cmd, shell=True)
    except:
        print("Could not find the duration of '%s' - Error: %s"%(vidfile, sys.exc_info()[1].__str__()))
        return -1
    outstr = outstr.decode('utf-8')
    outstr = outstr.replace("\n", "").replace("\r", "")
    wspattern = re.compile("\s*", re.DOTALL)
    outstr = wspattern.sub("", outstr)
    if outstr == 'N/A':
        outstr = 0
    durationinseconds = float(outstr)
    return durationinseconds



def addvoiceoveraudio(inputmp4, audiofiles, outputmp4, timeslist):
    infilestr = ""
    delaystr = ""
    mixstr = ""
    delayctr = 1
    tctr = 0
    numfiles = audiofiles.__len__()
    for audiofile in audiofiles:
        infilestr += "-i %s "%audiofile # Note the space after '%s'. It is required.
        try:
            timeofstart = math.ceil(Fraction(timeslist[tctr])) * 1000
        except:
            continue
        delaystr += "[%s]adelay=%s[s%s];"%(delayctr, timeofstart, delayctr)
        mixstr += "[s%s]"%delayctr
        dur = getaudioduration(audiofile) * 1000
        availabletime = 0
        try:
            nexttimeofstart = math.ceil(Fraction(timeslist[tctr+1])) * 1000
            availabletime = nexttimeofstart - timeofstart
            if availabletime < dur:
                outaudiofile = audiofile.split(".")[0] + "_cut.wav"
                # Cut the audio file to make dur = availabletime
                cutcmd = "ffmpeg -y -ss 00 -i %s -to %s -c copy %s"%(audiofile, availabletime, outaudiofile)
                subprocess.call(cutcmd, shell=True)
                if os.path.exists(outaudiofile):
                    os.unlink(audiofile)
                    os.rename(outaudiofile, audiofile)
                else:
                    print("Couldn't find resized audio file.")
        except:
            print("Error while trying to cut audio file: %s"%sys.exc_info()[1].__str__())
        delayctr += 1
        tctr += 1
    cmd = "ffmpeg -y -i %s %s -max_muxing_queue_size 9999 -filter_complex \"%s%samix=%s[a]\" -map 0:v -map \"[a]\" -preset ultrafast %s"%(inputmp4, infilestr, delaystr, mixstr, numfiles, outputmp4)
    try:
        subprocess.call(cmd, shell=True)
    except:
        print("Error in '%s' : %s"%(cmd, sys.exc_info()[1].__str__()))
    return outputmp4


def getaudiofromtext(textstr):
    voiceurl = "https://regios.org/wavenet/wavenet-gen.php"
    postdict = {"input" : textstr}
    postdata = urlencode(postdict) # Need to do this to get the length of the content
    httpheaders = {'accept' : 'audio/mpeg', 'accept-encoding' : 'gzip,deflate'}
    httpheaders['content-length'] = str(postdata.__len__())
    response = requests.post(voiceurl, data=postdict, headers=httpheaders, stream=True)
    if response.status_code == 200:
        outaudiofile = time.strftime("%Y%m%d%H%M%S_wavenet_audio",time.localtime()) + ".mp3"
        out = open(outaudiofile, "wb")
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, out)
        out.close()
        print("Successfully retrieved audio file")
    else:
        return None
    return outaudiofile



def getaudiofromtext_google(textstr):
    wavenet_api_key = "5e1a71620551d6fe8f65bc7f0790c52f34bf2f16"
    #wavenet_api_key = "ffcdb1dc5dff7b6ee0a6559b533c04ab6716b874"
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=textstr)
    # British male voice options: en-GB-Wavenet-B, en-GB-Wavenet-D, en-GB-Standard-B, en-GB-Standard-D . Code for all of them is en-GB.
    voice = texttospeech.VoiceSelectionParams(language_code="en-GB", name="en-GB-Wavenet-B", ssml_gender=texttospeech.SsmlVoiceGender.MALE)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    outaudiofile = time.strftime(os.getcwd() + os.path.sep + "videos" + os.path.sep + "%Y%m%d%H%M%S",time.localtime()) + ".wav"
    if os.path.exists(outaudiofile):
        datetimepattern = re.compile("^([\w\/\\_\-]+)[\\\/]{1}(\d{14})$")
        dps = re.search(datetimepattern, outaudiofile.split(".")[0])
        if dps:
            basedir = dps.groups()[0]
            filename = dps.groups()[1]
            outaudiofile = basedir + os.path.sep + str(int(filename) + 1) + ".wav"
        else:
            outaudiofile = outaudiofile.split(".")[0] + "_2.wav"
    with open(outaudiofile, "wb") as out:
        out.write(response.audio_content)
    print('Audio content written to file "%s"'%outaudiofile)
    return outaudiofile


def getaudiofromtext_google_2(textstr):
    url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
    data = { "input": {"text": textstr}, "voice": {"name":  "en-GB-Wavenet-B", "languageCode": "en-GB"}, "audioConfig": {"audioEncoding": "LINEAR16"} };
    headers = {"content-type": "application/json", "X-Goog-Api-Key": "ffcdb1dc5dff7b6ee0a6559b533c04ab6716b874", "Authorization" : "Bearer ffcdb1dc5dff7b6ee0a6559b533c04ab6716b874" }
    r = requests.post(url=url, json=data, headers=headers)
    content = r.content
    outaudiofile = time.strftime(os.getcwd() + os.path.sep + "videos" + os.path.sep + "%Y%m%d%H%M%S",time.localtime()) + ".wav"
    if os.path.exists(outaudiofile):
        datetimepattern = re.compile("^([\w\/\\_\-]+)[\\\/]{1}(\d{14})$")
        dps = re.search(datetimepattern, outaudiofile.split(".")[0])
        if dps:
            basedir = dps.groups()[0]
            filename = dps.groups()[1]
            outaudiofile = basedir + os.path.sep + str(int(filename) + 1) + ".wav"
        else:
            outaudiofile = outaudiofile.split(".")[0] + "_2.wav"
    with open(outaudiofile, "wb") as out:
        out.write(content)
    print('Audio content written to file "%s"'%outaudiofile)
    return outaudiofile


if __name__ == "__main__":
    pass
    


