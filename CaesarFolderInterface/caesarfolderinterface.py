from pydub import AudioSegment
import io
import os
class CaesarFolderInterface:
    def __init__(self) -> None:
        self.audio_input_folder = "CaesarAudioWAVs"
        self.notes_folder = "CaesarNotes"
        self.audio_output_folder = "CaesarAudioTranslations"
    def clean_all(self):
        try: 
            for i in os.listdir(self.audio_input_folder):
                os.remove(f"{self.audio_input_folder}/{i}")
            for i in os.listdir(self.notes_folder):
                os.remove(f"{self.notes_folder}/{i}")
            for i in os.listdir(self.audio_output_folder):
                os.remove(f"{self.audio_output_folder}/{i}")
    
        except Exception as ex:
            return False
    def store_audio(self,argfilename,contents):
        try:
            recording = AudioSegment.from_file(io.BytesIO(contents), format="mp3")
            recording.export(f'{self.audio_output_folder}/{argfilename}.mp3', format='mp3') 
            return True
        except Exception as ex:
            return False