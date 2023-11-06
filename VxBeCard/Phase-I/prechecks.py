
def excelValidation(**kwargs):
    return 200, "Success", {"xx": kwargs["aa"]}

def myLabDataValidation(**kwargs):
    return 400, "Failure", {"xx": kwargs["aa"]}