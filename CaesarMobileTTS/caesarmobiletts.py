
from gtts import gTTS
from CaesarFolderInterface.caesarfolderinterface import CaesarFolderInterface
import os

class CaesarMobileTTS(CaesarFolderInterface):
    def __init__(self) -> None:
        super().__init__()
    def load_transcription(self,argfilename):
        with open(f"{self.audio_output_folder}/{argfilename}.mp3","rb") as f:
            contents = f.read()
        return contents

    def check_file_exists(self,argfilename):
        folder =  self.audio_output_folder
        if folder in os.listdir():
            if f"{argfilename}.mp3" in os.listdir(folder):
                return True
            else:
                return False
        else:
            return True
    def clean_up_tts(self,argfilename):
        try:
            folder = self.audio_output_folder
            os.remove(f"{folder}/{argfilename}.mp3")
            return True
        except Exception as ex:
            return False
                
    def run_tts(self,argfilename,text,language):
        try:
            myobj = gTTS(text=text, lang=language, slow=False)
            # Saving the converted audio in a mp3 file named
            # welcome
            if self.audio_output_folder not in os.listdir():
                os.mkdir(self.audio_output_folder)
            myobj.save(f"{self.audio_output_folder}/{argfilename}.mp3")
            # Playing the converted file
            #os.system("mpg321 welcome.mp3")
            worked = True
            error = None
        except Exception as ex:
            worked = False
            error = f"{type(ex)} - {ex}"
        return worked,error


