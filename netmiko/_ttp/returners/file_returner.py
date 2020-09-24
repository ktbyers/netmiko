import time
import logging
import os

_name_map_ = {"file_returner": "file"}

log = logging.getLogger(__name__)
ctime = time.strftime("%Y-%m-%d_%H-%M-%S")


def file_returner(D, **kwargs):
    """Method to write data into file
    Args:
        url (str): os path there to save files
        filename (str): name of the file
    """
    url = kwargs.get("url", "./Output/")
    filename = kwargs.get("filename", "output_{}.txt".format(ctime))
    # if no filename provided, add outputter name to filename
    if not kwargs.get("filename", False):
        filename = _ttp_["output_object"].name + "_" + filename
    # check if path exists already, create it if not:
    if not os.path.exists(url):
        os.mkdir(url)
    # save excel workbook to file:
    if hasattr(D, "save") and hasattr(D, "worksheets"):
        log.info("output.returner_file: saving excel workbook")
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        D.save(url + filename)
    # save data to text file
    else:
        log.info("output.returner_file: saving text results to file")
        with open(url + filename, "w") as f:
            if not isinstance(D, str):
                f.write(str(D))
            else:
                f.write(D)