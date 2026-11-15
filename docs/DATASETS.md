# Datasets

The datasets we have looked at for Leviathan's training runs, with links. Only
the rehearsal shard is in a run config today. The data mix for the first public
run is decided together with the model ([ROADMAP](ROADMAP.md), "Pick the model
and lock the data mix"), and English with Turkish needs a multilingual
tokenizer, so every source below is re-tokenized before a run uses it.

## Rehearsal, in a config today

| Dataset | What it is | License |
|---|---|---|
| [emozilla/fineweb-10bt-tokenized-datatrove-llama2](https://huggingface.co/datasets/emozilla/fineweb-10bt-tokenized-datatrove-llama2/tree/cd477aed05fd5c2efd4b0c6c2459f1537fbd1a30) | FineWeb's 10B-token sample, tokenized for Llama 2 in the datatrove format. The FineWeb rehearsal reads its first shard, `00000_00000_shuffled.ds`, at revision `cd477ae`, with the model [emozilla/llama2-20m-init](https://huggingface.co/emozilla/llama2-20m-init) ([fineweb-rehearsal.toml](https://github.com/wienerlabs/leviathan-net/blob/main/config/leviathan/fineweb-rehearsal.toml)). | The repo lists none. The source, [FineWeb](https://huggingface.co/datasets/HuggingFaceFW/fineweb), is ODC-By. |

## English web base, one of the two

| Dataset | What it is | License |
|---|---|---|
| [HuggingFaceFW/fineweb-edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu) | 1.3T tokens of educational web pages filtered from FineWeb. | ODC-By |
| [mlfoundations/dclm-baseline-1.0](https://huggingface.co/datasets/mlfoundations/dclm-baseline-1.0) | DCLM-Baseline: 4T tokens and 3B documents, a subset of DCLM-Pool, which is derived from Common Crawl. | CC BY 4.0 |

## Turkish

| Dataset | What it is | License |
|---|---|---|
| [HuggingFaceFW/fineweb-2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2), subset [`tur_Latn`](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2/tree/main/data/tur_Latn) | 95,129,129 documents and about 41.9B words, 125.53 GB on disk. | ODC-By |

## Looked at, not chosen

Corpora built only from openly licensed or public domain text. Suggested on 16
October 2026 and not chosen: the first runs use web text for quality.

| Dataset | What it is | License |
|---|---|---|
| [Common Pile v0.1, filtered](https://huggingface.co/collections/common-pile/common-pile-v01-filtered-data-68300bb0a946d10dda697663) | Openly licensed and public domain text. [comma_v0.1_training_dataset](https://huggingface.co/datasets/common-pile/comma_v0.1_training_dataset) is the consolidated set behind the Comma v0.1 models, and the [raw data](https://huggingface.co/collections/common-pile/common-pile-v01-raw-data-6826b454a5a6a445d0b51b37) is a separate collection. | Per source |
| [PleIAs/common_corpus](https://huggingface.co/datasets/PleIAs/common_corpus) | 2.27T tokens from books, newspapers, scientific articles and other sources, only uncopyrighted or freely licensed. | Per document |

## Before a run uses one

- Pull the repo at a pinned revision and check that its tokenizer matches the
  model. A corpus tokenized for a larger vocabulary indexes past the model's
  embedding table, and then the replay verifier cannot recompute anything
  ([FIRST_RUN, section 2](https://github.com/wienerlabs/leviathan-net/blob/main/docs/FIRST_RUN.md)).
- Serve the shards over HTTP from a short mirror domain. The verifier replays
  only an `Http` data location, and the on-chain URL fields are too short for a
  Hugging Face URL template.

Sizes and licenses were read from each dataset card on Hugging Face on 15
November 2026.
