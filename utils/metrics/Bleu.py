import os
from multiprocessing import Pool
import re
import nltk
from nltk.translate.bleu_score import SmoothingFunction
import random
from utils.metrics.Metrics import Metrics


class Bleu(Metrics):
    def __init__(self, test_text='', real_text='', gram=3):
        super().__init__()
        self.name = 'Bleu'
        self.test_data = test_text
        self.real_data = real_text
        self.gram = gram
        self.sample_size = 200
        self.reference = None
        self.is_first = True

    def get_name(self):
        return self.name

    def get_score(self, is_fast=True, ignore=False):
        if ignore:
            return 0
        if self.is_first:
            self.get_reference()
            self.is_first = False
        if is_fast:
            return self.get_bleu_fast()
        return self.get_bleu_parallel()

    def get_reference(self):
        if self.reference is None:
            reference = list()

            with open(self.real_data) as real_data:
                for text in real_data:
                    text = re.sub("\t", " ", text).split()
                    #text = nltk.word_tokenize(text)
                    reference.append(text)
            # randomly choose a portion of test data
            # In-place shuffle
            random.shuffle(reference)
            len_ref = len(reference)
            portion=0.5
            reference = reference[:int(portion * len_ref)]

            self.reference = reference
            return reference
        else:
            return self.reference

    def get_bleu(self):
        ngram = self.gram
        bleu = list()
        reference = self.get_reference()
        weight = tuple((1. / ngram for _ in range(ngram)))
        cnt=0
        with open(self.test_data) as test_data:
            for hypothesis in test_data:
                if(cnt>=self.sample_size):
                    break
                cnt+=1
                hypothesis = re.sub("\t", " ", hypothesis).split()
                #hypothesis = nltk.word_tokenize(hypothesis)
                bleu.append(nltk.translate.bleu_score.sentence_bleu(reference, hypothesis, weight,
                                                                    smoothing_function=SmoothingFunction().method1))
        return sum(bleu) / len(bleu)

    def calc_bleu(self, reference, hypothesis, weight):
        return nltk.translate.bleu_score.sentence_bleu(reference, hypothesis, weight,
                                                       smoothing_function=SmoothingFunction().method1)

    def get_bleu_fast(self):
        reference = self.get_reference()
        # random.shuffle(reference)
        reference = reference[0:self.sample_size]
        return self.get_bleu_parallel(reference=reference)

    def get_bleu_parallel(self, reference=None):
        ngram = self.gram
        if reference is None:
            reference = self.get_reference()
        weight = tuple((1. / ngram for _ in range(ngram)))
        pool = Pool(os.cpu_count())
        result = list()
        with open(self.test_data) as test_data:
            for hypothesis in test_data:
                hypothesis = re.sub("\t", " ", hypothesis).split()
                #text = nltk.word_tokenize(text.lower())
                #hypothesis = nltk.word_tokenize(hypothesis)
                result.append(pool.apply_async(self.calc_bleu, args=(reference, hypothesis, weight)))
        score = 0.0
        cnt = 0
        for i in result:
            score += i.get()
            cnt += 1
        pool.close()
        pool.join()
        return score / cnt
