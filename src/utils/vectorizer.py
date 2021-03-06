from sklearn.feature_extraction.text import (
    CountVectorizer,
    HashingVectorizer,
    TfidfVectorizer,
)
from utils import preprocessing, to_dataframe, word2vec
import numpy as np


def vectorizer_wrapper(
    data,
    vectorizer="tfidf",
    stopwords=None,
    return_vectorizer=False,
    pretrained=False,
    print_path=False,
):
    """Wrapper to combine word2vec wrapper with the count/tfidf/hashing vectorizer wrapper.

       Written by Leo Nguyen. Contact Xenovortex, if problems arises.

    Args:
        data (numpy array): 1d array containing sentences
        filename (str): name of h5 file to load (run preprocessing first)
        vectorizer (str, optional): Select the vectorizer type. Implemented so far are: 'tfidf', 'count', 'hash'. Defaults to 'tfidf'.
        stopwords (list, optional): List of stopwords. Defaults to None.
        return_vectorizer (bool, optional): Return vectorizer model if true. Defaults to False.
        pretrained (bool, optional): if True, finetune the pretrained model instead of training from scratch
        print_path (bool, optional): print save path of the trained word2vec model. default: True
    """

    if vectorizer == "word2vec":
        # tokenization + stopword removal
        corpus = preprocessing.tokenizer(data, method="spacy")

        # vectorization
        return NN_vectorizer_wrapper(
            corpus,
            10,
            0.05,
            0.0001,
            120,
            10,
            7,
            "skip-gram",
            vectorizer,
            "train",
            return_vectorizer,
            False,
            print_path,
        )
    elif vectorizer == "pretrained_word2vec":
        # tokenization + stopword removal
        corpus = preprocessing.tokenizer(data, method="spacy")

        # vectorization
        return NN_vectorizer_wrapper(
            corpus,
            10,
            0.05,
            0.0001,
            120,
            10,
            7,
            "skip-gram",
            "word2vec",
            "train",
            return_vectorizer,
            True,
            print_path,
        )
    else:
        return ML_vectorizer_wrapper(data, vectorizer, stopwords, return_vectorizer)


def ML_vectorizer_wrapper(
    data, vectorizer="tfidf", stopwords=None, return_vectorizer=False
):
    """Takes in a numpy array of sentences and perform the selected vectorizer on the data.
       Returns a numpy array of sentence features represented by number vectors.

       Written by Leo Nguyen. Contact Xenovortex, if problems arises.

    Args:
        data (numpy array): 1d array containing sentences
        vectorizer (str, optional): Select the vectorizer type. Implemented so far are: 'tfidf', 'count', 'hash'. Defaults to 'tfidf'.
        stop_words (list, optional): List of stopwords. Defaults to None.
        return_vectorizer (bool, optional): Return vectorizer model if true. Defaults to False.

    Returns:
        features [scipy sparse matrix (csr)]: document-term matrix with dimension (number of sentences, features per sentence)
    """

    # apply selected vectorizer
    if vectorizer == "tfidf":
        vec = TfidfVectorizer(encoding="ISO-8859-1", stop_words=stopwords)
        features = vec.fit_transform(data)
    elif vectorizer == "count":
        vec = CountVectorizer(encoding="ISO-8859-1", stop_words=stopwords)
        features = vec.fit_transform(data)
    elif vectorizer == "hash":
        vec = HashingVectorizer(encoding="ISO-8859-1", stop_words=stopwords)
        features = vec.fit_transform(data)
    else:
        raise ValueError(
            "Vectorizer {} not implemented. Please select one of the following options: 'tfidf', 'count', 'hash'.".format(
                vectorizer
            )
        )

    if return_vectorizer:
        return features, vec
    else:
        return features


def NN_vectorizer_wrapper(
    corpus,
    epochs,
    lr,
    min_lr,
    num_features,
    window_size=5,
    min_count=5,
    algorithm="skip-gram",
    vectorizer="word2vec",
    mode="train",
    return_vectorizer=False,
    pretrained=False,
    print_path=True,
):
    """Takes in a 2d list of sentences and perform the selected vectorizer on the data.
       Returns an array of sentence features represented by number vectors.

       Written by Leo Nguyen. Contact Xenovortex, if problems arises.

    Args:
        corpus (2d list): 2d list of tokens for each sentence
        epochs (int): number of epochs
        lr (double): start learning rate
        min_lr (double): end learning rate
        num_features (int): dimension of feature space
        window_size (int, optional): window size of word2vec. Defaults to 5.
        min_count (int, optional): ignore words that occur less than min_count. Defaults to 5.
        algorithm (str, optional): choose between "CBOW" and "skip-gram". Defaults to "skip-gram".
        vectorizer (str, optional): Select the vectorizer type. Implemented so far are: 'word2vec'. Defaults to 'word2vec'.
        mode (str, optional): train new word2vec model or load existing model (options: 'train' or 'load')
        return_vectorizer (bool, optional): Return vectorizer model if true. Defaults to False.
        pretrained (bool, optional): if True, finetune the pretrained model instead of training from scratch
        print_path (bool, optional): print save path of the trained word2vec model. default: True

    Return:
        features [2d array]: document-term matrix with dimension (number of sentences, features per sentence)
    """

    # apply selected vectorizer
    if vectorizer == "word2vec":
        model = word2vec.word2vec(
            corpus,
            epochs,
            lr,
            min_lr,
            num_features,
            window_size,
            min_count,
            algorithm,
            pretrained,
        )
        if mode == "train":
            model.train(print_path)
        elif mode == "load":
            model.load_wv()
        else:
            raise ValueError(
                "mode {} unknown. Please choose 'train' or 'load'".format(mode)
            )
        model.transform()
        features = model.features
    else:
        raise ValueError(
            "Vectorizer {} not implemented. Please one of the following options: 'word2vec'.".format(
                vectorizer
            )
        )

    if return_vectorizer:
        return features, model
    else:
        return features
