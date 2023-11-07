from time import sleep

def excelValidation(**kwargs):
    sleep(5)
    return 200, "All entered fields match the excel metadata from MyLabData.", {"xx": "excelValidation", "bb": {"xx": 1, "yy": 2}}

def myLabDataValidation(**kwargs):
    sleep(5)
    return 400, "0 fsc files found !", {"xx": "myLabDataValidation", "cc": "XYZ"}

def testValidation(**kwargs):
    sleep(3)
    return 200, "Success !!!", {}

def submitForm(**kwargs):
    sleep(1)
    if hasattr(kwargs, "_validation") and kwargs["_validation"] != 200:
        return 400, "Data clean process not started !", {}
    else :
        return 200, "Data clean process submitted. An email sill be sent to inform you about the progress of the pipeline.", {}