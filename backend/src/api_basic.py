###########################
# LOAD API KEYS
import os
import dotenv
dotenv.load_dotenv()
BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
API_KEY = os.getenv("API_KEY")

###########################
# ENV CONSTS
DEBUG = True

MODEL_NAME = "albert_small"

###########################
# Create a FastAPI instance
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from openai import OpenAI
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from datetime import datetime
SYSTEM_PROMPT = True
if (SYSTEM_PROMPT == True):
    SYSTEM_PROMPT_FILE = "./src/system_prompt.txt"
    with open(SYSTEM_PROMPT_FILE, "r") as file:
        system_prompt = "".join(file.readlines()).format(currentDateTime=datetime.now().strftime("%Y-%m-%d"))
        if DEBUG: print("system prompt", system_prompt) 

###########################
# Class to extract prompt from body
from pydantic import BaseModel
class Body(BaseModel):
    prompt: str

###########################
# Other imports

#######################################################################
#######################################################################


@app.post("/")
async def root(body: Body):
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    messages = [{"role": "user", "content": body.prompt}]
    if SYSTEM_PROMPT: messages.append({"role": "system", "content": system_prompt})
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "n": 1,
    }
    response = client.chat.completions.create(**data)
    # if DEBUG: print(response.choices[0].message.content)
    return {"response": response.choices[0].message.content}

def api_basic():
    if DEBUG: print("Starting FastAPI server...")
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    api_basic()
    exit(1)
