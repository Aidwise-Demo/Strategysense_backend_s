import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Union, List, Dict, Any

import requests
import cloudinary
import cloudinary.uploader
from bson import ObjectId

from pydantic import BaseModel, ValidationError
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, HTTPException, Body, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from functions import Functions as f
from variables import process_clients as pc
from variables import extract_clients as ec
from variables import collection, collection1, collection2, collection3


# class Program(BaseModel):
#     _id: Optional[str] = None,
#     File_Name: Optional[str] = None,
#     Image_String: Optional[str] = None,
#     Project_Name: str
#     Context: Dict[str, Any]
#     Overview: Dict[str, Any]
#     Owner: Dict[str, Any]
#     Stakeholders: List[str]
#     Status: str
#     Initiative_Details: Dict[str, Any]
#     List_of_Sub_Initiatives: Optional[List[str]] = None
#     Interdependencies: List[Dict[str, Any]]
#     Risks_and_Mitigations: List[Dict[str, Any]]
#     Key_Performance_Indicators: List[Dict[str, Any]]
#     Budget: Optional[str] = None
#     Path: Optional[str] = None
#     DB_Id: Optional[str] = None
#     Skip: Optional[bool] = None
#     Extracted: Optional[str] = None
#     Summary: Optional[str] = None

class Program(BaseModel):
    _id: Union[str, ObjectId] = None
    File_Name: str = None
    Image_String: str = None
    Project_Name: Optional[str] = None
    Context: Optional[Union[str, Dict[str, Any]]] = None
    Overview: Optional[Union[str, Dict[str, Any]]] = None
    Owner: Optional[Union[str, Dict[str, Any]]] = None
    Stakeholders: Optional[Union[str, List[str]]] = None
    Status: Optional[str] = None
    Initiative_Details: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = None
    List_of_Sub_Initiatives: Optional[Union[str, List[str]]] = None
    Interdependencies: Optional[Union[str, List[Dict[str, Any]]]] = None
    Risks_and_Mitigations: Optional[Union[str, List[Dict[str, Any]]]] = None
    Key_Performance_Indicators: Optional[Union[str, List[Dict[str, Any]]]] = None
    Budget: Optional[str] = None
    Path: str = None
    DB_Id: str = None
    Skip: bool = None
    Extracted: str = None
    Summary: Optional[str] = None

class ItemList(BaseModel):
    file_ids: List[str]

class DeletionRequest(BaseModel):
    deletions: Dict[str, Any]

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your client's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cloudinary.config( 
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME_AIDWISE_DEMO'), 
    api_key = os.getenv('CLOUDINARY_API_KEY_AIDWISE_DEMO'), 
    api_secret = os.getenv('CLOUDINARY_API_SECRET_AIDWISE_DEMO'),
    secure=True
)

UPLOAD_FOLDER = 'Input'
Path("Uploaded Files").mkdir(parents=True,exist_ok=True)
Path("Output Files").mkdir(parents=True,exist_ok=True)

