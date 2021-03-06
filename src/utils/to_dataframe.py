import pandas as pd
import os
from os.path import join, abspath, dirname, isfile
from google_trans_new import google_translator
from sklearn.model_selection import train_test_split
import nlpaug.augmenter.word as naw
import spacy
from nltk.stem import SnowballStemmer
from utils import downloader, exploration, normalization

# from preprocessing import get_stopwords


def text_comp19_to_df():

    """
    Returns a pandas Dataframe object with
    the data of the TextComplexityDE19 dataset
    """

    # Path to relevant csv file
    csv_path = join(
        dirname(dirname(dirname(abspath(__file__)))),
        "data",
        "TextComplexityDE19/ratings.csv",
    )

    # read in csv file
    print("Check for TextComplexityDE19/ratings.csv")
    if isfile(csv_path):
        print("Reading in TextComplexityDE19/ratings.csv")
        corpus = pd.read_csv(csv_path, encoding="windows-1252")

    else:
        print("Downloading TextComplexityDE19 Dataset")
        downloader.download_TextComplexityDE19()
        print("Reading in TextComplexityDE19/ratings.csv")
        corpus = pd.read_csv(csv_path, encoding="windows-1252")

    # Rename columns and insert source of this dataframe for consistency
    corpus = corpus.rename(columns={"Sentence": "raw_text", "MOS_Complexity": "rating"})

    corpus.insert(2, "source", 0)

    # Delete all columns except the raw_text and the rating column
    corpus = corpus.drop(
        columns=[
            "ID",
            "Article_ID",
            "Article",
            "Votes_Complexity",
            "Std_Complexity",
            "Votes_Understandability",
            "MOS_Understandability",
            "Std_Understandability",
            "Vote_Lexical_difficulty",
            "MOS_Lexical_difficulty",
            "Std_Lexical_difficulty",
        ]
    )

    return corpus

def replace_rating(x):

    """
    Function to replace string ratings to int ratings.
    """
    if "Elementary" in str(x):
        return 0

    elif "Intermediate" in str(x):
        return 1

    elif "Advanced" in str(x):
        return 2

    elif "B2" and "C1" in str(x):
        return 1

    elif "B1" and not "C1" in str(x):
        return 0

    else:
        return 0

def weebit_to_df():

    """
    Returns a pandas Dataframe object with
    the translated data (from english to german)
    of the Weebit dataset.
    """

    # List paths of all .txt files

    print("Reading in Weebit Ele-Txt, Int-Txt, Adv-Txt")
    elementary_path = join(
        dirname(dirname(dirname(abspath(__file__)))),
        "data",
        "WeebitDataset",
        "Texts-SeparatedByReadingLevel",
        "Ele-Txt",
    )
    advanced_path = join(
        dirname(dirname(dirname(abspath(__file__)))),
        "data",
        "WeebitDataset",
        "Texts-SeparatedByReadingLevel",
        "Adv-Txt",
    )
    intermediate_path = join(
        dirname(dirname(dirname(abspath(__file__)))),
        "data",
        "WeebitDataset",
        "Texts-SeparatedByReadingLevel",
        "Int-Txt",
    )

    path_list = [elementary_path, advanced_path, intermediate_path]

    # Check for availability of Weebit dataset
    print("Check for weebit dataset")
    if not (
        isfile(elementary_path) and isfile(advanced_path) and isfile(intermediate_path)
    ):
        downloader.download_Weebit()

    # create dictionary for creation of dataframe
    data_dict = {"raw_text": [], "rating": [], "source": []}

    # Read in .txt files and write to dataframe
    for path in path_list:
        for filename in os.listdir(path):
            full_path_to_file = os.path.join(path, filename)

            # omit first line of each file, it contains the difficulty of the file
            omit = True
            str_list = []

            with open(full_path_to_file, encoding="windows-1252") as file:
                for line in file:
                    if omit:
                        omit = False
                        # write difficulty to dataframe
                        data_dict["rating"].append(replace_rating(line))
                        continue
                    str_list.append(replace_rating(line))

            # flatten list of line to one big string
            text = ""
            for i in range(0, len(str_list)):
                text += str_list[i]

            # create dataframe out of dictionary
            data_dict["raw_text"].append(text)
            data_dict["source"].append(1)

    weebit_data = pd.DataFrame(data_dict)

    # translate weebit dataset to german
    print("Translating Weebit dataset to german...")
    trans = google_translator()

    weebit_data["raw_text"] = weebit_data["raw_text"].apply(
        lambda x: trans.translate(x, lang_tgt="de")
    )

    return weebit_data


