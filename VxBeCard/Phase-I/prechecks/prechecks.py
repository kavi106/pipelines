import json
import argparse
import os
import re
import logging
import requests
#import datetime
import ursgal
import github.GithubException
import pandas as pd

from datetime import datetime
from github import Auth, Github
from send_email import send_email, render_template
from sqlalchemy.orm import Session
from db_lib import crud
from db_lib.database import engine
from db_lib.models import StateEnum
from collections import Counter


pd.set_option("display.max_columns", 100)

def sanitizing_user_inputs(input_dict):
    inputs = {
        "myLabDataTaskId": {
            "name" : "MyLabData TaskId",
            "pattern": "^[A-Za-z0-9_-]{0,30}$",
            "type": "string"
        },
        "requesterMUDID": {
            "name" : "Requester MUDID",
            "pattern": "^[A-Za-z0-9]{0,15}$",
            "type": "string"
        },
        "instrumentSapId": {
            "name" : "Instrument SAP ID",
            "pattern": "^[0-9]{0,20}$",
            "type": "string"
        },
        "dataCleanAlgorithm": {
            "name" : "Data Clean Algorithm",
            "pattern": "^.{0,20}$",
            "type": "string"
        },
        "projectName": {
            "name" : "Project Name",
            "pattern": "^.{0,50}$",
            "type": "string"
        },
        "experimentNumber": {
            "name" : "Experiment Number",
            "pattern": "^ELN[0-9a-zA-Z-_]{0,10}$",
            "type": "string"
        },
        "studyNumber": {
            "name" : "Study Number",
            "pattern": "^[0-9a-zA-Z_-]{0,30}$",
            "type": "string"
        },
        "resultRecipient": {
            "name" : "Result Recipient",
            "pattern": "^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$",
            "type": "RecipientArray"
        }
    }
    output = []
    for field in inputs:
        input_type = inputs[field]["type"]
        if input_type == "string":
            return (400, f"aa", input_dict)
            if not re.match(inputs[field]['pattern'], input_dict[field]):
                input_dict[field] = ""
                output.append(f"{inputs[field]['name']} has invalid input.")

    if len(output) > 0:
        error_message = ", ".join(output)
        return (400, f"{error_message}", input_dict)
    else:
        return (200, "All input fields valid.", input_dict)

def list_mylabdata_file(input_dict):
    _init_ursgal(input_dict)
    # ursgal.instances.ucredential_manager.add_credentials(
    #     input_dict["exits"][0]["kwargs"]["ursgal_credentials"]["credentials_lookup"]
    # )
    equipment_id = input_dict["instrumentSapId"]
    task_id = input_dict["myLabDataTaskId"]
    storage_base = f"mylabdata://{input_dict['prechecks_config']['mylabdata_api_backend_url']}/{equipment_id}/{task_id}"

    # ursgal.config["certificates"][
    #     input_dict["prechecks_config"]["mylabdata_api_backend_url"]
    # ] = False
    input_dict["mylabdata_files"] = []

    try:
        file_list_mld = ursgal.UFile(
            f"{storage_base}#dummy.txt"
        ).io.list_container_items()
    except:
        return (400, f"Cannot connect to {storage_base}", input_dict)

    input_dict["mylabdata_files"] = file_list_mld

    return_code = 400 if len(file_list_mld) == 0 else 200

    return return_code, f"Found {len(file_list_mld)} files in mylabdata bucket", input_dict


