from fastapi import FastAPI, Request, UploadFile, File, BackgroundTasks
from fastapi.templating import Jinja2Templates
import shutil
import os
import ocr
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# get the html using app.get
@app.get("/")
def home(request : Request):
    return templates.TemplateResponse("index.html",{"request":request})

# the app endpoint will take the image and perform the ocr and return the response
@app.post("git init")
# ... is a placeholder and this will initialize the file object for us and store it in image variable
async def perform_ocr(image : UploadFile = File(...)):
    # save the file
    temp_file = _save_file_to_disk(image, path="temp", save_as="temp")
    # perform the ocr
    text =await ocr.read_image(temp_file)
    return {"filename":image.filename, "text": text}

# For multiple image uploading
@app.post('/api/v1/bulk_extract_text')
async def bulk_perform_ocr(request : Request, bg_tasks : BackgroundTasks):
    images = await request.form()
    #saving images to our local machine
    #uuid will be also task id which will be queued in our task to extract results later on
    folder_name = str(uuid.uuid4())
    os.mkdir(folder_name)
    # save the image in the folder which we just created using uuid
    for image in images.values():
        temp_file = _save_file_to_disk(image, path=folder_name, save_as=image.filename)

    # ocr to be run in the background
    bg_tasks.add_task(ocr.read_images_from_dir,folder_name, write_to_file=True)
    # once the task has been queued or scheduled we can return the response
    return {"task_id":folder_name, "num_files":len(images)}

# check the multiple images , show the process and amount of images has been proceeded
@app.get("/api/v1/bulk_output/{task_id}")
async def bulk_output(task_id):
    text_map = {}
    for file_ in os.listdir(task_id):
        if file_.endswith("txt"):
            text_map[file_] = open(os.path.join(task_id, file_)).read()
    return {"task_id": task_id, "output": text_map}

def _save_file_to_disk(uploaded_file, path=".", save_as="default"):
    extension = os.path.splitext(uploaded_file.filename)[-1]
    temp_file = os.path.join(path, save_as + extension)
    # write and binary. Since we are writing a .jpg file, it looks fine.  " wb "
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)
    return temp_file

