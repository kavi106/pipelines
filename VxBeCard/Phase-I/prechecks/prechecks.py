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
    try:
        auth = Auth.Token(os.getenv("CONFIG_REPO_TOKEN"))
        g = Github(auth=auth)
        repo = g.get_repo(os.getenv("CONFIG_REPO"))
        folder = kwargs["folder"]
        filename = kwargs["additional_files"]["base_input_json"]
        file_content = repo.get_contents(
            f"{folder}/{filename}", os.getenv("CONFIG_REPO_BRANCH")
        )
        kwargs["base_input_json"] = json.loads(file_content.decoded_content.decode())
    except:
        return (400, f"Cannot get tec_qc_config.json from repo !", kwargs)
    try:
        filename = kwargs["additional_files"]["ursgal_credentials"]
        file_content = repo.get_contents(
            f"{folder}/{filename}", os.getenv("CONFIG_REPO_BRANCH")
        )
        kwargs["ursgal_credentials"] = json.loads(file_content.decoded_content.decode())
    except:
        return (400, f"Cannot get credentials_lookup.json from repo !", kwargs)

    print(kwargs)
    return 200, "All configuration files pulled successfully.", kwargs

def pullFcsFiles(**kwargs):
    sleep(5)
    kwargs["ws"] = "myLabDataValidation"
    kwargs["cc"] = "XYZ"
    print(kwargs)
    return 400, "0 fsc files found !", kwargs

def validateExcelMetadataFile(**kwargs):
    sleep(3)
    if kwargs["studyNumber"] == '11':
        return 200, "Success !!!", kwargs
    else:
        return 400, "Error !!!", kwargs