def pull_config_files(input_dict):
    """_summary_


    Args:
        input_dict (_type_): _description_

    Returns:
        dict: the return input_dict / pimped process.json will look like

            "exits": [
                {
                    "kwargs": {
                        "flow_name": "TecQC Pipeline",
                        "prefect_netloc": "https://flink.dev.a-launch-i.gsk.com/api/deployments/0b26bad3-bb47-4e4f-b0a8-a21d6719a9e8/create_flow_run"
                        "base_input_json" : "<the actual json pulled from github>",
                        "ursgal_credentials": "<the actual json pulled from github>"
                    },
                    "type": "prefect",
                    "pipeline": "tec_qc_prefect_pipeline.py",
                    "additional_files": {
                        "base_input_json": "tec_qc_config.json",
                        "ursgal_credentials": "credentials_lookup.json"
                    }
                }
            ]
    """
    auth = Auth.Token(os.getenv("CONFIG_REPO_TOKEN"))
    g = Github(auth=auth)
    repo = g.get_repo(os.getenv("CONFIG_REPO"))

    folder = input_dict["folder"]
    for exit in input_dict["exits"]:
        for file_key, filename in exit["additional_files"].items():
            try:
                file_content = repo.get_contents(
                    f"{folder}/{filename}", os.getenv("CONFIG_REPO_BRANCH")
                )
            except github.GithubException:
                return (
                    400,
                    f"Cannot get configuration files {folder}/{filename} from branch {os.getenv('CONFIG_REPO_BRANCH')}!",
                    input_dict,
                )

            exit["kwargs"][file_key] = json.loads(file_content.decoded_content.decode())

    meta_data_excel_mapping_location = os.path.join(
        input_dict["folder"],
        input_dict["prechecks_config"]["meta_data_excel_mapping"],
    )
    try:
        meta_data_excel_mapping = repo.get_contents(
            meta_data_excel_mapping_location, os.getenv("CONFIG_REPO_BRANCH")
        ).decoded_content.decode()
    except github.GithubException:
        return (
            400,
            f"Cannot get meta data file, expected: {meta_data_excel_mapping_location}!",
            input_dict,
        )
    input_dict["prechecks_config"]["meta_data_excel_mapping"] = meta_data_excel_mapping

    return 200, "All configuration files pulled successfully.", input_dict


