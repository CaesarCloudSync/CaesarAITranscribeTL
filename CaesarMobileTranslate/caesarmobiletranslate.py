#https://thepythoncode.com/article/translate-text-in-python?utm_content=cmp-true
from googletrans import Translator
from CaesarFolderInterface.caesarfolderinterface import CaesarFolderInterface
class CaesarMobileTranslate(CaesarFolderInterface):
    def __init__(self):
        super().__init__()
        self.translator = Translator()
    def translate(self,text,dest,verbose=0):
        # translate a spanish text to english text (by default)
        translation = self.translator.translate(text,dest=dest)
        if verbose == 1:
            print(f"{translation.origin} ({translation.src}) --> {translation.text} ({translation.dest})")
        return translation.text,translation.dest,translation.origin,translation.src

if __name__ == "__main__":
    caesarmobtrans = CaesarMobileTranslate()
    caesarmobtrans.translate("Hola Mundo","fr")