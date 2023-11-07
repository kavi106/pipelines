from time import sleep

def excelValidation(**kwargs):
    sleep(5)
    return 200, "Success", {"xx": "excelValidation", "bb": {"xx": 1, "yy": 2}}

def myLabDataValidation(**kwargs):
    sleep(5)
    return 400, "Failure", {"xx": "myLabDataValidation", "cc": "XYZ"}

def testValidation(**kwargs):
    sleep(3)
    return 400, "Failure", {}