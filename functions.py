import os
import time
import json
import shutil
import base64
import asyncio
import cloudinary
import numpy as np
from PIL import Image
from typing import Dict, Any
from dotenv import load_dotenv
from variables import claude_client as client
from fastapi import HTTPException
from variables import Prompts as p
from pdf2image import convert_from_path
from variables import extract_clients as ec
from variables import initialize_project_info as ipi
from variables import collection, collection1, collection2, collection3
import cloudinary.uploader

load_dotenv()


cloudinary.config( 
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME_GRAVITY'), 
    api_key = os.getenv('CLOUDINARY_API_KEY_GRAVITY'), 
    api_secret = os.getenv('CLOUDINARY_API_SECRET_GRAVITY'),
    secure=True
)

class Process_Structure:
    @staticmethod
    def Context(self ,string ,dummy = 0):

        items = string.split('|')
        result_dict = {}

        for item in items:
            key, value = item.split(':')
            result_dict[key.strip()] = value.strip()

        return result_dict
    
    @staticmethod
    def Owner(self ,string ,dummy = 0):

        items = string.split('|')
        result_dict = {}

        for item in items:
            key, value = item.split(':')
            if len(value.split(',')) > 1:
                result_dict[key.strip()] = value.strip().split(',')
            else:
                result_dict[key.strip()] = value.strip()

        return result_dict
    
    @staticmethod
    def Stakeholders(self ,string ,dummy = 0):

        items = string.split('|')
        return items[1:-1]
    
    @staticmethod
    def Overview(self ,string ,dummy = 0):

        items = string.split('|')
        result_dict = {}

        for item in items:
            key, value = item.split(':')
            result_dict[key.strip()] = value.strip()

        return result_dict
    
    @staticmethod
    def Initiative_Details(self ,string ,dummy = 0):

        # Split the string based on pipe
        items = string.split('|')
        result_dict = {}

        # Find the index of the element containing 'Key deliverables' or 'Key outcomes'
        index = next((i for i, s in enumerate(items) if 'Key deliverables' in s or 'Key outcomes' in s or 'Deliverables' in s), None)
        # Combine the list elements from the found keyword element onwards
        combined_text = '|'.join(items[index:])

        items = [items[0],combined_text]
        print(items)
        for item in items:
            key, value = item.split(':',1)
            if key.strip() in ['Key deliverables','Key outcomes','Deliverables'] and '|' in item:
                result_dict[key.strip()] = value.strip().split('|')
            elif key.strip() in ['Key deliverables','Key outcomes','Deliverables'] and '|' not in item:
                result_dict[key.strip()] = value.strip().split(',')
            else:
                result_dict[key.strip()] = value.strip()
        return result_dict
    
    @staticmethod
    def List_of_Sub_Initiatives(self ,string ,dummy = 0):
        if string[0] == '|' and string[-1] == '|':
            string =  string[1:-1]
        elif string[0] == '|':
            string =  string[1:]
        elif string[-1] == '|':
            string =  string[:-1]
        items = string.split('|')
        return items

    @staticmethod
    def Interdependencies(self ,string ,dummy = 0):
        if string[0] == '|' and string[-1] == '|':
            string =  string[1:-1]
        elif string[0] == '|':
            string =  string[1:]
        elif string[-1] == '|':
            string =  string[:-1]
        items = string.replace('\n','|').split('|')
        items = [element for element in items if element != ""]
        result = []
        keys = items[:2]
        items = items[2:]
        print(items)
        dic = {key: '' for key in keys}

        for i in range(0,len(items),2):

            dic = {key: '' for key in keys}
            for j,key in enumerate(list(dic.keys())):

                if j == 0:
                    dic[key] = items[i]
                else:
                    dic[key] =  items[i+1]
            result.append(dic)

        if len(items) % 2 != 0:
            return "Not Found!"
        
        return result
    
    @staticmethod
    def Risks_and_Mitigations(self ,string ,dummy = 0):

        items = string.replace('\n','|').split('|')
        result = []
        keys = items[:2]
        items = items[2:]
        dic = {key.strip(): '' for key in keys}
        for i in range(0,len(items),2):

            dic = {key.strip(): '' for key in keys}
            for j,key in enumerate(list(dic.keys())):

                if j == 0:
                    dic[key] = items[i].strip()
                else:
                    dic[key] =  items[i+1].strip()
            result.append(dic)

        if len(items) % 2 != 0:
            return "Not Found!"
        
        return result
    
    @staticmethod
    def Key_Performance_Indicators(self, string, dummy=0):
        print(string)
        try:
            # First attempt to parse the JSON string directly
            parsed = json.loads(string)
        except json.JSONDecodeError:
            # If parsing fails, try to wrap the string in braces and parse again
            try:
                wrapped_string = f'{{ {string} }}'
                parsed = json.loads(wrapped_string)
            except json.JSONDecodeError as e:
                # If it still fails, raise the exception or handle it as needed
                print(f"Failed to parse JSON after wrapping: {e}")
                raise e
        
        # Check for nested "Key_Performance_Indicators" and flatten if necessary
        if 'Key_Performance_Indicators' in parsed and isinstance(parsed['Key_Performance_Indicators'], dict):
            nested_kpi = parsed['Key_Performance_Indicators'].get('Key_Performance_Indicators')
            if nested_kpi:
                parsed['Key_Performance_Indicators'] = nested_kpi

        return parsed