def ensure_folder_exists(folder_path):
    """Ensure that the folder exists, create it if it doesn't."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def serialize_doc(doc):
    # doc['DB_Id'] = str(doc['_id'])
    # del doc['_id']
    return doc

@app.get("/")
async def read_form():
    return {"Message": "Server is running"}
 
@app.post("/upload/files")
async def upload_files(files: List[UploadFile] = File(...)):
    
    ensure_folder_exists(UPLOAD_FOLDER)

    responses = []
    for file in files:

        if file.filename.endswith(".pdf"):

            pdf_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            
            with open(pdf_file_path, 'wb') as f:
                f.write(await file.read())
            
            upload_result = cloudinary.uploader.upload(pdf_file_path,resource_type="raw",public_id = file.filename,folder = "Uploaded_Files/")
            
            file_data = {
                "file_type": "PDF",
                "file_name": file.filename,
                "file_path": pdf_file_path,
                "URL": upload_result['secure_url'],
                "isextracted" : "No",
                "message": "PDF file received and saved."
            }

            inserted_document = await collection.insert_one(file_data)
            file_data["_id"] = str(inserted_document.inserted_id)

            responses.append(file_data)

        elif file.filename.endswith((".jpg", ".jpeg", ".png")):

            image_bytes = await file.read()
            image_file_path = os.path.join(UPLOAD_FOLDER, file.filename)

            with open(image_file_path, 'wb') as f:
                f.write(image_bytes)

            upload_result = cloudinary.uploader.upload(image_file_path,public_id = file.filename,folder = "Uploaded_Files/")
            
            file_data = {
                "file_type": "image",
                "file_name": file.filename,
                "file_extension": file.filename.split('.')[-1],
                "file_path": image_file_path,
                "URL": upload_result['secure_url'],
                "isextracted" : "No",
                "message": "Image received and saved.",
            }
            
            inserted_document = await collection.insert_one(file_data)
            file_data["_id"] = str(inserted_document.inserted_id)
            
            responses.append(file_data)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format for file {file.filename}")
    return responses

@app.get("/files")
async def get_uploaded_files():
    files = await collection.find().to_list(length=None)
    # Convert ObjectId to string
    for file in files:
        file["_id"] = str(file["_id"])
    return JSONResponse(content=files)

@app.post("/process")
async def process_file(file_ids: ItemList):

    pages = []
    file_ids = file_ids.file_ids

    for file_id in file_ids:

        file_data = {
                "file_type": "image",
                "Parent_ID": file_id,
                "Status": "Pending",
                "message": "Image received and saved.",
                    }
        await collection2.insert_one(file_data)

    for file_id in file_ids:

        document = await collection.find_one({"_id": ObjectId(file_id)})

        if not document:
            return {"message": f"File could not be found, maybe check ID: [{file_id}]"}
        
        await send_status_updates("Processing has started. Please wait...")

        if document and "URL" in document:

            await collection2.update_one({"Parent_ID": file_id}, {"$set": {"Status": "Processing"}})
            url = document['URL']

            if "file_type" in document:
                if document['file_type'] == "PDF":

                    outputpath = os.path.join("Output Files",f"{document['file_name']}")
                    response = requests.get(url)

                    if response.status_code == 200:

                        with open(outputpath, 'wb') as file:
                            file.write(response.content)

                        pages.append(await f.process_pdfs([outputpath],file_id))
                        await collection2.update_one({"Parent_ID": file_id}, {"$set": {"Status": "Completed"}})
                    
                    else: return {"Message": f"Failed to download PDF. HTTP status code: {response.status_code}"}
                elif document['file_type'] == 'image':

                    outputpath = os.path.join("Output Files",f"{document['file_name']}")
                    response = requests.get(url)

                    if response.status_code == 200:

                        with open(outputpath, 'wb') as file:
                            file.write(response.content)

                        pages.append(await f.process_images([outputpath],file_id))
                        await collection2.update_one({"Parent_ID": file_id}, {"$set": {"Status": "Completed"}})
                    
                    else: return {"Message": f"Failed to download image. HTTP status code: {response.status_code}"}
        else: return {"Message": f"URL Missing from File ID: {file_id}"}

    await send_status_updates("Processing complete!")
    await send_status_updates("Disconnecting all Connections !")
        
    for client in pc:
        await client.close()
    
    pc.clear()
    pages = [item for sublist in pages for item in sublist]
    print(pages)
    return pages

@app.get("/extract/{file_id}")
async def Extract_info(file_id:str):

    images = []
    records = await collection1.find({"Parent_ID": file_id}).to_list(length=None)

    if not records:
        return {"message": "Images could not be found to Extract Information"}

    if all(record['file_path'] == records[0]['file_path'] for record in records):
        records = [records[0]]
    print(records)

    await asyncio.ensure_future(send_status_updates("Extraction of Information Started!"))
    
    document = await collection.find_one({"_id": ObjectId(file_id)})
    print(document)
    if not document:
        return {"message": f"No document uploaded by this ID: {file_id}"}
    elif document and "isextracted" in document:
        if document['isextracted'] == "No":
            await collection.update_one({"_id": ObjectId(file_id)}, {"$set": {"isextracted": "Started"}})
        elif document['isextracted'] == "Yes":
            return {"message": "Extraction Already Finished for this document!"}           

    for document in records:
        if document and "Crop_URL" in document:
            
            url = document['Crop_URL']
            outputpath = os.path.join("Output Files",f"{document['file_name']}")
            response = requests.get(url)

            if response.status_code == 200:

                with open(outputpath, 'wb') as file:
                    file.write(response.content)

                data = {
                    "Path": outputpath,
                    "DB_Id": str(document['_id'])
                }

                images.append(data)
    print(images)
    await f.processPages(images)

    await collection.update_one({"_id": ObjectId(file_id)}, {"$set": {"isextracted": "Yes"}})

    await asyncio.ensure_future(send_status_updates("Extraction of Information Finished!"))
    await asyncio.ensure_future(send_status_updates("Disconnecting all Connections !"))
    
    for client in ec:
        await client.close()
    ec.clear()

    return {"message": "Extraction Finished."}

@app.get("/process/check/{file_id}")
async def get_records_by_parent_id(file_id: str):
    
    records = await collection2.find_one({"Parent_ID": file_id})
    
    if not records:
        raise HTTPException(status_code=404, detail="No records found")
    
    records["_id"] = str(records["_id"])
    
    return JSONResponse(content=records)

@app.get("/records/pageinfo/{parent_id}")
async def get_records_by_parent_id(parent_id: str):
    
    records = await collection1.find({"Parent_ID": parent_id}).to_list(length=None)
    
    if not records:
        raise HTTPException(status_code=404, detail="No records found")
    
    for file in records:
        file["_id"] = str(file["_id"])
    
    return JSONResponse(content=records)

@app.get("/records/pagedata/{file_id}")
async def get_records_by_parent_id(file_id: str):
    
    records = await collection3.find_one({"DB_Id": file_id})
    
    if not records:
        raise HTTPException(status_code=404, detail="No records found")
    
    records["_id"] = str(records["_id"])
    
    return JSONResponse(content=records)

# @app.get("/json/names")
# async def get_json_names():
    # json_files = []
    # # Iterate over files in the JSON directory
    # for filename in os.listdir("Output_JSON"):
    #     if filename.endswith(".json"):
    #         json_files.append(filename)
    # return {"json_files": json_files}

# @app.get("/json/{filename}")
# async def read_json(filename: str):
    # filepath = os.path.join("Output_JSON", filename)
    # if not os.path.isfile(filepath):
    #     raise HTTPException(status_code=404, detail="File not found")
    
    # with open(filepath, "r") as file:
    #     json_data = json.load(file)
    
    # return json_data

# CRUD Endpoint
@app.post("/CRUD", response_model=Program)
async def handle_program(data: Dict[str, Any] = Body(...)):
    
    action = data.get("action")
    payload = data.get("payload")

    if action == "create":
        
        result = collection3.insert_one(payload)
        new_program = collection3.find_one({"_id": result.inserted_id})
        
        return serialize_doc(new_program)

    if action == "update":
        
        if "DB_Id" not in payload:
            raise HTTPException(status_code=400, detail="DB_Id is required for update")
        
        program_id = payload.pop("DB_Id")
        result = await collection3.update_one({"DB_Id": program_id}, {"$set": payload})
        
        if result.modified_count == 1:
            
            updated_program = await collection3.find_one({"DB_Id": program_id})
            return serialize_doc(updated_program)
        
        raise HTTPException(status_code=404, detail="Program not found, or might not have been updated because no new changes were made in the payload")

    elif action == "delete":
        
        if "DB_Id" not in payload:
            raise HTTPException(status_code=400, detail="DB_Id is required for delete")
        
        result = await collection3.delete_one({"DB_Id": payload["DB_Id"]})
        
        if result.deleted_count == 1:
            return {"detail": "Program deleted"}
        
        raise HTTPException(status_code=404, detail="Program not found")
    
    elif action == "delete-keys":
        
        if "DB_Id" not in payload:
            raise HTTPException(status_code=400, detail="DB_Id is required for delete")
        
        try:
            deletion_request = DeletionRequest(deletions=payload['deletions'])
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.errors())
        
        program_id = payload.pop("DB_Id")
        program = await collection3.find_one({"DB_Id": program_id})
        
        if program:

            try:
                output = f.recursive_delete(program, deletion_request.deletions)
                
                copy1 = output.copy()
                del copy1['Image_String']
                print(copy1,"\n\n\n")
                
                # Update MongoDB with the modified output
                result = await collection3.replace_one({"DB_Id": program_id}, output)
                
                del output['Image_String']
                
                if result.modified_count == 0:
                    raise HTTPException(status_code=500, detail=f"Failed to update document with ID {program_id}")
            
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
            output["_id"] = str(output["_id"])              
        
        if not program:    
            raise HTTPException(status_code=404, detail="Program not found")
        
        print(output)
        return output
        # return {"message": "Deletions completed successfully", "data": output}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        

@app.delete("/delete_files")
async def delete_files(file_ids: ItemList):
    file_ids = file_ids.file_ids  
    for i,item in enumerate(file_ids):
            file_ids[i] = ObjectId(file_ids[i])
    try:
        # Delete files based on the provided file_ids
        result = await collection.delete_many({"_id": {"$in": file_ids}})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="No files found with the provided IDs")
        return {"message": f"Deleted {result.deleted_count} files"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/process-updates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pc.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pc.remove(websocket)

@app.websocket("/extraction-updates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ec.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ec.remove(websocket)

# def flatten_list(nested_list):
    # flattened_list = []
    # for item in nested_list:
    #     if isinstance(item, list):
    #         flattened_list.extend(flatten_list(item))
    #     else:
    #         flattened_list.append(item)
    # return flattened_list

async def send_status_updates(message: str):
    if pc:
        for client in pc:
            await client.send_text(message)
    if ec:
        for client in ec:
            await client.send_text(message)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=5273)