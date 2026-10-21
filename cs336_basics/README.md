# Byte-level tokenizer

## Introduction
This project implements a byte-level BPE tokenizer. This starts with the UTF-8 encoding of texts, where texts is transformed into a sequence of byte objects, our vocablury. Then, we add most frequent combination of these bytes object as new tokens in our vocabulry. For example, we may use TinyStoriesV2-GPT4-train as data set.

## Implementation

The implementation is designed so that if one decides to enlarge the vocabulry again, only 1 function is needed, namely enlarging_vocab. For this, one needs to store the return values of enlarging_vocab from the last time it is called. If it is the first time, one needs 3 functions to initialize the process. 

These functions, along with their help functions, are stored in tokenizer_functions.py. The first 3 functions do not return anything.

- download_token_data: Downloading the text file in UTF-8 encoding. 

The text is supposed be divided into smaller parts using a special character dividing_str, for example "<|endoftext|>" in TinyStoriesV2-GPT4-train.

The arguments are:

token_data_path:Path object, the directory to store the data

token_data_file_name : str, the name you want for the data

url:str, the url to find and download data

- count_tokens_in_file:  Find some regular expressions inside the text along with their frequency. These are stored in a dictionary. The regular expressions are encoded as a tuple of byte objects which together represent the UTF-8 encoding.

The arguments are:

file_path

PAT: str, this string tells the regex module which expressions to look for

dividing_str: the character that divides the text.


- initialize_vocab: Initializes the vocablury using 256 tokens which refere to elements of UTF-8 encoding. A special character b"<|endoftext|>" is inculded as the 257th token. There is 1 argument

special_tokens: list, a list of special tokens as strings wanted to be added to the vocabulry




- enlarging_vocab: This is the main function. There are two ways to use this function

**First time**: if it is the first time to call this function. 3 arguments are needed

vocab: dict, this is the return value of initialize_vocab

intended_vocab_size: int

byte_counts:dict,  this is the return value of count_tokens_in_file

**Return**: There are 6 returns 

vocab: dict, the enlarged vocab, 

byte_counts: dict, contains the regular expressions and their frequency. The regular expressions are encoded as a tuple of the enlarged vocabulary.

pairs_freq: dict, contains the frequency of each pair of vocablury elements appearing in the data set

pairs_freq_heap: heapq, a list of pairs and their frequency as a heapq object

pair_to_combs: dict, it provides the regular expressions in which each pair of tokens appear
   
merges: list, all the new tokens added. 

**Call againg** To call this function again, one needs to pass the returns of the previous call along with intended_vocab_size.



