import json
import argparse
import os
import re

import ursgal
from github import Auth, Github
import pandas as pd


pd.set_option("display.max_columns", 100)

def pull_config_files(input_dict):
    """_summary_

    Args:
        input_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        auth = Auth.Token(os.getenv("CONFIG_REPO_TOKEN"))
        g = Github(auth=auth)
        repo = g.get_repo(os.getenv("CONFIG_REPO"))
        folder = input_dict["folder"]
        for exit in input_dict["exits"]:
            for file_key, filename in exit["additional_files"].items():
                file_content = repo.get_contents(
                    f"{folder}/{filename}", os.getenv("CONFIG_REPO_BRANCH")
                )
                exit["kwargs"][file_key] = json.loads(
                    file_content.decoded_content.decode()
                )
        meta_data_excel_mapping_location = os.path.join(
            input_dict["folder"], 
            input_dict["prechecks_config"]["meta_data_excel_mapping"]
        )
        meta_data_excel_mapping = repo.get_contents(
            meta_data_excel_mapping_location, 
            os.getenv("CONFIG_REPO_BRANCH")
        ).decoded_content.decode()
        input_dict["prechecks_config"]["meta_data_excel_mapping"] = meta_data_excel_mapping
    except:
        return 400, f"Cannot get configuration files !", input_dict

    return 200, "All configuration files pulled successfully.", input_dict


def pull_fcs_files(input_dict):
    """_summary_

    Args:
        input_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        fcs_uri_list = _get_file_list(
            input_dict,
            input_dict["prechecks_config"]["input_file_pattern"],
            ursgal.uftypes.flow_cytometry.FCS,
        )
        # try:
        #     ursgal.instances.ucredential_manager.add_credentials(
        #         input_dict["exits"][0]["additional_files"]["ursgal_credentials"][
        #             "credentials_lookup"
        #         ]
        #     )
        #     equipment_id = input_dict["instrumentSapId"]
        #     task_id = input_dict["myLabDataTaskId"]
        #     storage_base = f"mylabdata://{input_dict['prechecks']['mylabdata_api_backend_url']}/{equipment_id}/{task_id}"

        #     ursgal.config["certificates"][
        #         input_dict["prechecks"]["mylabdata_api_backend_url"]
        #     ] = False
        #     try:
        #         file_list_mld = ursgal.UFile(
        #             f"{storage_base}#dummy.txt"
        #         ).io.list_container_items()
        #     except:
        #         return (400, f"Cannot connect to {storage_base}", input_dict)

        #     fcs_uri_list = []
        #     for file in file_list_mld:
        #         if re.search(input_dict["prechecks"]["input_file_pattern"], file):
        #             fcs_uri_list.append(
        #                 f"{storage_base}?uftype={ursgal.uftypes.flow_cytometry.FCS}#{file}"
        #             )

        len_fcs_file_list = len(fcs_uri_list)
        if len_fcs_file_list == 0:
            return 400, "0 fsc files found !", input_dict

        input_dict["fcs_uri_list"] = fcs_uri_list

    except:
        return 400, "Error getting fcs files !", input_dict

    return 200, f"{len_fcs_file_list} fsc files found !", input_dict


def _get_file_list(input_dict, file_pattern, uftype):
    ursgal.instances.ucredential_manager.add_credentials(
        input_dict["exits"][0]["additional_files"]["ursgal_credentials"][
            "credentials_lookup"
        ]
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


def validate_meta_data_excel(input_dict):
    #print(input_dict)
    #return 200, "All meta data fields match excel sheet", input_dict
    """Validate Meta Data Excel entries agains input_dict based on a validation_json.

    Args:
        input_dict (dict): Submitted User data (jsonforms)
        # excel_file (MS Excel File): Excel sheet with meta data
        # validation_json (json): JSon with mappings for all fields
        #     input_dict.field <-> excel.sheet.row.column. Defaults to None.

    Returns:
        _type_: _description_
    """
    checks = input_dict["prechecks_config"]["meta_data_excel_mapping"]

    excel_files = _get_file_list(
        input_dict,
        input_dict["prechecks_config"]["meta_data_input_file_pattern"],
        uftype=ursgal.uftypes.mx.METADATA_XLSX,
    )
    if len(excel_files) != 1:
        return 400, "Found more than 1 execl sheet matchin pattern !", input_dict

    meta_xls = pd.ExcelFile(excel_files[0].path)
    msg = []
    for check in checks:
        json_field = check["input_json_field"]
        xls_df = meta_xls.parse(sheet_name=check["sheet"], header=None)
        check["input_value"] = input_dict.get(
            json_field, f"{json_field} was not specified in input_dict"
        )
        check["meta_data_excel_value"] = xls_df.iloc[
            check["row"] - 1, check["column"] - 1
        ]
        if check["meta_data_excel_value"] != check["input_value"]:
            msg.append(
                "Value for '{input_json_field}' in sheet '{sheet}' (row '{row}', "
                " column '{column}') is '{meta_data_excel_value}' "
                "yet recieved '{input_value}' as input".format(
                    **check,
                )
            )
    if len(msg) > 0:
        return 400, ". ".join(msg), input_dict
    else:
        return 200, "All meta data fields match excel sheet", input_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-x",
        "--excel_meta_file",
        dest="excel_file",
        help="Excel input file with meta data",
        required=True,
    )
    parser.add_argument(
        "-l",
        "--validation_json",
        dest="validation_json",
        help="Validation json specifying a list of dicts with which input_json field maps to which excel cell",
        required=True,
    )
    args = parser.parse_args()

    response = validate_meta_data_excel(
        {
            "task_id": "22-10011464-C4",
            "eln number": "ELN185065",
        },
        excel_file=args.excel_file,
        validation_json=args.validation_json,
    )
    print(response)
