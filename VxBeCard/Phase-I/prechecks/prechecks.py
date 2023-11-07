from time import sleep

def pullConfigFiles(**kwargs):
    sleep(5)
    kwargs["xx"] = "excelValidation"
    kwargs["bb"] = {"xx": 1, "yy": 2}
    print(kwargs)
    return 200, "All entered fields match the excel metadata from MyLabData.", kwargs

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