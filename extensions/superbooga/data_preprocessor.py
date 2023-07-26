"""
This module contains utils for preprocessing the text before converting it to embeddings.

- TextPreprocessorBuilder preprocesses individual strings.
    * lowering cases
    * converting numbers to words or characters
    * merging and stripping spaces
    * removing punctuation
    * removing stop words
    * lemmatizing
    * removing specific parts of speech (adverbs and interjections)
- TextSummarizer extracts the most important sentences from a long string using text-ranking.
"""

import pytextrank
import string
import spacy
import nltk
import math
import re

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from num2words import num2words

class TextPreprocessorBuilder:
     # Define class variables as None initially
    _stop_words = None
    _lemmatizer = None

    @classmethod
    def initialize_class_variables(cls):
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        cls._stop_words = set(stopwords.words('english'))
        cls._lemmatizer = WordNetLemmatizer()

    def __init__(self, text: str):
        # Initialize class variables if they haven't been initialized
        if TextPreprocessorBuilder._stop_words is None or TextPreprocessorBuilder._lemmatizer is None:
            self.initialize_class_variables()
        self.text = text

    def to_lower(self):
        # Match both words and non-word characters
        tokens = re.findall(r'\b\w+\b|\W+', self.text)
        for i, token in enumerate(tokens):
            # Check if token is a word
            if re.match(r'^\w+$', token):
                # Check if token is not an abbreviation or constant
                if not re.match(r'^[A-Z]+$', token) and not re.match(r'^[A-Z_]+$', token):
                    tokens[i] = token.lower()
        self.text = "".join(tokens)
        return self

    def num_to_word(self, min_len: int = 1):
        # Match both words and non-word characters
        tokens = re.findall(r'\b\w+\b|\W+', self.text)
        for i, token in enumerate(tokens):
            # Check if token is a number of length `min_len` or more
            if token.isdigit() and len(token) >= min_len:
                # This is done to pay better attention to numbers (e.g. ticket numbers, thread numbers, post numbers)
                # 740700 will become "seven hundred and forty thousand seven hundred".
                tokens[i] = num2words(int(token)).replace(",","") # Remove commas from num2words.
        self.text = "".join(tokens)
        return self


    def num_to_char_long(self, min_len: int = 1):
        # Match both words and non-word characters
        tokens = re.findall(r'\b\w+\b|\W+', self.text)
        for i, token in enumerate(tokens):
            # Check if token is a number of length `min_len` or more
            if token.isdigit() and len(token) >= min_len:
                # This is done to pay better attention to numbers (e.g. ticket numbers, thread numbers, post numbers)
                # 740700 will become HHHHHHEEEEEAAAAHHHAAA
                convert_token = lambda token: ''.join((chr(int(digit) + 65) * (i + 1)) for i, digit in enumerate(token[::-1]))[::-1]
                tokens[i] = convert_token(tokens[i])
        self.text = "".join(tokens)
        return self
    
    def num_to_char(self, min_len: int = 1):
        # Match both words and non-word characters
        tokens = re.findall(r'\b\w+\b|\W+', self.text)
        for i, token in enumerate(tokens):
            # Check if token is a number of length `min_len` or more
            if token.isdigit() and len(token) >= min_len:
                # This is done to pay better attention to numbers (e.g. ticket numbers, thread numbers, post numbers)
                # 740700 will become HEAHAA
                tokens[i] = ''.join(chr(int(digit) + 65) for digit in token)
        self.text = "".join(tokens)
        return self
    
    def merge_spaces(self):
        self.text = re.sub(' +', ' ', self.text)
        return self
    
    def strip(self):
        self.text = self.text.strip()
        return self
        
    def remove_punctuation(self):
        self.text = self.text.translate(str.maketrans('', '', string.punctuation))
        return self

    def remove_stopwords(self):
        self.text = "".join([word for word in re.findall(r'\b\w+\b|\W+', self.text) if word not in self._stop_words])
        return self
    
    def remove_specific_pos(self):
        """
        In the English language, adverbs and interjections rarely provide meaningul information.
        Removing them improves the embedding precision. Don't tell JK Rowling, though.
        """
        # Match both words and non-word characters
        tokens = re.findall(r'\b\w+\b|\W+', self.text)

        # Exclude adverbs and interjections
        excluded_tags = ['RB', 'RBR', 'RBS', 'UH']

        for i, token in enumerate(tokens):
            # Check if token is a word
            if re.match(r'^\w+$', token):
                # Part-of-speech tag the word
                pos = nltk.pos_tag([token])[0][1]
                # If the word's POS tag is in the excluded list, remove the word
                if pos in excluded_tags:
                    tokens[i] = ''
        self.text = "".join(tokens)
        return self

    def lemmatize(self):
        self.text = "".join([self._lemmatizer.lemmatize(word) for word in re.findall(r'\b\w+\b|\W+', self.text)])
        return self

    def build(self):
        return self.text

class TextSummarizer:
    _nlp_pipeline = None

    @staticmethod
    def load_nlp_pipeline():
        # Lazy-load it.
        if TextSummarizer._nlp_pipeline is None:
            TextSummarizer._nlp_pipeline = spacy.load('en_core_web_sm')
            TextSummarizer._nlp_pipeline.add_pipe("textrank", last=True)
        return TextSummarizer._nlp_pipeline

    def process_long_text(self, text: str, min_num_sent: int) -> list[str]:
        """
        This function applies a text summarization process on a given text string, extracting 
        the most important sentences based on the principle that 20% of the content is responsible
        for 80% of the meaning (the Pareto Principle).

        Returns:
        list: A list of the most important sentences
        """

        nlp_pipeline = self.load_nlp_pipeline()
        doc = nlp_pipeline(text)

        num_sent = len(list(doc.sents))

        if num_sent >= min_num_sent:

            limit_phrases = math.ceil(len(doc._.phrases) * 0.20)  # 20% of the phrases, rounded up
            limit_sentences = math.ceil(num_sent * 0.20)  # 20% of the sentences, rounded up
            extracted_sentences = [str(sent) for sent in doc._.textrank.summary(limit_phrases=limit_phrases, limit_sentences=limit_sentences)]
            return extracted_sentences
        
        return [text]

    