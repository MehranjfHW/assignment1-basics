
# Byte-Level BPE Tokenizer

A Python implementation of a **byte-level Byte Pair Encoding (BPE) tokenizer**, developed while studying [Stanford CS336: Language Modeling from Scratch](https://github.com/stanford-cs336/assignment1-basics).

The implementation focuses on efficient BPE vocabulary training through incremental frequency updates, reverse indexing, and heap-based pair selection.

It also supports **extending an existing vocabulary** without restarting the entire training process.

## 1. Overview

Byte Pair Encoding (BPE) is a subword tokenisation algorithm that constructs a vocabulary by repeatedly merging the most frequent adjacent token pairs in a training corpus.

The algorithm starts with the 256 possible byte values. Text is encoded using UTF-8, allowing the vocabulary to represent text in any language.

At each iteration, the algorithm selects the most frequent adjacent token pair, merges its occurrences, and adds the resulting token to the vocabulary.

The implementation supports:

- UTF-8 byte-level tokenisation
- Regular-expression-based pre-tokenisation
- Special tokens, such as `<|endoftext|>`
- Incremental pair-frequency updates
- Heap-based selection of the most frequent pair
- Resuming BPE vocabulary training

The [TinyStories dataset](https://huggingface.co/datasets/roneneldan/TinyStories) is used as an example training corpus.

## 2. Algorithm

The training algorithm consists of the following steps.

### Step 1: Vocabulary initialisation

The initial vocabulary contains all 256 possible single-byte values:

```python
vocab = {i: bytes([i]) for i in range(256)}
```

Special tokens can also be added to the vocabulary.

For example, TinyStories uses `<|endoftext|>` as a story separator.

Including this special token gives an initial vocabulary of 257 tokens.

### Step 2: Pre-tokenisation

The training text is divided at specified special-token boundaries and processed using a regular expression.

Each regex match is encoded in UTF-8 and represented as a tuple of single-byte objects.

The frequency of each distinct pre-token is recorded in the dictionary `byte_counts`.

For example:

```python
byte_counts = {
    (b'l', b'o', b'w'): 10,
    (b'n', b'e', b'w'): 7
}
```

The dictionary values represent the number of occurrences of each pre-token in the training corpus.

BPE merges are restricted to individual pre-tokens and do not cross pre-token boundaries.

### Step 3: Pair-frequency calculation

The algorithm identifies all adjacent pairs within each pre-token.

Their frequencies are calculated by weighting each pair occurrence by the frequency of its containing pre-token.

For example:

```python
(b'l', b'o', b'w')
```

contributes to the frequencies of:

```python
(b'l', b'o')
(b'o', b'w')
```

These frequencies are stored in the dictionary `pairs_freq`.

### Step 4: Selecting the most frequent pair

The pair with the highest frequency is selected.

If several pairs have the same frequency, the lexicographically greatest pair is chosen.

A priority queue implemented using Python's `heapq` module is used to select the pair efficiently.

### Step 5: Merging the selected pair

The selected pair is concatenated to create a new token.

For example:

```python
best_pair = (b'l', b'o')
new_token = b'lo'
```

The sequence:

```python
(b'l', b'o', b'w')
```

becomes:

```python
(b'lo', b'w')
```

All non-overlapping occurrences of the selected pair are merged from left to right.

The new token is added to `vocab`, and the selected pair is appended to the ordered `merges` list.

### Step 6: Updating the training state

After each merge, the algorithm updates:

- `byte_counts`: the current token sequences and their frequencies
- `pairs_freq`: the frequencies of adjacent token pairs
- `pair_to_combs`: the reverse index of pairs to pre-tokens
- `pairs_freq_heap`: the priority queue used for pair selection

Rather than rebuilding these structures from scratch, the implementation updates only the affected entries.

### Step 7: Repeating the process

The algorithm repeats the selection, merging, and updating steps until the requested vocabulary size is reached or no valid adjacent pairs remain.

For a vocabulary size of 10,000 with one special token:

- Initial byte tokens: 256
- Special tokens: 1
- Learned BPE merges: 9,743

## 3. Optimisation Techniques

A straightforward BPE implementation repeatedly scans the training corpus and recalculates pair frequencies after every merge.

This implementation uses three complementary optimisations to reduce redundant computations.

### 3.1 Reverse index: `pair_to_combs`

The reverse index maps each adjacent token pair to the set of distinct pre-tokens containing that pair.

For example:

```python
pair_to_combs[(b'a', b'b')] = {
    (b'a', b'b', b'c'),
    (b'a', b'b', b'd')
}
```

When `(b'a', b'b')` is selected, only the pre-tokens in its reverse index need to be processed.

This avoids scanning unrelated pre-tokens during every BPE iteration.

A set ensures that each distinct pre-token appears only once in the index, even when the same pair occurs multiple times in that pre-token.

### 3.2 Incremental pair-frequency updates

Instead of recalculating all pair frequencies after each merge, the algorithm updates the contributions of affected pre-tokens.

For each affected sequence:

1. Subtract the pair-frequency contributions of the original sequence.
2. Merge the selected pair.
3. Add the pair-frequency contributions of the updated sequence.
4. Record which pairs have changed.

The affected pairs are recorded in the set `changed_pairs`.

Only these pairs need to have their priorities updated in the heap.

This reduces redundant calculations, particularly when the selected pair appears in only a small fraction of all pre-tokens.

### 3.3 Priority queue: `heapq`

The implementation uses Python's built-in `heapq` module to efficiently select the most frequent adjacent pair.

Since `heapq` implements a min-heap, negative frequencies are stored to prioritise larger frequencies.

A heap entry is constructed using:

```python
def reverse_bytes(token):
    return tuple(-b for b in token) + (1,)

def heap_entry(pair, freq):
    return (
        -freq,
        reverse_bytes(pair[0]),
        reverse_bytes(pair[1]),
        pair
    )
```

The transformed byte sequences enforce the required lexicographic tie-breaking rule.

#### Lazy deletion

A pair's frequency may change after a merge.

Rather than searching the heap to modify an existing entry, the algorithm inserts a new entry containing the updated frequency.

When retrieving the next candidate, its stored frequency is compared with the current value in `pairs_freq`.

Outdated heap entries are discarded until a valid entry is found.

This technique is called **lazy deletion**.

It avoids rebuilding the entire heap after each merge, although outdated entries may temporarily increase memory consumption.

## 4. Project Structure

The main files are:

```text
cs336_basics/
├── tokenizer.ipynb
├── tokenizer_functions.py
└── README.md
```

### `tokenizer.ipynb`

The Jupyter notebook provides the main workflow.

It defines the training parameters and calls the four main functions needed for vocabulary training.

### `tokenizer_functions.py`

This file contains the implementation of the main training functions and supporting helper functions.

The helper functions handle:

- Pair-frequency calculation
- Reverse-index construction and maintenance
- Token merging
- Incremental frequency updates
- Priority-queue operations

### `README.md`

This file documents the implementation, algorithm, optimisations, and usage.

## 5. Requirements

The implementation uses Python and the following modules:

| Module | Purpose |
|---|---|
| `pathlib` | File and directory paths |
| `urllib.request` | Downloading the training corpus |
| `regex` | Regular-expression-based pre-tokenisation |
| `heapq` | Priority-queue operations |

All except `regex` are included in the Python standard library.

Install the external dependency using:

```bash
pip install regex
```

The main workflow can be executed in a Jupyter notebook using VS Code or another Jupyter-compatible environment.

## 6. Quick Start

Open `tokenizer.ipynb` and import the four main functions:

```python
from pathlib import Path

from tokenizer_functions import (
    download_token_data,
    count_tokens_in_file,
    initialize_vocab,
    enlarging_vocab
)
```

### Configure the training parameters

```python
intended_vocab_size = 10000

token_data_path = Path("data")
token_data_file_name = "TinyStoriesV2-GPT4-train.txt"

token_data_url = (
    "https://huggingface.co/datasets/roneneldan/"
    "TinyStories/resolve/main/"
    "TinyStoriesV2-GPT4-train.txt"
)

file_path = token_data_path / token_data_file_name

PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

dividing_str = "<|endoftext|>"
special_tokens = ["<|endoftext|>"]
```

### Train the vocabulary

The workflow requires four function calls:

```python
# 1. Download the training data
download_token_data(
    token_data_path,
    token_data_file_name,
    token_data_url
)

# 2. Pre-tokenise and count occurrences
byte_counts = count_tokens_in_file(
    file_path,
    PAT,
    dividing_str
)

# 3. Initialise the vocabulary
vocab = initialize_vocab(special_tokens)

# 4. Train the BPE vocabulary
(
    vocab,
    byte_counts,
    pairs_freq,
    pairs_freq_heap,
    pair_to_combs,
    merges
) = enlarging_vocab(
    vocab=vocab,
    intended_vocab_size=intended_vocab_size,
    byte_counts=byte_counts
)
```

The resulting `vocab` dictionary maps token IDs to byte sequences.

The `merges` list records the order in which token pairs were merged during training.

## 7. Resuming BPE Training

An important feature of this implementation is the ability to extend an existing vocabulary without repeating pre-tokenisation or reconstructing the initial training data structures.

The `enlarging_vocab()` function returns six objects representing the current training state.

| Object | Description |
|---|---|
| `vocab` | Mapping from token IDs to byte sequences |
| `byte_counts` | Current pre-token sequences and their frequencies |
| `pairs_freq` | Frequencies of adjacent token pairs |
| `pairs_freq_heap` | Priority queue for selecting the most frequent pair |
| `pair_to_combs` | Reverse index from pairs to pre-token sequences |
| `merges` | Ordered history of BPE merge operations |

Suppose a vocabulary has already been trained to 2,000 tokens.

It can be extended to 10,000 tokens by passing the existing state:

```python
(
    vocab,
    byte_counts,
    pairs_freq,
    pairs_freq_heap,
    pair_to_combs,
    merges
) = enlarging_vocab(
    vocab=vocab,
    intended_vocab_size=10000,
    byte_counts=byte_counts,
    pairs_freq=pairs_freq,
    pairs_freq_heap=pairs_freq_heap,
    pair_to_combs=pair_to_combs,
    merges=merges
)
```

Training continues using the existing vocabulary and intermediate data structures.

Currently, this continuation mechanism relies on objects retained in memory. Saving and restoring the complete state from disk is a possible future extension.

## 8. Function Reference

The implementation provides four main functions.

| Function | Description | Returns |
|---|---|---|
| `download_token_data()` | Downloads the training corpus | `None` |
| `count_tokens_in_file()` | Performs pre-tokenisation and counts frequencies | `byte_counts` |
| `initialize_vocab()` | Constructs the initial byte vocabulary and adds special tokens | `vocab` |
| `enlarging_vocab()` | Trains or extends the BPE vocabulary | Six training-state objects |

Additional helper functions are defined in `tokenizer_functions.py`.

## 9. Testing and Future Improvements

The current implementation focuses on BPE vocabulary training and algorithmic efficiency.

Planned improvements include:

- Validating the training algorithm against Stanford CS336's provided tests
- Implementing a complete tokenizer interface with encoding and decoding
- Measuring training time and peak memory consumption
- Comparing the optimised algorithm with a straightforward BPE implementation
- Adding disk-based checkpointing to resume training in a new Python session
- Investigating strategies for reducing heap memory consumption

Benchmark results and test outcomes will be added after validation.

## 10. References and Acknowledgements

- [Stanford CS336: Language Modeling from Scratch](https://github.com/stanford-cs336)
- [Stanford CS336 Assignment 1: Basics](https://github.com/stanford-cs336/assignment1-basics)
- [TinyStories Dataset](https://huggingface.co/datasets/roneneldan/TinyStories)
- [Python heapq Documentation](https://docs.python.org/3/library/heapq.html)

This project is an independent implementation developed while studying Stanford CS336, with an emphasis on understanding the BPE algorithm and investigating efficient training strategies.
