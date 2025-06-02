from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from openai import OpenAI
from pydantic import BaseModel
import requests
import json

BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
COLLECTION_NAME = "moodle_pdfs"
MAX_HISTORY_CHARS = 3000
MAX_MESSAGES_HISTORY = 20
# import API from backend/api_key.secret which is a .txt file containing the API key
# so we read backend/api_key.secret file
with open("backend/api_key.secret", "r") as f:
    API_KEY = f.read().strip()
    
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
    # TODO add "download from moodle" feature / know when to refresh the collection
    # TODO add store history feature
    # TODO dont give chunk ID but global position in PDF
    # TODO ping endroit en particulier dans le texte avec les top k chunks

    prompt, command = parse_command(body.prompt)

    collection_id = await get_collection_id()
    
    # Get the top k chunks from the RAG service
    print("Getting RAG chunks...")
    chunks_dict_list = await get_rag_chunks(prompt, collection_id, k=6)
    
    # Source the chunks from the RAG service
    chunk_file_sources = []
    for chunk_dict in chunks_dict_list:
        chunk_file_sources.append({
            "file_name": chunk_dict["metadata"]["document_name"],
            "chunk_id": chunk_dict["id"],
        })

    # Get the full chunk
    full_chunk_rag = "\n\n\n".join([chunk_dict["content"] for chunk_dict in chunks_dict_list])

    # Call the OpenAI API with the full chunk and the prompt
    print("Calling OpenAI API...")
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    messages = read_history()
    messages.append({"role": "tool", "content": full_chunk_rag})
    messages.append({"role": "user", "content": prompt})
    data = {
        "model": "albert-small",
        "messages": messages,
        "stream": False,
        "n": 1,
    }
    response = client.chat.completions.create(**data)

    answer = apply_command(response.choices[0].message.content, command, chunk_file_sources)

    if command != "reset":
        write_history(prompt, answer)

    return answer

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run(app, host="localhost", port=8000)
    
def read_history():
    """
    Read the history from the history.json file.
    """
    history_file = "history.json"
    if not os.path.exists(history_file):
        return []
    
    with open(history_file, "r") as f:
        history = json.load(f)
    
    return history

def write_history(prompt: str, response: str):
    """
    Write the prompt and response to the history.json file.
    """
    history_file = "history.json"
    history = read_history()
    
    # Append the new entry
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": response})
    
        # Make sure the history does not exceed the MAX_TOKEN_HISTORY
    # Compute total number of characters in the history
    total_chars = sum(len(entry["content"]) for entry in history)
    # On garde au minimum 4 entries (2 user and 2 assistant) pour le contexte
    while (total_chars > MAX_HISTORY_CHARS and len(history) > 4) or len(history) > MAX_MESSAGES_HISTORY * 2:
        # Remove the oldest entry (the first one)
        total_chars -= len(history[0]["content"]) + len(history[1]["content"])
        history = history[2:]  # Remove the first user and assistant entries

    # Write the updated history back to the file
    with open(history_file, "w") as f:
        json.dump(history, f)

def apply_command(response: str, command: str, chunk_file_sources: list):
    if command is None:
        return response
    elif command == "source":
        # If the command is "source", we return the sources of the chunks
        sources = []
        for chunk_file_source in chunk_file_sources:
            sources.append(f"File: {chunk_file_source['file_name']}, Chunk ID: {chunk_file_source['chunk_id']}")
        return response + "\n\nSources used :\n" + "\n".join(sources)
    elif command == "reset":
        with open("history.json", "w") as f:
            json.dump([], f)
        return "History reset."
    else:
        # If the command is not recognized, we return the response as is
        return f"Command '{command}' not recognized. Response: {response}"

def parse_command(prompt: str):
    """
    Parse the command from the prompt.
    """
    command = None
    if prompt.startswith("/"):
        # Keep the first word as the command
        command = prompt.split()[0][1:]
        prompt = prompt[len(command) + 2:]  # Remove the command and the space after it
    
    return prompt, command

async def get_collection_id():
    # Get if the collection already exists
    collection_id = None
    offset = 0
    while offset == 0 or len(response["data"]) == 100:
        # Connect to the session
        session = requests.session()
        session.headers = {"Authorization": f"Bearer {API_KEY}"}

        # Get the list of collections
        response = session.get(f"{BASE_URL}/collections?offset={offset}&limit=100")
        offset += 100
        assert response.status_code == 200
        response = response.json()
 
        # Check if the collection already exists
        for collection in response["data"]:
            if collection["name"] == COLLECTION_NAME:
                collection_id = collection["id"]
                break

        if offset > 1000:
            raise Exception("Too many collections for Albert API please delete some before refreshing the moodle collection.")
        
    return collection_id

async def refresh_moodle_collection(collection_id: int):
    # Upload a collection of PDF files to the RAG service
    session = requests.session()
    session.headers = {"Authorization": f"Bearer {API_KEY}"}

    embeddings_model = "embeddings-small"

    if collection_id is not None:
        # If the collection exists, we first delete it to refresh it
        response = session.delete(f"{BASE_URL}/collections/{collection_id}")
        assert response.status_code == 204

    # Create a collection for RAG
    response = session.post(f"{BASE_URL}/collections", json={"name": COLLECTION_NAME, "model": embeddings_model})
    assert response.status_code == 201
    response = response.json()
    collection_id = response["id"]
    
    # Get all pdf files in ./moodle_pdfs/
    moodle_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moodle_pdfs")
    pdf_files = [f for f in os.listdir(moodle_dir) if f.endswith(".pdf")]

    # Add all pdf files to the collection
    for file_local_path in pdf_files:
        file_path = os.path.join(moodle_dir, file_local_path)
        files = {"file": (os.path.basename(file_path), open(file_path, "rb"), "application/pdf")}
        data = {"request": '{"collection": "%s"}' % collection_id}
        response = session.post(f"{BASE_URL}/files", data=data, files=files)
        assert response.status_code == 201

    
async def get_rag_chunks(prompt: str, collection_id : int, k: int = 6, cosine_similarity_minimum: float = 0.5):
    # Connect to the session
    session = requests.session()
    session.headers = {"Authorization": f"Bearer {API_KEY}"}

    # Get the top k chunks from the RAG service
    data = {"collections": [collection_id], "k": k, "prompt": prompt, "method": "semantic", "score_threshold": cosine_similarity_minimum}
    response = session.post(url=f"{BASE_URL}/search", json=data)

    chunks_dicts_list = [result["chunk"] for result in response.json()["data"]]
    return chunks_dicts_list

