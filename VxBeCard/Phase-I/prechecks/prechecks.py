from time import sleep

def pullConfigFiles(**kwargs):
    sleep(5)
    kwargs["xx"] = "excelValidation"
    kwargs["bb"] = {"xx": 1, "yy": 2}
    return 200, "All entered fields match the excel metadata from MyLabData.", kwargs

def pullFcsFiles(**kwargs):
    sleep(5)
    kwargs["xx"] = "myLabDataValidation"
    kwargs["cc"] = "XYZ"
    return 400, "0 fsc files found !", kwargs

def validateExcelMetadataFile(**kwargs):
    sleep(3)
    if kwargs["studyNumber"] == '11':
        return 200, "Success !!!", kwargs
    else:
        return 400, "Error !!!", kwargs