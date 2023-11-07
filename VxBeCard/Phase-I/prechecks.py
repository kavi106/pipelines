from time import sleep

def excelValidation(**kwargs):
    sleep(5)
    return 200, "All entered fields match the excel metadata from MyLabData.", {"xx": "excelValidation", "bb": {"xx": 1, "yy": 2}}

def myLabDataValidation(**kwargs):
    sleep(5)
    return 200, "0 fsc files found !", {"xx": "myLabDataValidation", "cc": "XYZ"}

def testValidation(**kwargs):
    sleep(3)
    return 200, "Success !!!", {}