class API:
    def process():
        
        ...
    ...

class Functions:
    @staticmethod
    def crop(img_paths, top = 1500,bottom = 1500):
        for i,img in enumerate(img_paths):
            # img_paths[i] = Functions.crop_image(imgpath,top,bottom)
            # img['Path'] = Functions.crop_blank_space(img['Path'])
            img_paths[i] = Functions.crop_blank_space(img)
        print("Image has been Cropped!")
        return img_paths
            
    @staticmethod
    def delete_directory(directory_path):
        try:
            shutil.rmtree(directory_path)
            print(f"Directory '{directory_path}' and its contents successfully deleted.")
        except OSError as e:
            print(f"Error: {directory_path} : {e.strerror}")

    @staticmethod
    def pdf_to_img(pdf_path, img_quality=100,dpi = 600):
        # if os.path.exists("Output_Images"):
        #     Functions.delete_directory("Output_Images")

        # if os.path.exists("Cropped_Images"):
        #     Functions.delete_directory("Cropped_Images")
        
        if not os.path.exists("Output_Images"):
            os.makedirs("Output_Images")

        if not os.path.exists("Cropped_Images"):
            os.makedirs("Cropped_Images")

        print("PDF is being Converted to Images!")
        pages = convert_from_path(pdf_path,dpi = dpi)

        img_paths = []
        for i, page in enumerate(pages):
            img_path = os.path.join("Output_Images", f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.png")
            page.save(img_path, "PNG", quality=img_quality)
            img_paths.append(img_path)

        return img_paths

    @staticmethod
    def crop_image(image_path, top_pixels=1500, bottom_pixels=1500):
        img = Image.open(image_path)
        width, height = img.size

        cropped_img = img.crop((0, top_pixels, width, height - bottom_pixels))
        savepath = os.path.join("Cropped_Images" ,os.path.basename(image_path))
        cropped_img.save(savepath)
        return savepath
    
    @staticmethod
    def crop_blank_space(image_path):
        with Image.open(image_path) as img:
            # Convert the image to grayscale
            img_gray = img.convert('L')
            
            # Convert the image to a NumPy array
            img_array = np.array(img_gray)
            
            # Find the first non-white (non-zero) row from the top
            top_non_white_rows = np.where(img_array != 255)[0]
            
            # Find the last non-white (non-zero) row from the bottom
            bottom_non_white_rows = np.where(img_array[::-1] != 255)[0]
            
            # Calculate the amount of pixels cropped from the top and bottom
            pixels_cropped_top = top_non_white_rows[0] if top_non_white_rows.size > 0 else 0
            pixels_cropped_bottom = bottom_non_white_rows[0] if bottom_non_white_rows.size > 0 else 0
            
            # Crop the image based on the calculated pixel amounts
            cropped_img = img.crop((0, pixels_cropped_top, img.width, img.height - pixels_cropped_bottom))
            
            print(f"\nImage [{os.path.basename(image_path)}] has been Cropped!")
            print(f"Pixels cropped from the top: {pixels_cropped_top}")
            print(f"Pixels cropped from the bottom: {pixels_cropped_bottom}")
            
            # Save the cropped image as PNG with high DPI
            # cropped_img.save('cropped_image.png', dpi=(300, 300))
            savepath = os.path.join("Cropped_Images/", os.path.basename(image_path))
            cropped_img.save(savepath, dpi=(300, 300))
            
            return savepath

    @staticmethod
    def ClaudeOutput(imgpath, prompt):
        with open(imgpath, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        image_media_type = "image/png"
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )
        return message.content[0].text
    
    # @staticmethod
    # def ClaudeOutput(imgpath, prompt):
    #     with open(imgpath, "rb") as image_file:
    #         image_data = base64.b64encode(image_file.read()).decode("utf-8")
    #     image_media_type = "image/png"
        
    #     message = client.chat.completions.create(
    #         model="gpt-4o-2024-08-06",
    #         max_tokens=2000,
    #         temperature=0,
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": [
    #                     {
    #                         "type": "image_url",
    #                         "image_url": {
    #                                     "url": f"data:{image_media_type};base64,{image_data}",
    #                                     "detail":"high"
    #                         },
    #                     },
    #                     {
    #                         "type": "text",
    #                         "text": prompt
    #                     }
    #                 ],
    #             }
    #         ],
    #     )
    #     return message.choices[0].message.content
    
    
    @staticmethod
    def recursive_delete(data: Any, deletions: Dict[str, Any]):
        
        protected_keys = ["_id", "File_Name", "Image_String","Path", "DB_Id", "Skip", "Extracted"] 
        
        if not isinstance(deletions, dict):
            raise HTTPException(status_code=400, detail="Invalid deletions format")

        for key, value in deletions.items():
            
            if key in protected_keys:
                raise HTTPException(status_code=400, detail=f"Cannot delete protected key: {key}")

            if key not in data:
                raise HTTPException(status_code=404, detail=f"Key not found: {key}")
            
            if value is None:
                del data[key]
            
            elif key not in ["Interdependencies","Risks_and_Mitigations","Key_Performance_Indicators"]:
                
                if isinstance(value, list):
                    
                    if isinstance(data[key], list):
                        
                        # Delete specific indices in a list
                        for index in sorted(value, reverse=True):
                            
                            if not isinstance(index, int):
                                raise HTTPException(status_code=400, detail="List index must be an integer")
                            
                            if index < 0 or index >= len(data[key]):
                                raise HTTPException(status_code=400, detail="List index out of range")
                            
                            data[key].pop(index)
                    
                    elif isinstance(data[key], dict):
                        
                        # Delete specific sub-keys in a dictionary
                        for sub_key in value:
                            
                            if sub_key in data[key]:
                                del data[key][sub_key]
                            
                            else:
                                raise HTTPException(status_code=404, detail=f"Sub-key {sub_key} not found in {key}")
                    else:
                        raise HTTPException(status_code=400, detail="Invalid data type for deletions")
                
                elif isinstance(value, dict):
                    
                    # Recursively delete nested dictionary keys or list elements
                    if isinstance(data[key], dict):
                        Functions.recursive_delete(data[key], value)
                    
                    elif isinstance(data[key], list):
                        
                        for index, sub_deletions in value.items():
                            
                            if not isinstance(index, int):
                                raise HTTPException(status_code=400, detail="List index must be an integer")
                            
                            if index < 0 or index >= len(data[key]):
                                raise HTTPException(status_code=400, detail="List index out of range")
                            
                            if isinstance(sub_deletions, dict):
                                Functions.recursive_delete(data[key][index], sub_deletions)
                            
                            else:
                                raise HTTPException(status_code=400, detail="Invalid deletions format for list elements")
                else:
                    raise HTTPException(status_code=400, detail="Invalid deletions format")
            
            elif key in ["Key_Performance_Indicators"]:
                
                if not isinstance(value, dict):
                    raise HTTPException(status_code=400, detail="Invalid deletions format")
                   
                print(value)
                if 'kpi_type' in value and 'index' in value and 'Targets' in value:
                    
                    if value["kpi_type"] is None:
                        raise HTTPException(status_code=400, detail="kpi_type cannot be null")
                
                    if not isinstance(value["kpi_type"],str):
                        raise HTTPException(status_code=400, detail="kpi_type must be str")
                
                    if value['Targets'] is None:
                        
                        if value['index'] is None:
                            
                            if value['kpi_type'].lower() not in ['main kpi','support kpi']:
                                raise HTTPException(status_code=400, detail="Invalid KPI type!")
                            else:

                                for i,item in enumerate(data[key]):
                                    
                                    if value['kpi_type'].lower() == item['kpi_type'].lower():
                                        data[key].pop(i)
                        else:
                            
                            if not isinstance(value["index"], list):
                                raise HTTPException(status_code=400, detail="index must be a list or null")
                            
                            for index in value["index"]:
                                
                                if not isinstance(index, int):
                                    raise HTTPException(status_code=400, detail="List index must be an integer")
                                
                                for i,item in enumerate(data[key]):
                                    
                                    if value['kpi_type'].lower() == item['kpi_type'].lower():
                                        
                                        if index < 0 or index >= len(data[key][i]["data"]):
                                            raise HTTPException(status_code=400, detail="List index out of range")
                                        else:
                                            data[key][i]["data"].pop(index)
                    else:
                        if not isinstance(value["index"], list):
                            raise HTTPException(status_code=400, detail="index must be a list or null")
                        
                        if len(value["index"]) != 1:
                            raise HTTPException(status_code=400, detail="if Targets is not null, index must only contain one item")
                            
                        for index in value["index"]:
                            
                            if not isinstance(index, int):
                                raise HTTPException(status_code=400, detail="List index must be an integer")
                            
                            for i,item in enumerate(data[key]):
                                
                                if value['kpi_type'].lower() == item['kpi_type'].lower():
                                    
                                    if index < 0 or index >= len(data[key][i]["data"]):
                                        raise HTTPException(status_code=400, detail="List index out of range")
                                    
                                    else:
                                        
                                        for target in value["Targets"]:
                                            
                                            val = data[key][i]["data"][index]["Targets"].pop(target, None)
                                            
                                            if val is None:
                                                raise HTTPException(status_code=400, detail=f"Invalid Targets Value: [{target}]")               
                else:
                    raise HTTPException(status_code=400, detail="Missing Keys in payload")
            else:
                # Mycode
                print(value)
                
                if isinstance(value, list):
                    
                    if isinstance(data[key], list):
                        
                        # Delete specific indices in a list
                        for index in sorted(value, reverse=True):
                            
                            if not isinstance(index, int):
                                raise HTTPException(status_code=400, detail="List index must be an integer")
                            
                            if index < 0 or index >= len(data[key]):
                                raise HTTPException(status_code=400, detail="List index out of range")
                            
                            data[key].pop(index)
                
                elif isinstance(value, dict):
                    
                    # Delete specific sub-keys in a dictionary
                    if 'index' in value and 'key' in value:
                        
                        if isinstance(value['index'], list) and isinstance(value['key'], list):
                           
                            if len(value['index']) != len(value['key']):
                                raise HTTPException(status_code=400, detail="List length mismatch")
                          
                            for i,item in enumerate(value['index']):
                                
                                if not isinstance(item, int):
                                    raise HTTPException(status_code=400, detail="index list must be an integer")
                                
                                else:
                                    
                                    if item < 0 or item >= len(data[key]):
                                        raise HTTPException(status_code=400, detail="List [index] out of range")
                                    
                                    if not isinstance(value['key'][i], str):
                                        raise HTTPException(status_code=400, detail="Key must be a string")
                                    
                                    # print("\ndata key: ",data[key])
                                    data[key][item].pop(value['key'][i])
                        else:
                            raise HTTPException(status_code=400, detail="the keys must be a list")
                    else:
                        raise HTTPException(status_code=404, detail=f"Index or Key Missing!")
                else:
                    raise HTTPException(status_code=400, detail="Invalid data type for deletions")

        return data
    
    @staticmethod
    def check_file_type(file_path):
        file_extension = os.path.splitext(file_path)[1].lower()

        # Check if it's a PDF or an image file
        if file_extension == ".pdf":
            return "PDF"
        elif file_extension in (".jpg", ".jpeg", ".png", ".gif", ".bmp"):
            return "Image"
        else:
            return "Unknown"
    
    @staticmethod
    def upscale(image_path: str, output_directory: str = "Output_Images", default_dpi=72) -> str:
        # Open the image file
        img = Image.open(image_path)
        target_dpi = 600
        target_size = (5100, 6600)
        # Check if the image dimensions fall within the specified range
        if img.width == 5100 and 2600 <= img.height <= 2800:
            # No resizing needed, keep the original size
            upscaled_img = img
        else:
            # Resize the image
            upscaled_img = img.resize(target_size)

        # Get the base name of the original image
        _, filename = os.path.split(image_path)
        # Add "Image_" prefix to the file name
        new_filename = "Image_" + filename
        # Join the output directory and the new file name to get the full path
        new_image_path = os.path.join(output_directory, new_filename)
        print(new_image_path)
        # Save the upscaled image to the new directory
        upscaled_img.save(new_image_path,dpi = (target_dpi,target_dpi))

        return new_image_path  

    @staticmethod
    def convert_to_png(image_path):

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, image_path)

        img = Image.open(image_path)
        file_extension = os.path.splitext(image_path)[1].lower()
        # print(file_extension)

        # If the file is not in PNG format, convert it to PNG
        if file_extension != ".png":
            # Create a new file path with PNG extension
            new_image_path = os.path.splitext(image_path)[0] + ".png"
            img.save(new_image_path, "PNG")
            print(f"Image converted to PNG and saved at {new_image_path}")
            return new_image_path
        else:
            return image_path

    @staticmethod
    def img_str(img):
        with open(img, "rb") as image_file:
            image_data = image_file.read()
        base64_encoded_image = base64.b64encode(image_data).decode("utf-8")
        return base64_encoded_image
    
    @staticmethod
    def insert_at_index(dictionary, key, value, index):
        items = list(dictionary.items())
        items.insert(index, (key, value))
        return dict(items)

    @staticmethod
    async def send_status_updates(message: str, clients=ec):
        tasks = [client.send_text(message) for client in clients]
        await asyncio.gather(*tasks)

    @staticmethod
    async def process_pdfs(pdfs,file_id):
            print("pdfs:   ",pdfs)
            if pdfs:
                pages = []
                await Functions.send_status_updates("PDF(s) are being converted to images.")
                for pdf in pdfs:
                    await Functions.send_status_updates(f"{os.path.basename(pdf)} is being converted to images.")
                    img_paths = Functions.pdf_to_img(pdf, img_quality=100)
                    await Functions.send_status_updates(f"{os.path.basename(pdf)} has been converted to images.")
                    await Functions.send_status_updates(f"Images of {os.path.basename(pdf)} are Being uploaded to DB.")
                    for img_path in img_paths:

                        upload_result = cloudinary.uploader.upload(img_path,public_id = os.path.basename(img_path),folder = "Pages/")
                        upload_result1 = cloudinary.uploader.upload(Functions.crop([img_path])[0],public_id = os.path.basename(img_path),folder = "Cropped_Pages/")

                        file_data = {
                            "file_type": "image",
                            "file_name": os.path.basename(img_path),
                            "file_extension": os.path.basename(img_path).split('.')[-1],
                            "file_path": img_path,
                            "Org_URL": upload_result['secure_url'],
                            "Crop_URL": upload_result1['secure_url'],
                            "Parent_ID": file_id,
                            "message": "Image received and saved.",
                        }

                        inserted_document = await collection1.insert_one(file_data)
                        file_data["_id"] = str(inserted_document.inserted_id)
                        pages.append(file_data)
                    await Functions.send_status_updates(f"Images of {os.path.basename(pdf)} Have been uploaded to DB.")
                # Send a message indicating the progress
                await Functions.send_status_updates("All PDF(s) have been converted to images.")
                return pages
            else:
                await Functions.send_status_updates("No PDF's to Process.")
                img_paths = []
    @staticmethod
    async def process_images(images,file_id):
        
            if not os.path.exists("Output_Images"):
                os.makedirs("Output_Images")

            if not os.path.exists("Cropped_Images"):
                os.makedirs("Cropped_Images")
            
            print("Images:   ",images)
            
            if images:
                pages = []
                await Functions.send_status_updates("Images are Being Upscaled & Uploaded to DB!")
                for i, img in enumerate(images):

                    img = Functions.upscale(Functions.convert_to_png(img))
                    upload_result = cloudinary.uploader.upload(img,public_id = os.path.basename(img),folder = "Pages/")
                    cropimg = Functions.crop([img])[0]
                    upload_result1 = cloudinary.uploader.upload(cropimg,public_id = os.path.basename(img),folder = "Cropped_Pages/")

                    file_data = {
                            "file_type": "image",
                            "file_name": os.path.basename(img),
                            "file_extension": os.path.basename(img).split('.')[-1],
                            "file_path": img,
                            "Org_URL": upload_result['secure_url'],
                            "Crop_URL": upload_result1['secure_url'],
                            "Parent_ID": file_id,
                            "message": "Image received and saved.",
                        }
                    
                    inserted_document = await collection1.insert_one(file_data)
                    file_data["_id"] = str(inserted_document.inserted_id)              
                    pages.append(file_data)
                    
                    await Functions.send_status_updates(f"Image {os.path.basename(img)} Upscaled and Uploaded to DB.")
                return pages
            else:
                await Functions.send_status_updates("No Individual Images to Process.")
    @staticmethod
    async def processPages(pages):

        project_info = ipi()
        start_time = time.time()
        processing = ['Context','Overview','Owner','Stakeholders','Initiative_Details','Interdependencies','Risks_and_Mitigations','List_of_Sub_Initiatives']

        for i, img in enumerate(pages):
        
            if '_id' in project_info:
                del project_info['_id']
        
            project_info['DB_Id'] = img['DB_Id']
            project_info['Path'] = img['Path']
            
            # Check if document with the same DB_Id exists
            existing_doc = ''
            existing_doc = await collection3.find_one({'DB_Id': img['DB_Id']})
        
            if existing_doc:
        
                print("Document exists, so we update it")
                project_info['_id'] = existing_doc['_id']
            else:
        
                print("Insert a new document and set the _id in project_info")
                inserted_document = await collection3.insert_one(project_info)

        for i,img in enumerate(pages):

            project_info = ipi()
            imgpath = img['Path']
            project_info['File_Name'] = os.path.basename(imgpath)
            project_info['Path'] = img['Path']
            project_info['DB_Id'] = img['DB_Id']
            project_info['Image_String'] =  Functions.img_str(imgpath)
            
            await Functions.send_status_updates(f"Information Extraction of {project_info['File_Name']} started!")
            
            print(f"\nImage [{os.path.basename(imgpath)}] is being Processed!")
            
            if Functions.ClaudeOutput(imgpath,p.prompt_blank) == 'No':
                
                print(f"Image [{os.path.basename(imgpath)}] is Not Blank!")
                await Functions.send_status_updates(f"Image [{os.path.basename(imgpath)}] is Not Blank!")
                
                if Functions.ClaudeOutput(imgpath,p.prompt_Milestones_check) == 'No' and Functions.ClaudeOutput(imgpath,p.prompt_check) == 'No' and Functions.ClaudeOutput(imgpath,p.charter_check) == "Yes":
                    
                    print(f"Image [{os.path.basename(imgpath)}] is an Initiative Charter!\n")
                    await Functions.send_status_updates(f"Image [{os.path.basename(imgpath)}] is an Initiative Charter!\n")
                    project_info['Summary'] = Functions.ClaudeOutput(imgpath,p.prompts['Summary'])
                    # print(dict(list(project_info.items())[2:]))
                    
                    for key in list(project_info.keys())[2:-5]:
                        # p.locals()[usekey]
                        if key in processing:
                        
                            output = Functions.ClaudeOutput(imgpath,p.prompts[key])
                            print(output)
                            project_info[key] = getattr(Process_Structure,key)(Process_Structure(),*(output,))
                        
                        elif key in ['Key_Performance_Indicators']:
                        
                            output = Functions.ClaudeOutput(imgpath,p.prompts[key])
                            del project_info['Key_Performance_Indicators']
                            processed_data = getattr(Process_Structure,key)(Process_Structure(),*(output,))
                            project_info = Functions.insert_at_index(project_info, key, processed_data, 12)
                            if 'Key_Performance_Indicators' in project_info and isinstance(project_info['Key_Performance_Indicators'], dict):
                                nested_kpi = project_info['Key_Performance_Indicators'].get('Key_Performance_Indicators')
                                if nested_kpi:
                                    project_info['Key_Performance_Indicators'] = nested_kpi
                        
                        else:
                        
                            project_info[key]  = Functions.ClaudeOutput(imgpath,p.prompts[key])
                        
                        print(f"The [{key}] has been Extracted!")
                        await Functions.send_status_updates(f"The [{key}] has been Extracted!")
                    
                    project_info['Extracted'] = 'Yes'
                    project_info['Skip'] = False
                    
                    if '_id' in project_info:
                        del project_info['_id']
                    
                    result = await collection3.replace_one({'DB_Id': img['DB_Id']}, project_info, upsert = True)
                    # project_info["_id"] = str(inserted_document.inserted_id)
                    
                    if result.matched_count:
                    
                        if result.modified_count:
                            print("Document updated successfully")
                        else:
                            print("Document found but no changes were made")
                    else:
                    
                        print("No document matched the criteria")
                    
                    # Functions.JSON(project_info)  
                else:
                    
                    print(f"Image [{os.path.basename(imgpath)}] is not an Initiative Charter, so page is skipped!")
                    project_info['Summary'] = Functions.ClaudeOutput(imgpath,p.prompts['Summary'])
                    project_info['Extracted'] = 'Yes'
                    project_info['Skip'] = True
                    
                    if '_id' in project_info:
                        del project_info['_id']
                    
                    result = await collection3.replace_one({'DB_Id': img['DB_Id']}, project_info, upsert = True)
                    await Functions.send_status_updates(f"Image [{os.path.basename(imgpath)}] is not an Initiative Charter, so page is skipped!")   
            
            elif Functions.ClaudeOutput(imgpath,p.prompt_blank) == 'Yes':
            
                print(f"Image [{os.path.basename(imgpath)}] is Blank, so page is skipped!")
                project_info['Summary'] = "This is a Blank Page!"
                project_info['Extracted'] = 'Yes'
                project_info['Skip'] = True
            
                if '_id' in project_info:
                    del project_info['_id']
            
                result = await collection3.replace_one({'DB_Id': img['DB_Id']}, project_info, upsert = True)
                await Functions.send_status_updates(f"Image [{os.path.basename(imgpath)}] is Blank, so page is skipped!")
            # if Functions.ClaudeOutput(imgpath,p.prompt_Milestones_check) == 'Yes':
            #     key = list(project_info.keys())[-1]
            #     project_info[key]  = Functions.ClaudeOutput(imgpath,p.prompts[key])
        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
        await Functions.send_status_updates(f"Time taken: {end_time - start_time} seconds")

    @staticmethod
    def JSON(dictionary):
        # print(dictionary['Project_Name'])
        file_path = os.path.join("Output_JSON",f"{dictionary['File_Name'][:-4]}-{dictionary['Project_Name'].replace("/","")}.json")
        # print(file_path)
        json_string = json.dumps(dictionary,indent = 4)
        with open(file_path, "w") as json_file:
            json_file.write(json_string)
        print(f"Dictionary converted to JSON file and saved at {file_path}")

