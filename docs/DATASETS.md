# Datasets

The datasets we have looked at for Leviathan's training runs, with links. Only
the rehearsal shard is in a run config today. The data mix for the first public
run is decided together with the model ([ROADMAP](ROADMAP.md), "Pick the model
and lock the data mix"), and English with Turkish needs a multilingual
tokenizer, so every source below is re-tokenized before a run uses it.

Nodes stream shards from our mirror, so a source has to allow redistribution:
non-commercial licenses are out, share-alike licenses carry over to the mirror,
and a gated set's terms have to be read before it is mirrored.

## Rehearsal, in a config today

| Dataset | What it is | License |
|---|---|---|
| [emozilla/fineweb-10bt-tokenized-datatrove-llama2](https://huggingface.co/datasets/emozilla/fineweb-10bt-tokenized-datatrove-llama2/tree/cd477aed05fd5c2efd4b0c6c2459f1537fbd1a30) | FineWeb's 10B-token sample, tokenized for Llama 2 in the datatrove format. The FineWeb rehearsal reads its first shard, `00000_00000_shuffled.ds`, at revision `cd477ae`, with the model [emozilla/llama2-20m-init](https://huggingface.co/emozilla/llama2-20m-init) ([fineweb-rehearsal.toml](https://github.com/wienerlabs/leviathan-net/blob/main/config/leviathan/fineweb-rehearsal.toml)). | The repo lists none. The source, [FineWeb](https://huggingface.co/datasets/HuggingFaceFW/fineweb), is ODC-By. |

## English web base, one of the two

| Dataset | What it is | License |
|---|---|---|
| [HuggingFaceFW/fineweb-edu](https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu) | 1.3T tokens of educational web pages filtered from FineWeb. | ODC-By |
| [mlfoundations/dclm-baseline-1.0](https://huggingface.co/datasets/mlfoundations/dclm-baseline-1.0) | DCLM-Baseline: 4T tokens and 3B documents, a subset of DCLM-Pool, which is derived from Common Crawl. | CC BY 4.0 |

## Turkish web

FineWeb-2 is the plan. The others were found on 15 November 2026 and are
candidates only.

| Dataset | What it is | License |
|---|---|---|
| [HuggingFaceFW/fineweb-2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2), subset [`tur_Latn`](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2/tree/main/data/tur_Latn) | 95,129,129 documents and about 41.9B words, 125.53 GB on disk. | ODC-By |
| [epfml/FineWeb2-HQ](https://huggingface.co/datasets/epfml/FineWeb2-HQ), subset `tur_Latn` | The top 10% of FineWeb-2 by a quality classifier: 8,578,808 Turkish documents, 100 GB on disk. | ODC-By |
| [HPLT/HPLT2.0_cleaned](https://huggingface.co/datasets/HPLT/HPLT2.0_cleaned), subset `tur_Latn` | 117M documents and 51.7B words. The card reports HPLT v2 on par with or better than FineWeb-2 for Turkish. | CC0 1.0 |
| [allenai/MADLAD-400](https://huggingface.co/datasets/allenai/MADLAD-400), subset `tr` | Multilingual web text audited language by language; the Turkish subset was kept after the authors' audit. | ODC-By |
| [allenai/c4](https://huggingface.co/datasets/allenai/c4), mC4 `tr` | The Turkish part of multilingual C4, older than the sets above. | ODC-By |
| [uonlp/CulturaX](https://huggingface.co/datasets/uonlp/CulturaX), subset `tr` | Cleaned and deduplicated mC4 and OSCAR in 167 languages. Gated: the card and terms need a signed-in account. | Gated, read the terms first |

## Turkish curated and domain text

Found on 15 November 2026, candidates only.

| Dataset | What it is | License |
|---|---|---|
| [ytu-ce-cosmos/Cosmos-Turkish-Corpus-v1.0](https://huggingface.co/datasets/ytu-ce-cosmos/Cosmos-Turkish-Corpus-v1.0) | About 15B tokens from Turkish websites, including forums, news and Wikipedia. | CC BY 4.0 |
| [turkish-nlp-suite/BellaTurca](https://huggingface.co/datasets/turkish-nlp-suite/BellaTurca) | Academic texts, edited texts, forum threads and cleaned OSCAR and mC4, as separate subsets. The card gives 30.89B words and 246.5 GB in total. | CC BY-SA 4.0 |
| [HuggingFaceFW/finepdfs](https://huggingface.co/datasets/HuggingFaceFW/finepdfs), subset `tur_Latn` | Text extracted from PDFs: 1,699,676 Turkish documents, 15.34B tokens, 18.71 GB. The educational filter, [finepdfs-edu](https://huggingface.co/datasets/HuggingFaceFW/finepdfs-edu), has a `tur_Latn` subset too. | ODC-By |
| [wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia), subset `20231101.tr` | Turkish Wikipedia, 553 MB of parquet. | CC BY-SA 3.0 and GFDL |
| [mrfg/turkish-court-decisions](https://huggingface.co/datasets/mrfg/turkish-court-decisions) | 11,045,085 court decisions, 31.5B characters, 5.50 GB of parquet. | CC0 1.0, as the uploader states |

## English supplements

Found on 15 November 2026, candidates only: math, code and synthetic text that a
web base is thin on.

| Dataset | What it is | License |
|---|---|---|
| [HuggingFaceTB/finemath](https://huggingface.co/datasets/HuggingFaceTB/finemath) | Math pages from Common Crawl. FineMath-3+ is 34B tokens in 21.4M documents, and FineMath-4+ is 9.6B tokens. | ODC-By |
| [open-web-math/open-web-math](https://huggingface.co/datasets/open-web-math/open-web-math) | 6.3M math documents filtered from Common Crawl. | ODC-By 1.0, plus the Common Crawl terms |
| [HuggingFaceTB/smollm-corpus](https://huggingface.co/datasets/HuggingFaceTB/smollm-corpus) | FineWeb-Edu-Dedup (220B tokens), Cosmopedia v2 (over 39M synthetic textbooks, blog posts and stories) and Python-Edu. | ODC-By |
| [HuggingFaceTB/cosmopedia](https://huggingface.co/datasets/HuggingFaceTB/cosmopedia) | Synthetic textbooks, blog posts, stories and WikiHow articles from Mixtral-8x7B-Instruct: over 30M files and 25B tokens. | Apache 2.0 |
| [HuggingFaceTB/stack-edu](https://huggingface.co/datasets/HuggingFaceTB/stack-edu) | Code filtered for educational value. The repo holds Software Heritage IDs only, and the files come from Software Heritage's S3 bucket. | Per file |

## Large open mixes, for reference

| Dataset | What it is | License |
|---|---|---|
| [allenai/olmo-mix-1124](https://huggingface.co/datasets/allenai/olmo-mix-1124) | The OLMo 2 pretraining mix: 3.90T tokens in 3.08B documents. | ODC-By |
| [Zyphra/Zyda-2](https://huggingface.co/datasets/Zyphra/Zyda-2) | 5T tokens, cross-deduplicated and model-filtered from open datasets, with a `sample-100BT` subset. | ODC-By |
| [LLM360/TxT360](https://huggingface.co/datasets/LLM360/TxT360) | 99 Common Crawl snapshots and 14 non-web sources, deduplicated together. | ODC-By |

## English and Turkish parallel text

| Dataset | What it is | License |
|---|---|---|
| [allenai/nllb](https://huggingface.co/datasets/allenai/nllb), pair `eng_Latn-tur_Latn` | Mined sentence pairs. It is a loading-script dataset, so the files are fetched from outside the Hub. | ODC-By, plus each original source's terms |
| [Helsinki-NLP/opus-100](https://huggingface.co/datasets/Helsinki-NLP/opus-100), subset `en-tr` | English and Turkish sentence pairs from OPUS. | Not stated |

## Looked at, not chosen

Corpora built only from openly licensed or public domain text. Suggested on 16
October 2026 and not chosen: the first runs use web text for quality.

| Dataset | What it is | License |
|---|---|---|
| [Common Pile v0.1, filtered](https://huggingface.co/collections/common-pile/common-pile-v01-filtered-data-68300bb0a946d10dda697663) | Openly licensed and public domain text. [comma_v0.1_training_dataset](https://huggingface.co/datasets/common-pile/comma_v0.1_training_dataset) is the consolidated set behind the Comma v0.1 models, and the [raw data](https://huggingface.co/collections/common-pile/common-pile-v01-raw-data-6826b454a5a6a445d0b51b37) is a separate collection. | Per source |
| [PleIAs/common_corpus](https://huggingface.co/datasets/PleIAs/common_corpus) | 2.27T tokens from books, newspapers, scientific articles and other sources, only uncopyrighted or freely licensed. | Per document |

## Do not use as is

| Dataset | What it is | Why not |
|---|---|---|
| [vngrs-ai/vngrs-web-corpus](https://huggingface.co/datasets/vngrs-ai/vngrs-web-corpus) | Turkish web text, 50.3M pages and 25.33B tokens. | CC BY-NC-SA 4.0, non-commercial |
| [boun-tabilab/turkish_parliamentary_data](https://huggingface.co/datasets/boun-tabilab/turkish_parliamentary_data) | Turkish parliament sessions. | CC BY-NC-SA 4.0, non-commercial |
| [hasankursun/turkish-corpus-100b](https://huggingface.co/datasets/hasankursun/turkish-corpus-100b) | About 105B tokens that repackage FineWeb-2, Cosmos, synthetic and instruction data. | Relicensed as Apache 2.0 by the uploader. Use the sources under their own licenses. |
| [tascib/turkish-llm-dataset](https://huggingface.co/datasets/tascib/turkish-llm-dataset) | A merge of BellaTurca, Cosmos-Turkish-Corpus and a categorized FineWeb-2. | Use the sources directly. |

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