def store_translated_weebit_h5():
    """
    Saves the translated weebit dataset as a HDF5 file in the data folder.
    """
    # read in weebit dataset
    translated_weebit = weebit_to_df()

    # define filename of .HDF5 file
    filename = "Weebit_translated.h5"

    # define path of .HDF5 file
    h5_path = join(dirname(dirname(dirname(abspath(__file__)))), "data", filename)

    translated_weebit.to_hdf(h5_path, key="Weebit", mode="w")


def dw_to_df():

    """ "
    Returns a pandas Dataframe object with
    the data of the dw dataset
    """

    # .h5 file path
    h5_path = join(dirname(dirname(dirname(abspath(__file__)))), "data", "dw.h5")

    # Check for availability of dw set
    print("Check for dw dataset")
    if not isfile(h5_path):
        downloader.download_dw_set()

    # read in h5 file
    print("Reading in dw.h5")
    data = pd.HDFStore(h5_path, "r")

    # assign in h5 file contained dataframes to variables
    pages_df = data["pages_df"]
    paragraphs_df = data["paragraphs_df"]
    text_df = data["text_df"]

    # merge dataframes on url and append paragraphs and text to one dataframe
    merged = text_df.merge(pages_df, left_on="url", right_on="url")
    merged2 = paragraphs_df.merge(pages_df, left_on="url", right_on="url")
    joined = merged.append(merged2, ignore_index=True)

    # Rename, delete columns and insert source of this dataframe for consistency
    dw_set = joined.drop(
        columns=[
            "artikel_x",
            "rubrik_x",
            "title",
            "url",
            "y_x",
            "rubrik_y",
            "html",
            "artikel_y",
            "tags",
            "y_y",
        ],
    )
    dw_set.rename(columns={"text": "raw_text", "levels": "rating"}, inplace=True)
    dw_set.insert(2, "source", 2)
    dw_set["rating"] = dw_set["rating"].apply(lambda x: replace_rating(x))

    return dw_set


def all_data(use_textcomp19=False, use_weebit=False, use_dw=False):

    """
    returns one dataframe for all datasets specified with true as arguments.
    The datasets are also cleared of "\n" and other special symbols,
    numbers, whitespace sequences.
    Also word count and flesch readability index is added to data.
    """

    # load all datasets into dataframes and store them in variables
    if use_textcomp19 == True:
        text_comp19 = text_comp19_to_df()

    if use_dw == True:
        dw = dw_to_df()

    if use_weebit == True:
        # check if translated weebit dataset exists as .h5 file.
        print("Check if translated weebit dataset exists...")

        # define filename of .HDF5 file
        filename = "Weebit_translated.h5"

        # define path of .HDF5 file
        h5_path = join(dirname(dirname(dirname(abspath(__file__)))), "data", filename)

        if isfile(h5_path):
            # read in .HDF5 file
            weebit_h5obj = pd.HDFStore(h5_path, "r")
            weebit = weebit_h5obj["Weebit"]

        else:
            # store the translated weebit dataset in a .h5 file
            store_translated_weebit_h5()
            # read in .HDF5 file
            weebit_h5obj = pd.HDFStore(h5_path, "r")
            weebit = weebit_h5obj["Weebit"]

    # append all dataframes to one dataframe
    if use_dw and use_weebit and use_textcomp19:
        all_dataset = text_comp19.append(weebit, ignore_index=True)
        all_dataset = all_dataset.append(dw, ignore_index=True)

    if use_textcomp19 and not use_weebit and not use_dw:
        all_dataset = text_comp19

    if use_weebit and not use_textcomp19 and not use_dw:
        all_dataset = weebit

    if use_dw and not use_textcomp19 and not use_weebit:
        all_dataset = dw

    if use_dw and use_weebit and not use_textcomp19:
        all_dataset = dw.append(weebit, ignore_index=True)

    if use_textcomp19 and use_weebit and not use_dw:
        all_dataset = text_comp19.append(weebit, ignore_index=True)

    if use_textcomp19 and use_dw and not use_weebit:
        all_dataset = text_comp19.append(dw, ignore_index=True)


    # delete "\n" and other special symbols
    print("removing newline command")
    all_dataset.replace("\n", "", regex=True, inplace=True)

    # remove numbers from data
    print("removing numbers from data")
    all_dataset.raw_text.replace(r"\d", "", regex=True, inplace=True)

    # remove punctuation from data
    print("removing punctuation from data")
    all_dataset["raw_text"] = all_dataset["raw_text"].apply(
        lambda x: exploration.remove_punctuation(x)
    )

    # remove whitespace from data
    print("removing whitespace sequences from data")
    all_dataset["raw_text"] = all_dataset["raw_text"].apply(
        lambda x: exploration.remove_whitespace(x)
    )

    # Normalize Sentences
    print("Normalizing sentences")
    all_dataset["raw_text"] = all_dataset["raw_text"].apply(lambda x: x.lower())

    # add word count to data
    # print("adding word count to data")
    # all_dataset['word_count'] = all_dataset['raw_text'].str.findall(r'(\w+)').str.len()

    # add flesch readability index to data
    # print("adding flesch readability index to data")
    # all_dataset['flesch_readablty'] = all_dataset['raw_text'].apply(textstat.flesch_reading_ease)

    return all_dataset


