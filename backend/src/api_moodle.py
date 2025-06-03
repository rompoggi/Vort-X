"""
Script for selective Moodle file download using moodle-dl.
Flattens downloaded files into a single directory with unique names.

DISCLAIMER: do not delete any files in the download_path manually, as this script won't take them into account and still consider they are present.
-  If you wish to reset the files, please use the download_all_files function.
-  If you wish to download only new files, please use the download_new_files function.

"""

import os
import sys
import subprocess
import json
import requests
import shutil


def flatten_directory(download_path):
    """
    Copies all files from leaf directories under download_path into a 'Moodle_files' folder,
    resolving filename conflicts by appending (1), (2), etc. do not modify the other subfolders
    """
    # Create target directory 'Moodle_files'
    target_dir = os.path.join(download_path, "Moodle_files")
    os.makedirs(target_dir, exist_ok=True)  # Create if doesn't exist

    # Copy files from leaf directories with conflict resolution
    for root, dirs, files in os.walk(download_path):
        # Skip processing our target directory
        if root == download_path and "Moodle_files" in dirs:
            dirs.remove("Moodle_files")
        
        # Only process leaf directories (no subfolders) excluding root
        if not dirs and root != download_path:
            for filename in files:
                src_path = os.path.join(root, filename)
                
                # Skip if source is actually the target directory
                if os.path.abspath(src_path).startswith(os.path.abspath(target_dir)):
                    continue
                
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(target_dir, filename)
                counter = 1
                
                # Resolve filename conflicts
                while os.path.exists(dest_path):
                    new_filename = f"{base} ({counter}){ext}"
                    dest_path = os.path.join(target_dir, new_filename)
                    counter += 1
                
                # Copy file with original metadata
                shutil.copy2(src_path, dest_path)


def create_moodle_config(
    config_path: str,
    token: str,
    privatetoken: str,
    moodle_domain: str,
    download_course_ids: list,
    config_file_name: str = "config.json",
    moodle_path: str = "/",
    download_submissions: bool = False,
    download_descriptions: bool = False,
    download_links_in_descriptions: bool = False,
    download_databases: bool = True,
    download_forums: bool = True,
    download_quizzes: bool = True,
    download_lessons: bool = True,
    download_workshops: bool = True,
    download_books: bool = True,
    download_calendars: bool = False,
    download_linked_files: bool = False,
    download_also_with_cookie: bool = False
):
    """
    Crée un fichier de configuration JSON pour moodle-dl
    
    Args:
        token: Token d'authentification
        privatetoken: Token privé
        moodle_domain: Domaine Moodle (ex: "moodle.polytechnique.fr")
        download_course_ids: Liste des IDs de cours à télécharger
        config_file: Nom du fichier de sortie
        moodle_path: Chemin Moodle (défaut: "/")
        ... autres options avec valeurs par défaut
    """
    config = {
        "token": token,
        "privatetoken": privatetoken,
        "moodle_domain": moodle_domain,
        "moodle_path": moodle_path,
        "download_course_ids": download_course_ids,
        "download_submissions": download_submissions,
        "download_descriptions": download_descriptions,
        "download_links_in_descriptions": download_links_in_descriptions,
        "download_databases": download_databases,
        "download_forums": download_forums,
        "download_quizzes": download_quizzes,
        "download_lessons": download_lessons,
        "download_workshops": download_workshops,
        "download_books": download_books,
        "download_calendars": download_calendars,
        "download_linked_files": download_linked_files,
        "download_also_with_cookie": download_also_with_cookie
    }
    #file_path = config_path + '/' + config_file_name
    # Clean file path creation with os
    file_path = os.path.join(os.path.abspath(config_path), config_file_name)
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Configuration sauvegardée dans {file_path}")



def get_moodle_token(username: str, password: str, moodle_url: str = "https://moodle.polytechnique.fr") -> str:
    """
    Récupère un jeton d'authentification Moodle
    
    Args:
        username: Nom d'utilisateur Moodle
        password: Mot de passe Moodle
        moodle_url: URL de la plateforme Moodle, ex "https://moodle.polytechnique.fr"
    
    Returns: sous la forme {'token': 'XXXX', 'privatetoken': 'XXXX'}
        Jeton d'authentification
    
    Raises:
        Exception: Si l'authentification échoue
    """
    # Endpoint pour l'obtention du token
    token_url = f"{moodle_url}/login/token.php" + f"?username={username}&password={password}&service=moodle_mobile_app"
    
    try:
        # Envoi de la requête POST
        response = requests.post(token_url)
        #response.raise_for_status()  # Lève une exception pour les codes HTTP d'erreur
        
        # Extraction du token
        json_response = response.json()
        #print(json_response)
       
        return json_response
        
            
    except Exception as e:
        raise Exception(f"Erreur d'obtention de token': {str(e)}")


