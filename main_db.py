#https://thepythoncode.com/article/translate-text-in-python?utm_content=cmp-true
import asyncio
import uvicorn
from fastapi import FastAPI,UploadFile,Form,WebSocket
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, AnyStr, List, Union
import starlette
from CaesarMobileTranslate.caesarmobiletranslate import CaesarMobileTranslate
from CaesarFolderInterface.caesarfolderinterface import CaesarFolderInterface
from CaesarMobileTranscribe.caesartranscribe import CaesarMobileTranscribe

from CaesarMobileTTS.caesarmobiletts import CaesarMobileTTS
from CaesarSQLDB.caesar_create_tables import CaesarCreateTables
from CaesarSQLDB.caesarhash import CaesarHash
from pydub import AudioSegment
app = FastAPI()
caesarfolders = CaesarFolderInterface()
caesarmobtrb = CaesarMobileTranscribe()

caesarcrud = CaesarCRUD()
caesarcreatetables = CaesarCreateTables()
caesarcreatetables.create(caesarcrud)
caesarmobtrb.create_all_dirs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class CaesarMobileTranslateReq(BaseModel):
    text:str
    dest:str

JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]
@app.get("/") # POST # allow all origins all methods.
async def home():
    return "Hello world to Caesar Mobile Translate."  
@app.post("/caesarmobiletranslate") # POST # allow all origins all methods.
async def caesarmobiletranslate(data : JSONStructure = None):  
    try:
        data = dict(data)#request.get_json()
        print(data)
        translation,dest,original,src = caesarmobtrb.caesartrans.translate(data["text"],data["dest"])

        return {"translation":translation,"dest":dest,"original":original,"src":src}
    except Exception as ex:
        return {"error":f"{type(ex)}-{ex}"}
@app.post("/caesarmobiletranslatestoreaudio")
async def caesarmobiletranslatestoreaudio(file: UploadFile,language:  str = Form()):
    # Increase Upload filesize: https://stackoverflow.com/questions/73442335/how-to-upload-a-large-file-%E2%89%A53gb-to-fastapi-backend
    filename = file.filename
    fileformat = filename.split(".")[1]
    suffix = f"_{language}"
    argfilename = filename.replace(".mp3","").replace(".wav","") + suffix
    contents = await file.read()
    fields = ("filename","src","dest","translationhash","original_transcript","translated_transcript","translated_audio_contents")
    table = "translations"
    hash_input = argfilename.replace(suffix,'') + language 
    translationhash = CaesarHash.hash_text(hash_input)
    condition = f"translationhash = '{translationhash}'"
    translation_exists = caesarcrud.check_exists(("*"),table,condition)
    caesarfolders.clean_all()
    if not translation_exists:
        store_res = caesarmobtrb.store_audio(argfilename,contents,fileformat)
        if store_res:
            return {"message":"audio stored in active directory."}
        else:
            return {"error":"Error storing."}
    else:
        return {"message":"translation already exists in db."}

@app.websocket("/caesarmobiletranslateaudiows")
async def caesarmobiletranslateaudio(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_json()
            filename = data["filename"]
            language = data["language"]
            fileformat = "wav"
            
            
            suffix = f"_{language}"
            argfilename = filename + suffix
            print(argfilename)
            
            fields = ("filename","src","dest","translationhash","original_transcript","translated_transcript","translated_audio_contents")
            table = "translations"
            hash_input = argfilename.replace(suffix,'') + language 
            translationhash = CaesarHash.hash_text(hash_input)
            condition = f"translationhash = '{translationhash}'"
            translation_exists = caesarcrud.check_exists(("*"),table,condition)
            ttsfilename = f"{caesarmobtrb.audio_output_folder}/{argfilename}.mp3"
            if not translation_exists:
                contents = caesarmobtrb.load_audio(argfilename,fileformat,caesarmobtrb.audio_input_folder)
                if contents:
                    new_sound = AudioSegment.empty()
                    original_text = ""
                    final_translation = ""
                    send_interval = 3 
                    sliced_sections = caesarmobtrb .slice_sections(argfilename)
                    for i,new_sound,dsrc,text,translation in caesarmobtrb.run_api(argfilename,language,sliced_sections,new_sound):
                        original_text += f"{text}\n"
                        final_translation += f"{translation}\n"
                        new_sound.export(ttsfilename, format="mp3")
                        current_contents = caesarmobtrb.load_audio(argfilename,"mp3",caesarmobtrb.audio_output_folder)

                        await websocket.send_json({"progress":i,"total":len(sliced_sections),"send_audio_interval":send_interval})
                        if i % send_interval == 0:
                            await websocket.send_bytes(current_contents)
                    
                    new_sound.export(ttsfilename, format="mp3")
                    final_contents = caesarmobtrb.load_audio(argfilename,"mp3",caesarmobtrb.audio_output_folder)
                    await websocket.send_bytes(final_contents)
                    # .encode('ascii')
                    original_text = original_text.replace("\n","<new_line>",100000)
                    original_text = original_text.encode('ascii',"ignore").decode()
                    original_text = original_text.replace("<new_line>","\n",100000)
                    
                    final_translation = final_translation.replace("\n","<new_line>",100000)
                    final_translation = final_translation.encode('ascii',"ignore").decode()
                    final_translation = final_translation.replace("<new_line>","\n",100000)
                    await websocket.send_json({"original_text":original_text})
                    await websocket.send_json({"final_translation":final_translation})
                    print({"message":"All translation audio was sent."})

                    await websocket.send_json({"message":"All translation audio was sent."})
                    
                    # Store db.
                    #print("src:",src)
                    #res = caesarcrud.post_data(fields,(f"{argfilename.replace(suffix,'')}.mp3",src,languag,translationhash,original_text,final_translation,contents),table)
                    
                    #if res:
                    #    await websocket.send_json({"message":"translation was stored."})
                    #else:
                    #    await websocket.send_json({"error":"translation was stored."})


                else:
                    await websocket.send_json({"error":"error loading file in active directory send request to caesarmobiletranslatestoreaudio."})
            else:
                res = caesarcrud.get_data(("filename","translated_audio_contents"),table,condition)
                if res:
                    resjson = res[0]
                    store_result = caesarfolders.store_audio(argfilename,resjson["translated_audio_contents"])
                    if store_result:
                        await websocket.send_bytes(store_result)

                    else:
                       await websocket.send_json({"error":"error GET storing"})
                        
                else:
                    await websocket.send_json({"error":"error whilst getting data,"})
            
    except starlette.websockets.WebSocketDisconnect as wed:
        if str(wed) == "1000":
            caesarfolders.clean_all()
            print("connected close handled.")
        else:
            print(type(wed),wed)
    


async def main():
    config = uvicorn.Config("main:app", port=7860, log_level="info",host="0.0.0.0",reload=True) # Local
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())