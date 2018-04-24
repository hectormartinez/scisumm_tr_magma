import ast
import argparse
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import classification_report
import numpy as np

from scisumm_io_utils import system_variables
from scisumm_io_utils import Article,Section,Sentence
from scisumm_io_utils import Entry
from scisumm_io_utils import read_XML,export_to_file,instance_sentence_list,get_entries_from_folder,get_training_entries_from_file
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description='Scisumm shared task data ')
    parser.add_argument('--infile',default="../train.txt")
    args = parser.parse_args()

    entries,labels = get_training_entries_from_file(args.infile)
    X = []
    vectorizer = DictVectorizer()
    for e in entries:
        X.append(e.featurize())

    kf = KFold(5)

    X = vectorizer.fit_transform(X)
    Y = np.array(labels)
    gold_labels = []
    pred_labels = []
    for train_index, test_index in kf.split(X):
        X_train, X_test = X[train_index], X[test_index]
        Y_train, Y_test = Y[train_index], Y[test_index]
        mdl = LogisticRegression()
        mdl.fit(X_train,Y_train)
        pred_labels.extend(mdl.predict(X_test))
        gold_labels.extend(Y_test)
    print(set(gold_labels))
    print(set(pred_labels))
    print(classification_report(gold_labels,pred_labels))

if __name__ == '__main__':
    main()