def check_moodle_dl() -> bool:
        """Vérifie si moodle-dl est installé"""
        try:
            result = subprocess.run(['moodle-dl', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
def install_moodle_dl():
        """Installe moodle-dl via pip"""
        print("Installation de moodle-dl...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'moodle-dl'])
            print("moodle-dl installé avec succès")
        except subprocess.CalledProcessError:
            print("Erreur lors de l'installation de moodle-dl")
            sys.exit(1)


def get_user_id(moodle_url, token):
    """
    Retrieves the user ID for the token's associated user.

    Args:
        moodle_url (str): The base URL of your Moodle site.
        token (str): The Moodle Web Service token.

    Returns:
        int: The user ID of the token owner.
    """
    endpoint = f"{moodle_url}/webservice/rest/server.php"
    params = {
        'wstoken': token,
        'wsfunction': 'core_webservice_get_site_info',
        'moodlewsrestformat': 'json'
    }

    response = requests.get(endpoint, params=params)
    response.raise_for_status()

    data = response.json()
    return data.get('userid')

def get_user_courses(moodle_url, token, user_id):
    """
    Retrieves the list of course IDs for a given user.
    Args:
        moodle_url (str): The base URL of your Moodle site.
        token (str): The Moodle Web Service token.
        user_id (int): The user ID for which to retrieve courses.
    Returns:
        List[int]: A list of course IDs that the user is enrolled in.
    """

    endpoint = f"{moodle_url}/webservice/rest/server.php"
    params = {
        'wstoken': token,
        'wsfunction': 'core_enrol_get_users_courses',
        'moodlewsrestformat': 'json',
        'userid': user_id
    }

    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    return [c['id'] for c in response.json()]
     

def download_new_files(
    download_path: str,
    moodle_url, 
    username, 
    password,
    config_file_name: str = "config.json",
    moodle_path: str = "/",
    download_submissions: bool = False,
    download_descriptions: bool = False,
    download_links_in_descriptions: bool = False,
    download_databases: bool = True,
    download_forums: bool = True,
    download_quizzes: bool = True,
    download_lessons: bool = True,
    download_workshops: bool = True,
    download_books: bool = True,
    download_calendars: bool = False,
    download_linked_files: bool = False,
    download_also_with_cookie: bool = False):
    """
    Télécharge les fichiers Moodle en utilisant moodle-dl.
    Args:
        download_path: Chemin où les fichiers seront téléchargés
        moodle_url: URL de la plateforme Moodle, ex "https://moodle.polytechnique.fr"
        username: Nom d'utilisateur Moodle
        password: Mot de passe Moodle
        config_file_name: Nom du fichier de configuration (par défaut "config.json")
        moodle_path: Chemin Moodle (défaut: "/")
        ... autres options avec valeurs par défaut
    """


    token_dict = get_moodle_token(username , password, moodle_url)
    print("TOKEN DICT", token_dict)
    token = token_dict['token']
    private_token = token_dict['privatetoken']
    courses_id = get_user_courses(moodle_url=moodle_url, token = token, user_id= get_user_id(moodle_url,token))
    #now that we have all variables we create the config:
    moodle_domain = moodle_url.replace('https://', '').replace('http://', '')
    create_moodle_config(download_path, token, private_token, moodle_domain, courses_id)
    print(download_path)
    subprocess.run(['moodle-dl', '-p', "./" + download_path])
    subprocess.run(['moodle-dl'])
    print("Téléchargement terminé")
    # Flatten the directory structure after download
    flatten_directory(download_path)


def download_all_files(
    download_path: str,
    moodle_url, 
    username, 
    password,
    config_file_name: str = "config.json",
    moodle_path: str = "/",
    download_submissions: bool = False,
    download_descriptions: bool = False,
    download_links_in_descriptions: bool = False,
    download_databases: bool = True,
    download_forums: bool = True,
    download_quizzes: bool = True,
    download_lessons: bool = True,
    download_workshops: bool = True,
    download_books: bool = True,
    download_calendars: bool = False,
    download_linked_files: bool = False,
    download_also_with_cookie: bool = False):
    """
    Delete tous les anciens fichiers puis télécharge les fichiers Moodle en utilisant moodle-dl
    Args:
        download_path: Chemin où les fichiers seront téléchargés
        moodle_url: URL de la plateforme Moodle, ex "https://moodle.polytechnique.fr"
        username: Nom d'utilisateur Moodle
        password: Mot de passe Moodle
        config_file_name: Nom du fichier de configuration (par défaut "config.json")
        moodle_path: Chemin Moodle (défaut: "/")
        ... autres options avec valeurs par défaut
    """
    # Supprimer tous les fichiers et dossiers dans le dossier de téléchargement
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {file_path}: {e}")
        for name in dirs:
            dir_path = os.path.join(root, name)
            try:
                os.rmdir(dir_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du dossier {dir_path}: {e}")

    download_new_files(
        download_path=download_path,
        moodle_url=moodle_url,
        username=username,
        password=password,
        config_file_name=config_file_name,
        moodle_path=moodle_path,
        download_submissions=download_submissions,
        download_descriptions=download_descriptions,
        download_links_in_descriptions=download_links_in_descriptions,
        download_databases=download_databases,
        download_forums=download_forums,
        download_quizzes=download_quizzes,
        download_lessons=download_lessons,
        download_workshops=download_workshops,
        download_books=download_books,
        download_calendars=download_calendars,
        download_linked_files=download_linked_files,
        download_also_with_cookie=download_also_with_cookie
    )
    # save_credentials(
    #     save_path=download_path,
    #     moodle_url=moodle_url,
    #     username=username
    # )

# def save_credentials(
#     save_path: str,
#     moodle_url: str,
#     username: str,
# ):
#     """
#     Sauvegarde la configuration dans un fichier JSON.
    
#     Args:
#         download_path: Chemin où les fichiers seront téléchargés
#         moodle_url: URL de la plateforme Moodle, ex "https://moodle.polytechnique.fr"
#         username: Nom d'utilisateur Moodle
#         password: Mot de passe Moodle
#     """
#     config = {
#         "moodle_url": moodle_url,
#         "username": username,
#     }
    
#     with open(os.path.join(save_path, 'credentials.json'), 'w') as f:
#         json.dump(config, f, indent=4)

# def load_credentials(save_path: str):
#     """
#     Charge la configuration depuis un fichier JSON.
    
#     Args:
#         save_path: Chemin où le fichier de configuration est sauvegardé
#     Returns:
#         dict: Dictionnaire contenant les informations de configuration
#     """
#     with open(os.path.join(save_path, '/credentials.json'), 'r') as f:
#         config = json.load(f)
    
#     return ( config['username'], config['moodle_url'])

# def reset_RAG_data(
#     download_path: str,
#     password: str,
# ):
#     """
#     Met à jour le fichier de configuration avec les nouvelles informations.
    
#     Args:
#         download_path: Chemin où les fichiers seront téléchargés
#         moodle_url: URL de la plateforme Moodle, ex "https://moodle.polytechnique.fr"
#         username: Nom d'utilisateur Moodle
#         password: Mot de passe Moodle
#         config_file_name: Nom du fichier de configuration (par défaut "config.json")
#     """
#     username, moodle_url = load_credentials(download_path)
#     download_all_files(
#         download_path=download_path,
#         moodle_url=moodle_url,
#         username=username,
#         password=password,
#     )

# def update_RAG_data(
#     download_path: str,
#     password: str,
# ):
#     """
#     Met à jour le fichier de configuration avec les nouvelles informations.
    
#     Args:
#         download_path: Chemin où les fichiers seront téléchargés
#         moodle_url: URL de la plateforme Moodle, ex "https://moodle.polytechnique.fr"
#         username: Nom d'utilisateur Moodle
#         password: Mot de passe Moodle
#         config_file_name: Nom du fichier de configuration (par défaut "config.json")
#     """
#     username, moodle_url = load_credentials(download_path)
#     download_new_files(
#         download_path=download_path,
#         moodle_url=moodle_url,
#         username=username,
#         password=password,
#     )

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

###########################
# Class to extract prompt from body
from pydantic import BaseModel
class BodyMoodle(BaseModel):
    username: str
    session: str
    password: str
    action: str

@app.post("/")
async def root(body: BodyMoodle):
    username = body.username
    moodle_url = body.session
    password = body.password
    action = body.action

    OUT_FILE = "./moodle_storage/"

    if (action == "update"):
        download_new_files(download_path=OUT_FILE, moodle_url=moodle_url, username=username, password=password)

    if (action == "reset"):
        download_all_files(download_path=OUT_FILE, moodle_url=moodle_url, username=username, password=password)
    return

def api_moodle():
    if DEBUG: print("Starting FastAPI server...")
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    api_moodle()
    exit(1)
