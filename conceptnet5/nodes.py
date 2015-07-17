from __future__ import unicode_literals
"""
This module constructs URIs for nodes (concepts) in various languages. This
puts the tools in conceptnet5.uri together with stemmers that reduce words
to a root form, providing a higher-level interface to looking things up in
ConceptNet.

Currently, the only stemmer we use is Morphy, the built-in stemmer in WordNet,
which we apply to English concept names. Other languages are left alone.

The advantage of using Morphy is that its intended output is WordNet 3 lemmas,
a well-established set of strings. Other stemmers present a moving target that
is harder to define.
"""

from conceptnet5.language.english import english_filter
from conceptnet5.uri import concept_uri, split_uri
from wordfreq import simple_tokenize
from ftfy import fix_text
import re

LCODE_ALIASES = {
    # Pretend that all Chinese languages and variants are equivalent. This is
    # linguistically problematic, but it's also very helpful for aligning them
    # on terms where they actually are the same.
    #
    # This would mostly be a problem if ConceptNet was being used to *generate*
    # Chinese natural language text, and I don't believe it is.
    'cmn': 'zh',
    'yue': 'zh',
    'nan': 'zh',
    'zh_TW': 'zh',
    'zh_CN': 'zh',

    # An easier case: consider Bahasa Indonesia and Bahasa Malay to be the
    # same language, with code 'ms', because they're already 90% the same.
    # Many sources use 'ms' to represent the entire macrolanguage, with
    # 'zsm' to refer to Bahasa Malay in particular.
    'zsm': 'ms',
    'id': 'ms'
}


def standardize_as_list(text, token_filter=None):
    """
    Get a list of tokens or stems that appear in the text.

    The tokens can optionally be normalized and have stopwords removed.
    In practice, these will be used for English.
    Stopwords and an initial
    'to' will be stripped, unless this leaves nothing in the stem.

    >>> standardize_as_list('the dog', token_filter=english_filter)
    ['dog']
    >>> standardize_as_list('big dogs', token_filter=english_filter)
    ['big', 'dog']
    >>> standardize_as_list('big dogs')
    ['big', 'dogs']
    >>> standardize_as_list('to go', token_filter=english_filter)
    ['go']
    >>> standardize_as_list('the', token_filter=english_filter)
    ['the']
    >>> standardize_as_list('to', token_filter=english_filter)
    ['to']
    """
    text = fix_text(text)
    tokens = [token for token in simple_tokenize(text)]
    if token_filter is not None:
        tokens = token_filter(tokens)
    return tokens


def standardize_text(text, token_filter=None):
    """
    Get a string made from the tokens in the text. See
    standardize_as_list().
    """
    return '_'.join(standardize_as_list(text, token_filter))


def standardize_topic(topic):
    """
    Get a canonical representation of a Wikipedia topic, which may include
    a disambiguation string in parentheses. Returns a concept URI that
    may be disambiguated as a noun.

    >>> standardize_topic('Township (United States)')
    '/c/en/township/n/united_states'
    """
    # find titles of the form Foo (bar)
    topic = topic.replace('_', ' ')
    match = re.match(r'([^(]+) \(([^)]+)\)', topic)
    if not match:
        return standardized_concept_uri('en', topic)
    else:
        return standardized_concept_uri('en', match.group(1), 'n', match.group(2))


def standardized_concept_name(lang, text):
    """
    Make a normalized form of the given text in the given language. If the
    language is English, reduce words to their root form using the tools in
    conceptnet5.language.english. Otherwise, simply apply the function called
    `conceptnet5.uri.standardize_text`.

    >>> standardized_concept_name('en', 'this is a test')
    'this_be_test'
    >>> standardized_concept_name('es', 'ESTO ES UNA PRUEBA')
    'esto_es_una_prueba'
    """
    lang_filter = None
    if lang == 'en':
        lang_filter = english_filter
    else:
        lang_filter = None
    return standardize_text(text, lang_filter)

normalized_concept_name = standardized_concept_name


def standardized_concept_uri(lang, text, *more):
    """
    Make the appropriate URI for a concept in a particular language, including
    stemming the text if necessary, normalizing it, and joining it into a
    concept URI.

    Items in 'more' will not be stemmed, but will go through the other
    normalization steps.

    >>> standardized_concept_uri('en', 'this is a test')
    '/c/en/this_be_test'
    >>> standardized_concept_uri('en', 'this is a test', 'n', 'example phrase')
    '/c/en/this_be_test/n/example_phrase'
    """
    if lang in LCODE_ALIASES:
        lang = LCODE_ALIASES[lang]
    norm_text = standardized_concept_name(lang, text)
    more_text = [standardize_text(item) for item in more if item is not None]
    return concept_uri(lang, norm_text, *more_text)

normalized_concept_uri = standardized_concept_uri


def valid_concept_name(text):
    """
    Returns whether this text can be reasonably represented in a concept
    URI. This helps to protect against making useless concepts out of
    empty strings or punctuation.

    >>> valid_concept_name('word')
    True
    >>> valid_concept_name('the')
    True
    >>> valid_concept_name(',,')
    False
    >>> valid_concept_name(',')
    False
    >>> valid_concept_name('/')
    False
    >>> valid_concept_name(' ')
    False
    """
    return bool(standardize_text(text))

