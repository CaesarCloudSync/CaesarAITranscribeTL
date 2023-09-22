from CaesarMobileTranscribe.caesartranscribe import CaesarMobileTranscribe
from CaesarMobileTranslate.caesarmobiletranslate import CaesarMobileTranslate
from CaesarMobileTTS.caesarmobiletts import CaesarMobileTTS
from CaesarFolderInterface.caesarfolderinterface import CaesarFolderInterface
from CaesarSQLDB.caesar_create_tables import CaesarCreateTables
from CaesarSQLDB.caesarcrud import CaesarCRUD
from CaesarSQLDB.caesarhash import CaesarHash
from pydub import AudioSegment
if __name__ == "__main__":
    argfilename = "DIALOGUE" # "audio-sample-1" #
    language = "fr"
    caesarfolders = CaesarFolderInterface()
    caesarmobtrb = CaesarMobileTranscribe()
    caesarmobtrans = CaesarMobileTranslate()
    caesarmobtts = CaesarMobileTTS()
    caesarcrud = CaesarCRUD()
    caesarcreatetables = CaesarCreateTables()
    caesarcreatetables.create(caesarcrud)


    fields = ("filename","src","dest","translationhash","original_transcript","translated_transcript","translated_audio_contents")
    table = "translations"
    hash_input = argfilename + language 
    translationhash = CaesarHash.hash_text(hash_input)
    condition = f"translationhash = '{translationhash}'"
    translation_exists = caesarcrud.check_exists(("*"),table,condition)
    new = AudioSegment.empty()
    new.export(f"{caesarfolders.audio_output_folder}/{argfilename}_start.mp3", format="mp3")