def pull_fcs_files(input_dict):
    """_summary_

    Args:
        input_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        fcs_uri_list = _create_ufile_uri_list(
            input_dict,
            input_dict["prechecks_config"]["input_file_pattern"],
            ursgal.uftypes.flow_cytometry.FCS,
        )

        len_fcs_file_list = len(fcs_uri_list)
        if len_fcs_file_list == 0:
            return 400, f"0 fsc files under TaskId {input_dict['myLabDataTaskId']}. Please double check if the TaskId is correct.", input_dict

        input_dict["fcs_uri_list"] = fcs_uri_list

    except:
        return 400, f"Error getting fcs files !", input_dict

    return 200, f"{len_fcs_file_list} fsc files found !", input_dict


def _create_ufile_uri_list(input_dict, file_pattern, uftype):
    equipment_id = input_dict["instrumentSapId"]
    task_id = input_dict["myLabDataTaskId"]
    storage_base = f"mylabdata://{input_dict['prechecks_config']['mylabdata_api_backend_url']}/{equipment_id}/{task_id}"
    file_list = []
    for file in input_dict["mylabdata_files"]:
        if re.search(file_pattern, file):
            file_list.append(f"{storage_base}?uftype={uftype}#{file}")
    return file_list


def _get_file_list(input_dict, file_pattern, uftype):
    ursgal.instances.ucredential_manager.add_credentials(
        input_dict["exits"][0]["kwargs"]["ursgal_credentials"]["credentials_lookup"]
    )
    equipment_id = input_dict["instrumentSapId"]
    task_id = input_dict["myLabDataTaskId"]
    storage_base = f"mylabdata://{input_dict['prechecks_config']['mylabdata_api_backend_url']}/{equipment_id}/{task_id}"

    ursgal.config["certificates"][
        input_dict["prechecks_config"]["mylabdata_api_backend_url"]
    ] = False
    try:
        file_list_mld = ursgal.UFile(
            f"{storage_base}#dummy.txt"
        ).io.list_container_items()
    except:
        return (400, f"Cannot connect to {storage_base}", input_dict)

    file_list = []
    for file in file_list_mld:
        if re.search(file_pattern, file):
            file_list.append(f"{storage_base}?uftype={uftype}#{file}")
    return file_list


def _init_ursgal(input_dict):
    try:
        ursgal.instances.ucredential_manager.add_credentials(
            input_dict["exits"][0]["kwargs"]["ursgal_credentials"]["credentials_lookup"]
        )
        ursgal.config["certificates"][
            input_dict["prechecks_config"]["mylabdata_api_backend_url"]
        ] = False
    except:
        return 400, "Failed to initialize ursgal ucredentials !", input_dict


def validate_meta_data_excel(input_dict):
    """Validate Meta Data Excel entries agains input_dict based on a validation_json.

    Args:
        input_dict (dict): Submitted User data (jsonforms)
        # excel_file (MS Excel File): Excel sheet with meta data
        # validation_json (json): JSon with mappings for all fields
        #     input_dict.field <-> excel.sheet.row.column. Defaults to None.

    Returns:
        _type_: _description_
    """
    _init_ursgal(input_dict)
    checks = json.loads(input_dict["prechecks_config"]["meta_data_excel_mapping"])

    try:
        excel_files = _create_ufile_uri_list(
            input_dict,
            input_dict["prechecks_config"]["meta_data_input_file_pattern"],
            uftype=ursgal.uftypes.mx.METADATA_XLSX,
        )
    except:
        return 400, f"Error getting Excel Metadata file !", input_dict

    num_excel_files = len(excel_files)
    if num_excel_files == 0:
        return (
            400, 
            "0 excel metadata file found !"
            " Please make sure that the excel filename is"
            " 'standard_metadata_lab_input_v1.0.0.xlsx'", 
            input_dict
        )

    if num_excel_files != 1:
        e_file_names = ', '.join([(ursgal.UFile(file)).object_name for file in excel_files])
        return 400, f"{num_excel_files} metadata excel files found in the main folder: ({e_file_names}) !", input_dict

    meta_excel_uf = ursgal.UFile(excel_files[0])
    meta_xls = pd.ExcelFile(meta_excel_uf.path)

    if not "validated_meta_data" in input_dict:
        input_dict["validated_meta_data"] = {}
    msg = []
    for check in checks:
        json_field = check["input_json_field"]
        xls_df = meta_xls.parse(sheet_name=check["sheet"], header=None)
        check["input_value"] = input_dict.get(
            json_field,
            f"{json_field} was not specified in input_dict",
        )
        check["meta_data_excel_value"] = xls_df.iloc[
            check["row"] - 1, check["column"] - 1
        ]
        check_requires_validation = check.get("validate", True)

        if (
            str(check["meta_data_excel_value"]).strip() == str(check["input_value"]).strip()
            or check_requires_validation is False
        ):
            input_dict["validated_meta_data"][json_field] = check[
                "meta_data_excel_value"
            ]
        else:
            msg.append(
                "Value for '{input_json_field}' in sheet '{sheet}' (row '{row}', "
                " column '{column}') is '{meta_data_excel_value}' "
                "yet recieved '{input_value}' as input on Web User Interface".format(
                    **check,
                )
            )
    if len(msg) > 0:
        return 400, ". ".join(msg), input_dict
    else:
        return 200, "All meta data fields match excel sheet", input_dict


def validate_plate_csv(input_dict):
    """Validate plate CSV for correct experiment_number and experiment_name entries.

    Function uses process.json prechecks.plate_data_input_file_pattern to get a list of
    all plate csv in the selecged mylabdata bucket and compares the entries of the columns
    experiment_name and experiment_number against the entry in the meta data sheet.
    We also check if we have only 1 csv file per plate

    """
    _init_ursgal(input_dict)

    jsonforms_to_csv_column_name_mappings = {
        "experimentNumber": "experiment_number",
        "experimentName": "experiment_name",
    }
    try:
        plate_csvs = _create_ufile_uri_list(
            input_dict,
            input_dict["prechecks_config"]["plate_data_input_file_pattern"],
            uftype=ursgal.uftypes.any.CSV,
        )
    except:
        return 400, "Error getting CSV file !", input_dict

    if len(plate_csvs) == 0:
        return (
            400,
            "0 plate CSV file found in MyLabData for the input TaskId"
            " Please make sure that the csv filename follows the naming convention:"
            " 'standard_metadata_lab_input_PlateX_v1.0.0.csv' where X is an integer", 
            input_dict,
        )
    
    panel_names = []
    logging.debug(f"will check agains {input_dict['validated_meta_data']}")
    for p_csv in plate_csvs:
        p_csv_uf = ursgal.UFile(p_csv)
        df = pd.read_csv(p_csv_uf.path)
        for j_field, c_field in jsonforms_to_csv_column_name_mappings.items():
            if df[c_field].nunique() != 1:
                logging.debug(df.head(10))
                return (
                    400,
                    f"Plate CSV {p_csv_uf.object_name} has multiple entries in {c_field}, expected only 1",
                    input_dict,
                )
            c_value = df[c_field].unique()[0]
            j_value = input_dict["validated_meta_data"].get(
                j_field,
                None,
            )
            if c_value != j_value:
                logging.debug(df.head(10))
                return (
                    400,
                    f"Plate CSV {p_csv_uf.object_name} has {c_value} in {c_field},"
                    f" yet extracted value {j_value} from meta data excel sheet.",
                    input_dict,
                )
            else:
                logging.debug(f"{j_value} matches {c_field}")

        if not hasattr(df, 'panel_name'):
            return (
                400, 
                f"Plate CSV {p_csv_uf.object_name} does not have panel name field !", 
                input_dict
            )

        if df['panel_name'].nunique() != 1:
            logging.debug(df.head(10))
            return (
                400,
                f"Plate CSV {p_csv_uf.object_name} has multiple entries in panel_name, expected only 1",
                input_dict,
            )
        else:
            panel_names.append(df['panel_name'].unique()[0])

    input_dict["panel_names"] = panel_names
    
    return (
        200,
        "All Plate CSV entries for experiment_number and"
        " experiment_name match meta_data.xlsx and user input.",
        input_dict,
    )

def validate_panel_name(input_dict):
    """Validate panel name in CSV file match plate name in fcs file name.

    """
    unique_panel_names = list(dict.fromkeys(input_dict["panel_names"]))
    num_panel_names = len(unique_panel_names)
    if num_panel_names > 1:
        return (
            400, 
            f"{num_panel_names} panel names found in CSV files ({', '.join(unique_panel_names)}) !", 
            input_dict
        )
    
    panel_name = unique_panel_names[0]
    p_fcs_file = ursgal.UFile(input_dict['fcs_uri_list'][0])
    panel_name_fcs_file = (p_fcs_file.object_name.split('/')[-1]).split('_')[2]
    if panel_name.strip() != panel_name_fcs_file.strip():
        return (
            400,
            f"Plate CSV has {panel_name} as panel name,"
            f" yet fcs file has {panel_name_fcs_file} as panel name.",
            input_dict,
        )
    
    return (
        200,
        "Panel name in CSV files match panel name in fcs file name.",
        input_dict,
    )


def start_prefect_pipeline(input_dict):
    wid = ursgal.UWIDGenerator().generate_wid()
    input_dict["wid"] = wid
    
    if "_validation" in input_dict and input_dict["_validation"] != 200:
        return 400, "Please fix the errors and submit again !", input_dict

    try:
        configuration_json = input_dict["exits"][0]["kwargs"]["base_input_json"]
        configuration_json["files"]["fcs"] = input_dict["fcs_uri_list"]
        configuration_json["credentials_lookup"] = input_dict["exits"][0]["kwargs"][
            "ursgal_credentials"
        ]["credentials_lookup"]
    except:
        return 400, "No fcs files to process !", input_dict
    
    response = requests.post(
        url=input_dict["exits"][0]["kwargs"]["prefect_netloc"],
        json={
            "parameters": {
                "wid": wid,
                "input_json": configuration_json,
            },
        },
    )
    if response.status_code == 201:
        return (
            200,
            f"Submitted pipeline run with workflow ID: {wid}.",
            input_dict,
        )
    else:
        return response.status_code, f"Submission failed", input_dict


def send_notification(input_dict):
    try:
        recipients = (
            [i["email"] for i in input_dict["resultRecipient"]]
            if "resultRecipient" in input_dict and len(input_dict["resultRecipient"]) > 0
            else []
        )
        recipients.append(input_dict["requesterEmail"])
        if "teams_email" in input_dict and len(input_dict["teams_email"]) > 0:
            recipients.append(input_dict["teams_email"])
    except:
        return 400, "No recipients !", {}

    if "_validation" in input_dict and input_dict["_validation"] != 200:
        email_template = "error.html"
        message_color = "red"
        message_text = "<br/><br/>".join(input_dict["_validation_message"])
    else:
        email_template = "submit.html"
        message_color = "green"
        message_text = "Task submitted successfully."

    date_time_str = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
    task_id = input_dict['myLabDataTaskId']
    if len(message_text) > 0:
        templ_variables = {
            "date_time_str": date_time_str,
            "experiment_id": f"{input_dict['experimentNumber']}",
            "task_id": task_id,
            "message_text": message_text,
            "message_color": message_color,
            "wid": input_dict['wid'],
        }
        html = render_template(email_template, **templ_variables)
        send_email(
            recipients,
            "dso.launchi-app@gsk.com",
            cc="",
            bcc="",
            subject=f"Flow Cytometry Data Clean Process - {task_id}",
            body=html,
        )

    try:
        with Session(engine) as db:
            crud.create_recipient(
                db=db,
                recipient={
                    "wid": input_dict['wid'],
                    "recipients": ",".join(recipients),
                    "taskid": f"{task_id}",
                    "instrumentid": f"{input_dict['instrumentSapId']}",
                    "experimentid": f"{input_dict['experimentNumber']}",
                    "state": StateEnum.CREATED,
                    "created": datetime.now(),
                },
            )
    except:
        return 400, "Error saving to database !", {}

    return 200, "Email sent successfully !", {}

def main(input_json):
    logging.info(f"Launched with {input_json}")
    input_dict = json.load(open(input_json))

    logging.info(f"Starting pull_config_files")
    code, msg, input_dict = pull_config_files(input_dict)
    logging.info(f"Code: {code}")
    logging.info(f"Message: {msg}")
    if code != 200:
        exit(1)

    # updating credentials to use local env
    input_dict["exits"][0]["kwargs"]["ursgal_credentials"]["credentials_lookup"][
        1
    ].update(
        {
            "secret_store": "env",
            "user": "U_MYLABDATA_USER",
            "password": "U_MYLABDATA_PASSWORD",
        }
    )

    logging.info(f"Starting list_mylabdata_file")
    code, msg, input_dict = list_mylabdata_file(input_dict)
    logging.info(f"Code: {code}")
    logging.info(f"Message: {msg}")
    if code != 200:
        exit(1)
    for f in input_dict["mylabdata_files"]:
        logging.info(f)

    logging.info(f"Starting pull_fcs_files")
    code, msg, input_dict = pull_fcs_files(input_dict)
    logging.info(f"Code: {code}")
    logging.info(f"Message: {msg}")
    if code != 200:
        exit(1)

    logging.info(f"Starting validate_meta_data_excel")
    code, msg, input_dict = validate_meta_data_excel(input_dict)
    logging.info(f"Code: {code}")
    logging.info(f"Message: {msg}")
    if code != 200:
        exit(1)

    logging.info(f"Starting validate_plate_csv")
    code, msg, input_dict = validate_plate_csv(input_dict)
    logging.info(f"Code: {code}")
    logging.info(f"Message: {msg}")
    if code != 200:
        exit(1)

    input_dict["exits"][0]["kwargs"]["ursgal_credentials"]["credentials_lookup"][
        1
    ].update(
        {
            "secret_store": "akv",
            "user": "U-MYLABDATA-USER",
            "password": "U-MYLABDATA-PASSWORD",
        }
    )
    logging.info(f"Starting start_prefect_pipeline")
    code, msg, input_dict = start_prefect_pipeline(input_dict)
    logging.info(f"Code: {code}")
    logging.info(f"Message: {msg}")
    if code != 201:
        exit(1)
    breakpoint()


if __name__ == "__main__":
    pd.set_option("display.max_columns", 100)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_json",
        dest="input_json",
        help="Validation json specifying a list of dicts with which input_json field maps to which excel cell",
        required=True,
    )
    args = parser.parse_args()

    main(args.input_json)
