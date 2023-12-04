from enum import Enum
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import spacy


class FeatureExtractorType(Enum):
    count_vectorizer = 'count_vectorizer'
    tfidf_word = 'tfidf_word'
    tfidf_char = 'tfidf_char'
    tfidf_char34 = 'tfidf_char34'
    count_char = 'count_char'
    spacy_nl_sm = 'spacy_nl_sm'
    spacy_nl_md = 'spacy_nl_md'
    spacy_nl_lg = 'spacy_nl_lg'


class SpacyFeatureExtractor:
    def __init__(self, model_name):
        self.nlp = spacy.load(model_name)

    def fit_transform(self, data):
        return [self.nlp(text).vector for text in data]


class FeatureExtractorFactory:
    @property
    def feature_extractors(self):
        return {
            FeatureExtractorType.count_vectorizer: CountVectorizer(analyzer='word', token_pattern=r'\w{2,}', max_features=5000),
            FeatureExtractorType.tfidf_word: TfidfVectorizer(analyzer='word', token_pattern=r'\w{2,}', max_features=5000),
            FeatureExtractorType.tfidf_char: TfidfVectorizer(analyzer='char', token_pattern=r'\w{2,}', ngram_range=(2, 3), max_features=5000),
            FeatureExtractorType.tfidf_char34: TfidfVectorizer(analyzer='char', token_pattern=r'\w{2,}', ngram_range=(3, 4), max_features=5000),
            FeatureExtractorType.count_char: CountVectorizer(analyzer='char', token_pattern=r'\w{2,}', max_features=5000),
            FeatureExtractorType.spacy_nl_sm: SpacyFeatureExtractor('nl_core_news_sm'),
            FeatureExtractorType.spacy_nl_md: SpacyFeatureExtractor('nl_core_news_md'),
            FeatureExtractorType.spacy_nl_lg: SpacyFeatureExtractor(
                'nl_core_news_lg')
        }

    @property
    def feature_extractor_types(self):
        return self.feature_extractors.keys()

    def create_feature_extractor(self, feature_extractor_type: FeatureExtractorType):
        if feature_extractor_type in self.feature_extractors:
            return self.feature_extractors[feature_extractor_type]
        else:
            raise ValueError("Invalid type")