from time import sleep

def excelValidation(**kwargs):
    sleep(5)
    return 200, "Success", {"xx": kwargs}

def myLabDataValidation(**kwargs):
    sleep(5)
    return 400, "Failure", {"xx": kwargs}