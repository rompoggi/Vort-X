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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    data = {
        "model": "albert-small",
        "messages": [{"role": "user", "content": body.prompt}],
        "stream": False,
        "n": 1,
    }
    response = client.chat.completions.create(**data)
    # if DEBUG: print(response.choices[0].message.content)
    return {"response": response.choices[0].message.content}

if __name__ == "__main__":
    if DEBUG: print("Starting FastAPI server...")
    uvicorn.run(app, host="localhost", port=8000)
