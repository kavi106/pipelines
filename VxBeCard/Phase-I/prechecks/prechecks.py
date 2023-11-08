import json
import os
#import re
#import requests
#import ursgal
from github import Auth, Github
#from datetime import datetime
# from send_email import send_email, render_template
# from sqlalchemy.orm import Session
# from db_lib import crud
# from db_lib.database import engine
# from db_lib.models import StateEnum
# from .base import Base



from time import sleep

def pullConfigFiles(**kwargs):

    #return 200, "Success !!", kwargs
    
    try:
        auth = Auth.Token(os.getenv("CONFIG_REPO_TOKEN"))
        g = Github(auth=auth)
        repo = g.get_repo(os.getenv("CONFIG_REPO"))
        folder = kwargs["folder"]
        for exit in kwargs["exits"]:
            filename = exit["additional_files"]["base_input_json"]
            file_content = repo.get_contents(
                f"{folder}/{filename}", os.getenv("CONFIG_REPO_BRANCH")
            )
            exit["additional_files"]["base_input_json"] = json.loads(file_content.decoded_content.decode())
            filename = exit["additional_files"]["ursgal_credentials"]
            file_content = repo.get_contents(
                f"{folder}/{filename}", os.getenv("CONFIG_REPO_BRANCH")
            )
            exit["additional_files"]["ursgal_credentials"] = json.loads(file_content.decoded_content.decode())
    except:
        return (400, f"Cannot get configuration files !", kwargs)

    #print(kwargs)
    return 200, "All configuration files pulled successfully.", kwargs

def pullFcsFiles(**kwargs):
    #ursgal_credentials["credentials_lookup"]
    print(kwargs["exits"][0]["credentials_lookup"])
    sleep(5)
    kwargs["ws"] = "myLabDataValidation"
    kwargs["cc"] = "XYZ"
    #print(kwargs["base_input_json"])
    return 400, "0 fsc files found !", kwargs

def validateExcelMetadataFile(**kwargs):
    sleep(3)
    if kwargs["studyNumber"] == '11':
        return 200, "Success !!!", kwargs
    else:
        return 400, "Error !!!", kwargs