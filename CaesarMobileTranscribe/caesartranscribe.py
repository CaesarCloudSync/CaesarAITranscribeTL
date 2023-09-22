import os
import shutil
import sys
import numpy as np
# importing libraries 
import requests
import glob
import soundfile as sf
import speech_recognition as sr
from pydub import AudioSegment
import pydub
AudioSegment.converter = "/usr/bin/ffmpeg"
import io
from CaesarFolderInterface.caesarfolderinterface import CaesarFolderInterface
from CaesarMobileTranslate.caesarmobiletranslate import CaesarMobileTranslate
from CaesarMobileTTS.caesarmobiletts import CaesarMobileTTS
from tqdm import tqdm


def cosine_similarity(doc1,doc2):
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc1 = nlp(doc1)
    doc2 = nlp(doc2)
    similarity = np.dot(doc1.vector, doc2.vector) / (np.linalg.norm(doc1.vector) * np.linalg.norm(doc2.vector))
    return similarity
# create a speech recognition object
r = sr.Recognizer()

class CaesarMobileTranscribe(CaesarFolderInterface):
    def __init__(self) -> None:
        super().__init__()
        self.caesartrans = CaesarMobileTranslate()
        self.caesartts = CaesarMobileTTS()
    def create_all_dirs(self):
        if self.audio_input_folder not in os.listdir():
            os.mkdir(self.audio_input_folder)
        if self.notes_folder not in os.listdir():
            os.mkdir(self.notes_folder)
        if self.audio_output_folder not in os.listdir():
            os.mkdir(self.audio_output_folder)

        

        
    def store_audio(self,argfilename,contents,fileformat):
        try:
            recording = AudioSegment.from_file(io.BytesIO(contents)) # , format=fileformat
            recording.export(f'{self.audio_input_folder}/{argfilename}.wav', format='wav') 
            return True
        except Exception as ex:
            print(type(ex),ex)
            return False
        
        

    def send_revisionbank(self,sentences,txtfilename):
        boole = True
        while boole == True:
            sendrevisionbank = input("Send to RevisionBank: (y) or (n)").lower()
            if sendrevisionbank == "y":
                cardname = f'{txtfilename.split("/")[0]}/{txtfilename.split("/")[-1].replace(".txt","").capitalize()}'
                json = {"revisioncardscheduler":{"sendtoemail":"amari.lawal05@gmail.com","revisionscheduleinterval":60,"revisioncards":[{"subject":f"A-Level {cardname}","revisioncardtitle":cardname,"revisioncard":sentences}]}}
                loginjson = {"email":"amari.lawal05@gmail.com","password":"kya63amari"}
                try:
                    print("Logging in...")
                    access_token = requests.post("https://revisionbank.onrender.com/loginapi",json=loginjson).json()["access_token"]
                    headers = {"Authorization": f"Bearer {access_token}"}
                    print("Logged in.")
                except Exception as ex:
                    print("Login Failed.{}:{}".format(type(ex),ex))

                try:
                    print("Storing CaesarAI text...")
                    response = requests.post("https://revisionbank.onrender.com/storerevisioncards",json=json,headers=headers).json()
                    print("CaesarAI Stored.")
                except Exception as ex:
                    print("CaesarAI Text not stored.".format(type(ex),ex))
                boole = False
            elif sendrevisionbank == "n":
                boole = False
            else:
                boole = True

    def check_if_wav(self,argfilename):
        folder = self.audio_input_folder
        res = ""
        for i in os.listdir(folder):
            if argfilename in i :
                res += i
        if "wav" in res:
            return True
        else:
            return False

    def mp3_to_wav(self,src,dst):
        folder = self.audio_input_folder
        src = f"{folder}/{src}"
        dst = f"{folder}/{dst}"
        sound = AudioSegment.from_mp3(src)
        sound.export(dst, format="wav")
        os.remove(src)
    def check_file_exists(self,argfilename):
        folder =  self.notes_folder
        if folder in os.listdir():
            if f"{argfilename}.txt" in os.listdir(folder):
                return True
            else:
                return False
        else:
            return True

    def slice_sections(self,argfilename,largewav="large"):
                    
        filename = "{}/{}.wav".format(self.audio_input_folder,argfilename)
        sound = AudioSegment.from_wav(filename) 
        if self.notes_folder not in os.listdir():
            os.mkdir(self.notes_folder)

        if largewav == "small":
            sentences =""
            txtfilename = "{}/{}.txt".format(self.notes_folder,argfilename)
            with sr.AudioFile(filename) as source:
                # listen for the data (load audio to memory)
                audio_data = r.record(source)
                # recognize (convert from speech to text)
                text = r.recognize_google(audio_data)
                #print(text)
                with open(txtfilename,"w+") as f:
                    f.write(text)
                with open(txtfilename,"r") as f:
                    text = f.read()
                    textlist  = text.split("period")
                    #print(textlist)
                with open(txtfilename,"w+") as f:
                    for t in textlist:
                        sentence = f"{t.rstrip().lstrip()}.\n".capitalize()
                        #print(sentence)
                        sentences += f"{sentence}\n"
                        f.write(sentence)
                #print(textlist[0])
            #self.send_revisionbank(sentences,txtfilename)
            print(sentences)
        if largewav == "large": 
            sentences = ""

            duration  = sound.duration_seconds //60 
            # 7 seconds - 3 minutes
            #print(duration)
            
            minute_intervals = 0.5# 0.15 or 0.50 # TODO Try 1,2 and 3 and see which is the most optimized by seeing themost words/letters collected.
            percentages = [i * (minute_intervals/duration) for i in range(0,int(duration//minute_intervals))]
            #print(percentages)
            #percentages = [i/20 for i in range(0,20)]# 0.8
            

            # TODO Maximum audio time is 3.8 minutes, using percentage may be inconsistent if the audio duration increases.
            slicedsections =  [ sound[round(percentages[i] * len(sound)):round(percentages[i+1] * len(sound))] for i in range(len(percentages)-1) ]
            return slicedsections

    
    def run_api(self,argfilename,language_src,dest,slicedsections,new_sound,verbose=0):
            filename = "{}/{}.wav".format(self.audio_input_folder,argfilename)
            txtfilename = "{}/{}.txt".format(self.notes_folder,argfilename)
            folder_name = "audio-chunks"
            print("Starting...")


            for i, audio_chunk in enumerate(tqdm(slicedsections), start=1):
                # create a drectory to store the audio chunks
                if not os.path.isdir(folder_name):
                    os.mkdir(folder_name)
                print("Translating chunk{}.wav...".format(i))
                chunk_filename = os.path.join(folder_name, "chunk{}.wav".format(i))
                audio_chunk.export(chunk_filename, format="wav")
                with sr.AudioFile(chunk_filename) as source:
                    audio_listened = r.record(source)
                    # try converting it to text
                    try:
                        text = r.recognize_google(audio_listened,language=language_src)
                    except sr.UnknownValueError as e:
                        print("Error:", str(e))
                    else:
                        text = "{}. ".format(text.capitalize())
                        try:
                            with open(txtfilename,"a+",encoding="utf-8") as f:
                                f.write("{}\n".format(text))
                            with open(txtfilename,"r",encoding="utf-8") as f:
                                caesarnotesduplicate = f.readlines()
                        except UnicodeEncodeError as uex:
                            pass
                        try:
                            sim = cosine_similarity(caesarnotesduplicate[-1],caesarnotesduplicate[-2])
                            if sim > 0.95:
                                caesarnotesduplicate.remove(caesarnotesduplicate[-1])
                                try:
                                    with open(txtfilename,"w+",encoding="utf-8") as f:
                                        for word in caesarnotesduplicate:
                                            f.write(word)
                                except UnicodeEncodeError as uex:
                                    pass
                        except IndexError as iex:
                            pass
                        try:
                            print(chunk_filename, ":", text)
                            translation,dest,origin,src = self.caesartrans.translate(text,dest)
                            print(translation)
                            self.caesartts.run_tts(argfilename,translation,dest)
                            ttsfilename = f"{self.audio_output_folder}/{argfilename}.mp3"
                            sound = AudioSegment.from_mp3(ttsfilename) 
                            new_sound += sound
                            yield i,new_sound,src,text,translation

                            
                        except UnicodeEncodeError as uex:
                            pass
                try:
                    shutil.rmtree('audio-chunks')
                except FileNotFoundError as fex:
                    pass
            


    def clean_up_wav(self,argfilename):
        try:
            folder = self.audio_input_folder
            os.remove(f"{folder}/{argfilename}.wav")
            return True
        except Exception as ex:
            return False

    def clean_up_txt(self,argfilename):
        try:
            folder = self.notes_folder
            os.remove(f"{folder}/{argfilename}.txt")
            return True
        except Exception as ex:
            return False


    def load_transcription(self,argfilename):
        with open(f"{self.notes_folder}/{argfilename}.txt") as f:
            text = f.read()
        return text
    def load_audio(self,argfilename,fileformat,folder):
        print(f"{folder}/{argfilename}.{fileformat}")
        try:
            with open(f"{folder}/{argfilename}.{fileformat}","rb") as f:
                contents = f.read()
            return contents
        except FileNotFoundError as fex:
            return False


if __name__ == "__main__":
    caesarmbtr = CaesarMobileTranscribe()
    argfilename = "DIALOGUE_de"
    dest = "fr"
    ttsfilename_new = f"{caesarmbtr.audio_output_folder}/{argfilename}_new.mp3"
    new_sound = AudioSegment.empty()
    sliced_sections = caesarmbtr.slice_sections(argfilename)
    for i,new_sound in caesarmbtr.run_api(argfilename,dest,sliced_sections,new_sound):
        print(f"{i}:")
    
    new_sound.export(ttsfilename_new, format="mp3")
    



    
