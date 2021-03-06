import os
import shutil
import zipfile
from distutils.dir_util import copy_tree
from os.path import abspath, dirname, exists, join
from tqdm import tqdm

import requests


def download_TextComplexityDE19():

    """
    Download the TextComplexityDE dataset from Github Repository.
    Contact Badak Naderi (babak.naderi[at]tu-berlin.de)
    for further support concerning the dataset itself.
    Written by Leo Nguyen. Contact Xenovortex, if problems arises.
    """

    # url of dataset github repository
    url = "https://github.com/babaknaderi/TextComplexityDE.git"

    # create folder for dataset (if it doesn't exist yet)
    download_to_path = join(dirname(dirname(dirname(abspath(__file__)))), "data")
    if not exists(download_to_path):
        os.makedirs(download_to_path)

    # check if data folder already has subfolder TextComplexityDE
    # , if no: download github repository to folder
    if "TextComplexityDE19" not in os.listdir(download_to_path):
        # create temp folder to download github repository
        if not exists(join(download_to_path, "temp")):
            os.makedirs(join(download_to_path, "temp"))
        os.system(
            "git clone {} {}".format(url, join(download_to_path, "temp"))
        )  # Repo.clone_from(url, join(download_to_path, "temp"))
        # clean up downloaded repository
        shutil.rmtree(join(download_to_path, "temp", ".git"))
        os.remove(join(download_to_path, "temp", ".gitignore"))
        os.remove(join(download_to_path, "temp", "LICENSE"))
        os.remove(join(download_to_path, "temp", "README.md"))
        # copy content from temp folder to data folder
        copy_tree(join(download_to_path, "temp"), download_to_path)
        # delete temp folder
        shutil.rmtree(join(download_to_path, "temp"))
    else:
        print("Folder data already contains TextComplexityDE19. Skip download.")


def download_Weebit():

    """
    Downloads the Weebit dataset from
    an online repository to the
    text-analytics-project/data folder
    """
    # url of dataset github repository
    url = (
        "https://zenodo.org/record/1219041/"
        "files/nishkalavallabhi/"
        "OneStopEnglishCorpus-bea2018.zip?"
        "download=1"
    )

    # path to which the dataset will be saved
    download_to_path = join(dirname(dirname(dirname(abspath(__file__)))), "data")

    # create folder for dataset if it does not exist
    if not exists(download_to_path):
        os.makedirs(download_to_path)

    path_with_name = join(download_to_path, "weebit.zip")

    # create folder for dataset (if it doesn't exist yet)
    r = requests.get(url)

    with open(path_with_name, "wb") as file:
        file.write(r.content)

    with zipfile.ZipFile(path_with_name, "r") as zip_ref:
        zip_ref.extractall(download_to_path)

    extracted_name = join(
        download_to_path, "nishkalavallabhi-" "OneStopEnglishCorpus-" "089be0f"
    )
    renamed_extracted = join(download_to_path, "WeebitDataset")

    os.remove(path_with_name)
    os.rename(extracted_name, renamed_extracted)


def download_dw_set():
    """
    Downloads the dw dataset from an
    online repository to the
    text-analytics-project/data folder
    """

    url = "https://github.com/shlomihod/" "deep-text-eval/raw/master/data/dw/dw.h5"

    # path to which the dataset will be saved
    download_to_path = join(dirname(dirname(dirname(abspath(__file__)))), "data")

    # create folder for dataset if it does not exist
    if not exists(download_to_path):
        os.makedirs(download_to_path)

    # create subfolder dw if it does not exist yet
    if not exists(join(download_to_path, "dw")):
        os.makedirs(join(download_to_path, "dw"))

    path_with_name = join(download_to_path, "dw", "dw.h5")

    # create folder for dataset (if it doesn't exist yet)
    r = requests.get(url)

    with open(path_with_name, "wb") as file:
        file.write(r.content)


def download_file_from_google_drive(id, destination):
    # taken from https://gist.github.com/joshtch/8e51c6d40b1e3205d1bb2eea18fb57ae and modified
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()
    response = session.get(URL, params={"id": id}, stream=True)

    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token:
        params = {"id": id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    CHUNK_SIZE = 32 * 1024
    # TODO: this doesn't seem to work; there's no Content-Length value in header?
    total_size = int(response.headers.get("content-length", 0))

    with tqdm(desc=destination, total=total_size, unit="B", unit_scale=True) as pbar:
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    pbar.update(CHUNK_SIZE)
                    f.write(chunk)