def augmented_all(
    use_textcomp19=False,
    use_weebit=False,
    use_dw=False,
    backtrans=False,
    lemmatization=False,
    stemming=False,
    randword_swap=False,
    randword_del=False,
    test_size=0.1,
):

    """
    Returns the augmented training dataset
    and the test dataset of all specified data.

    backtrans : enables back and forth translation of the data
    lemmatization self explanatory
    stemming self explanatory
    randword_swap : enables randomly swapping words around sentences
    randword_del : enalbles randomly deleting words from sentences
    test_size : gives the ratio of test to train set

    train_set, test_set = augmented_all()

    """

    # Perform a Train-Test Split keeping dataset proportions the same
    print("perform train-test split keeping dataset proportions the same")

    all_dataset = all_data(use_textcomp19, use_weebit, use_dw)
    print("#####################",all_dataset[all_dataset["source"]==1])

    if use_textcomp19:
        text_comp_train, text_comp_test = train_test_split(
            all_dataset[all_dataset["source"] == 0], test_size=test_size
        )

    if use_weebit:
        weebit_train = all_dataset[all_dataset["source"] == 1]
        print(weebit_train)

    if use_dw:
        dw_train = all_dataset[all_dataset["source"] == 2]

    if use_textcomp19 and not use_weebit and not use_dw:                                  #0
        all_dataset_train = text_comp_train
        all_dataset_test = text_comp_test

    if use_weebit and not use_textcomp19 and not use_dw:                                   #1
        print("No weebit test set available!")
        all_dataset_train = weebit_train

    if use_dw and not use_weebit and not use_textcomp19:                                  #2
        print("No dw test set available!")
        all_dataset_train = dw_train
        all_dataset_test = dw_train # added so that dataset with only dw can be created

    if use_textcomp19 and use_weebit and not use_dw:                                       #01
        all_dataset_train = text_comp_train.append(weebit_train, ignore_index=True)
        all_dataset_test = text_comp_test

    if use_weebit and use_dw and not use_textcomp19:                                        #12
        print("No weebit and dw test set available!")
        all_dataset_train = weebit_train.append(dw_train, ignore_index=True)

    if use_textcomp19 and use_dw and not use_weebit:                                        #02
        all_dataset_train = text_comp_train.append(dw_train, ignore_index=True)
        all_dataset_test = text_comp_test

    if use_textcomp19 and use_weebit and use_dw:                                           # 012
        all_dataset_train = text_comp_train.append(weebit_train, ignore_index=True)
        all_dataset_train = all_dataset_train.append(dw_train, ignore_index=True)

        all_dataset_test = text_comp_test

    ## Augmentation of data
    print("Start augmenting Data...")

    # Back and forth translation of data
    if backtrans == True:

        print("Back and forth translation...")
        back_translation_aug = naw.BackTranslationAug(
            from_model_name="transformer.wmt19.de-en",
            to_model_name="transformer.wmt19.en-de",
        )
        if use_weebit:
            translated = all_dataset_train[all_dataset_train["source"] != 1]
        else:
            translated = all_dataset_train

        translated["raw_text"] = translated["raw_text"].apply(
            lambda x: back_translation_aug.augment(x)
        )

        all_dataset_train = all_dataset_train.append(translated, ignore_index=True)

    # Random word swap
    if randword_swap == True:
        print("Random word swap")
        aug1 = naw.RandomWordAug(action="swap")
        swapped_data = all_dataset_train
        swapped_data["raw_text"] = all_dataset_train["raw_text"].apply(
            lambda x: aug1.augment(x)
        )
        all_dataset_train = all_dataset_train.append(swapped_data, ignore_index=True)

    # Random word deletion
    if randword_del == True:

        print("Random word deletion")
        aug2 = naw.RandomWordAug()
        rand_deleted_data = all_dataset_train
        rand_deleted_data["raw_text"] = all_dataset_train["raw_text"].apply(
            lambda x: aug2.augment(x)
        )
        all_dataset_train = all_dataset_train.append(
            rand_deleted_data, ignore_index=True
        )

    # Lemmatization using spacy
    if lemmatization == True:

        print("lemmatizing")
        nlp = spacy.load("de_core_news_sm")
        all_dataset_train["raw_text"] = all_dataset_train["raw_text"].apply(
            lambda x: " ".join([y.lemma_ for y in nlp(x)])
        )

        all_dataset_test["raw_text"] = all_dataset_test["raw_text"].apply(
            lambda x: " ".join([y.lemma_ for y in nlp(x)])
        )

    # Stemming using
    if stemming == True:

        print("stemming")
        stemmer = SnowballStemmer("german")
        all_dataset_train["raw_text"] = all_dataset_train["raw_text"].apply(
            lambda x: stemmer.stem(x)
        )

        all_dataset_test["raw_text"] = all_dataset_test["raw_text"].apply(
            lambda x: stemmer.stem(x)
        )

    return all_dataset_train, all_dataset_test


