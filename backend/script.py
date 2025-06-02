from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from openai import OpenAI
from pydantic import BaseModel

# LOAD API KEYS
import dotenv
dotenv.load_dotenv()
BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
API_KEY = os.getenv("API_KEY")

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

class Body(BaseModel):
    prompt: str

@app.post("/")
async def root(body: Body):
    # TODO add RAG from the server-side storage
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    data = {
        "model": "albert-small",
        "messages": [{"role": "user", "content": body.prompt}],
        "stream": False,
        "n": 1,
    }
    response = client.chat.completions.create(**data)
    return response.choices[0].message.content

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run(app, host="localhost", port=8000)
    

    