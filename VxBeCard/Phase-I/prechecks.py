
def excelValidation(**kwargs):
    return 1, "Success", {"xx": kwargs["aa"]}

def myLabDataValidation(**kwargs):
    return 0, "Failure", {"xx": kwargs["aa"]}