def store_augmented_h5(
    filename="",
    use_textcomp19=False,
    use_weebit=False,
    use_dw=False,
    backtrans=False,
    lemmatization=False,
    stemming=False,
    randword_swap=False,
    randword_del=False,
    test_size=0.1,
):

    """
    Since the augmented dataset is a large file and
    all the preprocessing steps require a long time
    to finish it is reasonable to save this data once completed.

    Args:
    backtrans : enables back and forth translation of the data
    lemmatization : self explanatory
    stemming : self explanatory
    randword_swap : enables randomly swapping words around sentences
    randword_del : enables randomly deleting words from sentences
    test_size : gives the ratio of test to train set

    The file is saved in the same data folder where the original data also resides.
    filename = "filename.h5", keys ="train","test"
    """
    # Ask user for filename
    if filename == "":
        filename = input("Please enter filename with .h5 at the end")

    # define path of .HDF5 file
    h5_path = join(dirname(dirname(dirname(abspath(__file__)))), "data", filename)

    # Load augmented data into variables
    all_dataset_train, all_dataset_test = augmented_all(
        use_textcomp19,
        use_weebit,
        use_dw,
        backtrans,
        lemmatization,
        stemming,
        randword_swap,
        randword_del,
        test_size,
    )

    # Write augmented data to h5 file at the above path "h5_path"
    all_dataset_train.to_hdf(h5_path, key="train")
    all_dataset_test.to_hdf(h5_path, key="test")


def read_augmented_h5(filename=""):
    """
    Args: filename (default empty, but will be prompted to enter name)

    Returns the augmented data from the stored .HDF5 file.
    Similar to augmented_all() with the difference that the
    data is not generated but read instead.

    train_set, test_set = read_augmented_h5().
    """
    # Ask user for
    if filename == "":
        filename = input("Please enter filename with .h5 at the end")

    # define path of .HDF5 file
    h5_path = join(dirname(dirname(dirname(abspath(__file__)))), "data", filename)

    # read in .HDF5 file
    data = pd.HDFStore(h5_path)

    return data["train"], data["test"]


if __name__ == "__main__":
    store_augmented_h5(use_textcomp19=True)
