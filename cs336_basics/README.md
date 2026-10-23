# Byte-Level BPE Tokenizer

A Python implementation of **byte-level Byte Pair Encoding (BPE)** developed while studying [Stanford CS336: Language Modeling from Scratch](https://github.com/stanford-cs336/assignment1-basics).

The project covers BPE vocabulary training, encoding, decoding, and iterable encoding. The training code uses an inverted pair-to-pre-token index, incremental frequency updates, and a priority queue; the encoder applies learned merge priorities to new input.

## 1. Overview

BPE begins with the 256 possible byte values and optionally adds special tokens such as `<|endoftext|>`. Ordinary text is pre-tokenised using a regular expression, and each pre-token is represented as UTF-8 bytes. Training repeatedly merges the most frequent adjacent pair **within** pre-tokens until the target vocabulary size is reached. The output consists of a vocabulary mapping integer IDs to byte sequences and an ordered list of learned merges.

The implementation uses the [TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories) corpus for the example training workflow. Its main code currently lives in `tokenizer_functions.py`; the training workflow is also demonstrated in `tokenizer.ipynb`.

## 2. Training Algorithm

1. **Initialise vocabulary:** create `vocab = {i: bytes([i]) for i in range(256)}` and append the supplied special tokens.
2. **Pre-tokenise:** split the training corpus at special-token boundaries, apply `PAT` to the ordinary text, and count each distinct regex match. Encode the matches as tuples of individual UTF-8 bytes; their frequencies are stored in `byte_counts`.
3. **Count adjacent pairs:** sum adjacent-pair frequencies across the pre-tokens, weighting by each pre-token's occurrence count (`pairs_freq`).
4. **Choose a pair:** select the most frequent pair, breaking ties by the lexicographically greatest byte pair.
5. **Merge:** concatenate the selected pair into a new vocabulary token and replace its non-overlapping occurrences left-to-right in affected pre-tokens. Record the chosen pair in `merges`.
6. **Update:** change the affected pre-tokens, pair frequencies, inverted index, and priority queue without rescanning the entire corpus.
7. **Repeat:** continue until the desired vocabulary size is reached or no mergeable pairs remain.

A vocabulary of 10,000 entries with one special token allows **9,743 learned merges** (10,000 − 256 − 1).

## 3. Training Optimisations

### Reverse index: `pair_to_combs`

`pair_to_combs` maps an adjacent token pair to the set of distinct pre-token sequences containing it. A merge therefore touches only the affected pre-tokens, rather than scanning all distinct pre-tokens.

### Incremental frequency updates

When a sequence changes, the algorithm subtracts its old adjacent-pair contributions and adds those of the new sequence. `changed_pairs` records which pair priorities need refreshing.

### Heap and lazy deletion

Python's `heapq` is a min-heap. The implementation stores negative pair frequencies so the highest frequency is selected first, with additional ordering fields for the required tie-break. Rather than searching the heap to update an old entry, it pushes a new entry for a changed pair. Obsolete entries are discarded when popped if their frequency no longer matches `pairs_freq`.

This avoids rebuilding the entire frequency dictionary and heap each iteration, at the cost of some additional heap memory.

## 4. Encoding

Training and encoding use the same pre-tokenisation pattern but have **different pair-selection rules**:

- **Training:** choose the pair with the greatest frequency across the training corpus.
- **Encoding:** among adjacent pairs currently present in a pre-token, choose the pair with the **earliest position in the learned `merges` list**.

The `Tokenizer` class accepts `vocab`, `merges`, and optional `special_tokens`. It constructs the inverse vocabulary (`bytes_to_id`) and merge-priority dictionary once:

```python
bytes_to_id = {token: token_id for token_id, token in vocab.items()}
merge_ranks = {pair: rank for rank, pair in enumerate(merges)}
```

### `encode(text)`

1. Separate ordinary text from special tokens, preserving their order. Special tokens are assigned their IDs directly.
2. Apply the same `PAT` regex used during training to each ordinary segment.
3. Convert each pre-token to a sequence of individual UTF-8 byte tokens.
4. Examine adjacent pairs, select the available pair with the lowest `merge_ranks` value, and merge its non-overlapping occurrences from left to right. Repeat until no learned pair is available.
5. Convert the resulting byte tokens to integer IDs through `bytes_to_id`.

The implementation caches results of repeated pre-tokens in `encoded_matches` within an encoding call. For each previously unseen pre-token, it builds a heap of currently available adjacent pairs ranked by merge priority.

### `decode(ids)`

Decoding looks up each ID in the vocabulary, concatenates the resulting **bytes**, and only then decodes the complete sequence as UTF-8:

```python
text = b"".join(vocab[token_id] for token_id in ids).decode("utf-8", errors="replace")
```

Decoding after concatenation is essential because an individual token can contain only part of a multibyte Unicode character.

## 5. Iterable Encoding

`Tokenizer.encode_iterable(iterable)` yields integer token IDs progressively rather than returning one large list:

```python
with open("example.txt", encoding="utf-8") as f:
    for token_id in tokenizer.encode_iterable(f):
        print(token_id)
```

The current implementation buffers text between input chunks. With configured special tokens, it uses their occurrences as boundaries; without special tokens, it attempts to use regex pre-token boundaries. It then delegates the completed text to `encode()` using `yield from`.

**Limitation:** passing the provided iterable tests is not proof of correctness for *arbitrary* chunk boundaries. Cases involving split pre-tokens, overlapping special tokens, and empty or unusual chunks require separate checks. Bounded memory usage is also not yet established for every input.

## 6. Project Structure

```text
assignment1-basics/
├── cs336_basics/
│   ├── tokenizer.ipynb
│   ├── tokenizer_functions.py
│   └── README.md
└── tests/
    ├── adapters.py
    ├── test_train_bpe.py
    └── test_tokenizer.py
```

- `tokenizer.ipynb`: interactive BPE-training workflow.
- `tokenizer_functions.py`: training helpers and the `Tokenizer` class (`encode`, `decode`, `encode_iterable`).
- `tests/adapters.py`: integrates the implementations with Stanford's test interfaces `run_train_bpe` and `get_tokenizer`.

The tokenizer class is currently implemented in `tokenizer_functions.py`, **not** a separate completed `tokenizer.py` module.

## 7. Requirements and Setup

The repository's `pyproject.toml` specifies Python 3.12–3.13 and manages dependencies with [`uv`](https://docs.astral.sh/uv/). The tokenizer itself relies on the third-party `regex` library; `heapq`, `pathlib`, and `urllib.request` are from the Python standard library.

From the repository root:

```bash
uv sync
```

## 8. Quick Start

From the `cs336_basics` notebook working directory:

```python
from pathlib import Path
from tokenizer_functions import (
    download_token_data,
    count_tokens_in_file,
    initialize_vocab,
    enlarging_vocab,
    Tokenizer,
)

intended_vocab_size = 10000
special_tokens = ["<|endoftext|>"]
PAT = Tokenizer.PAT

data_dir = Path("data")
filename = "TinyStoriesV2-GPT4-train.txt"
url = (
    "https://huggingface.co/datasets/roneneldan/TinyStories/"
    "resolve/main/TinyStoriesV2-GPT4-train.txt"
)

download_token_data(data_dir, filename, url)
byte_counts = count_tokens_in_file(data_dir / filename, PAT, special_tokens)
vocab = initialize_vocab(special_tokens)

vocab, byte_counts, pairs_freq, pairs_freq_heap, pair_to_combs, merges = enlarging_vocab(
    vocab=vocab,
    intended_vocab_size=intended_vocab_size,
    byte_counts=byte_counts,
)
```

Create a tokenizer from the trained vocabulary and ordered merges:

```python
tokenizer = Tokenizer(vocab, merges, special_tokens)
text = "Hello world! <|endoftext|>"
ids = tokenizer.encode(text)
print(ids)
print(tokenizer.decode(ids))
```

**Note:** Training 10,000 tokens on the full TinyStories training corpus is more demanding than the smaller Stanford test fixtures.

## 9. Training State and Vocabulary Extension

`enlarging_vocab()` returns six training-state objects:

| Object | Role |
|---|---|
| `vocab` | Integer token IDs mapped to byte sequences |
| `byte_counts` | Current pre-token sequences and their frequencies |
| `pairs_freq` | Frequencies of adjacent token pairs |
| `pairs_freq_heap` | Heap of candidate pairs |
| `pair_to_combs` | Reverse index from pairs to pre-token sequences |
| `merges` | Ordered learned-merge history |

These structures support further training without recounting the original corpus. When extending a vocabulary, pass the previous `merges` list together with the other training-state objects, so the learned merge history is preserved rather than reset. **This continuation behaviour still needs a dedicated test**, separate from the initial BPE-training tests. Disk-based persistence is not implemented.

## 10. Function Reference

| Function or method | Description |
|---|---|
| `download_token_data()` | Download a corpus if the file does not already exist |
| `count_tokens_in_file()` | Count pre-token frequencies after special-token splitting |
| `initialize_vocab()` | Initialise 256 byte tokens and any special tokens |
| `enlarging_vocab()` | Train BPE and return vocabulary plus intermediate state |
| `Tokenizer.encode(text)` | Convert a string to a list of integer token IDs |
| `Tokenizer.decode(ids)` | Convert token IDs to a decoded UTF-8 string |
| `Tokenizer.encode_iterable(iterable)` | Yield IDs from an iterable of text chunks |

## 11. Testing and Known Limitations

Run the training tests:

```bash
uv run pytest tests/test_train_bpe.py -v
```

Run the tokenizer tests:

```bash
uv run pytest tests/test_tokenizer.py -v
```

**Reported local results:** All three BPE-training tests passed, including the training-speed test. The standard encoding/decoding tests and the selected iterable-encoding correctness tests were also reported passing. No separate benchmark measurements are claimed here.

Further work:

- Validate or correct `encode_iterable` for arbitrary chunk boundaries, split special tokens, and inputs without separators.
- Verify memory use on Linux: Stanford's streaming memory test is skipped on macOS.
- Add a dedicated continuation test to verify that extending a trained vocabulary preserves the earlier merge history and produces the same output as uninterrupted training.
- Validate training pre-tokenisation when the special-token list is empty.
- Benchmark encoding speed and peak memory use against a simple reference implementation.

## 12. References

- [Stanford CS336 — Language Modeling from Scratch](https://github.com/stanford-cs336)
- [Stanford CS336 Assignment 1: Basics](https://github.com/stanford-cs336/assignment1-basics)
- [TinyStories Dataset](https://huggingface.co/datasets/roneneldan/TinyStories)
- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html)

This is an independent learning implementation focused on the algorithms and engineering decisions behind byte-level BPE tokenisation.
