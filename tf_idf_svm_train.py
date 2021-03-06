#!/usr/bin/env python3

import os
import sys
import argparse
import json
import re

import pickle

import spacy

# python -m spacy download de_core_news_sm --user
from spacy.lang.de import German

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn import svm
from sklearn.decomposition import PCA
from sklearn.decomposition import TruncatedSVD


def parse_args():
    parser = argparse.ArgumentParser(description='')

    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    parser.add_argument('-i', '--input_path', required=True, help='input path')
    parser.add_argument('-t', '--text_field', choices=['text', 'text_origin'], default='text_origin', help='input path')
    parser.add_argument('-o', '--output_path', required=True, help='output path')
    parser.add_argument('-p', '--pca_length', type=int, default=0, help='output path')
    args = parser.parse_args()
    return args


def gen_mapping(data):
    data_set = set(data)
    return {x: y for x, y in zip(data_set, range(len(data_set)))}


def run_mapping(mapping, data):
    return [mapping[x] for x in data]


def save(path, clf, year_mapping, tfidf_transformer, count_transformer):
    with open(path + '_svm.bin', 'wb') as f:
        f.write(pickle.dumps(clf))

    with open(path + '_mapping.bin', 'wb') as f:
        f.write(pickle.dumps(year_mapping))

    with open(path + '_tfidf.bin', 'wb') as f:
        f.write(pickle.dumps(tfidf_transformer))

    with open(path + '_count.bin', 'wb') as f:
        f.write(pickle.dumps(count_transformer))


# 33 Matthias
def main():
    args = parse_args()

    nlp = spacy.load('de_core_news_sm')

    texts = []
    school = []
    year = []
    course = []

    with open(args.input_path, 'r') as json_f:
        for i, line in enumerate(json_f):

            data_dict = json.loads(line)

            texts.append(data_dict[args.text_field])
            school.append(data_dict['school'])
            year.append(int(data_dict['year']))
            course.append(data_dict['course'])

    count_transformer = CountVectorizer()
    feature_count = count_transformer.fit_transform(texts)
    tfidf_transformer = TfidfTransformer().fit(feature_count)
    feature_tfidf = tfidf_transformer.transform(feature_count)

    print(feature_tfidf.shape)

    year_mapping = gen_mapping(year)
    year_target = run_mapping(year_mapping, year)

    if args.pca_length > 0:
        print('dimension reduction')
        pca_transform = TruncatedSVD(args.pca_length)

        pca_transform.fit(feature_tfidf)
        feature_tfidf_pca = pca_transform.transform(feature_tfidf)

        feature_train = feature_tfidf_pca
    feature_train = feature_tfidf

    print('train SVM')
    clf = svm.SVC()
    clf.fit(feature_train, year_target)

    save(args.output_path, clf, year_mapping, tfidf_transformer, count_transformer)


if __name__ == '__main__':
    sys.exit(main())
