# Cache Engineering for AI Agent Harnesses

## Companion exercises, Python laboratories and checked solutions

This public repository contains the companion material for all 12 chapters of *Cache Engineering for AI Agent Harnesses*. The source code and fixtures are original, synthetic teaching examples. They are **not** production security controls or empirical performance benchmarks.

Each chapter folder contains a self-contained laboratory guide, exercise questions, checked solutions and its runnable Python script. Read the chapter, attempt the questions, then use the checked solutions to review your reasoning.

| Chapter | Topic | Companion material | Python lab |
|:--:|---|---|---|
| 1 | The Cache Problem in Agent Harness Engineering | [Laboratory, questions and answers](chapters/01/README.md) | [Source code](chapters/01/) |
| 2 | Caching Taxonomy and Memory Hierarchy | [Laboratory, questions and answers](chapters/02/README.md) | [Source code](chapters/02/) |
| 3 | Prompt Prefix Caching and Stable Context Design | [Laboratory, questions and answers](chapters/03/README.md) | [Source code](chapters/03/) |
| 4 | Transformer KV-Cache and Attention Serving | [Laboratory, questions and answers](chapters/04/README.md) | [Source code](chapters/04/) |
| 5 | Paged Attention, Quantisation and KV Eviction | [Laboratory, questions and answers](chapters/05/README.md) | [Source code](chapters/05/) |
| 6 | Semantic Caching and Similarity Thresholds | [Laboratory, questions and answers](chapters/06/README.md) | [Source code](chapters/06/) |
| 7 | Retrieval, RAG and Vector-Store Cache Strategies | [Laboratory, questions and answers](chapters/07/README.md) | [Source code](chapters/07/) |
| 8 | Tool, API and Multi-Agent Result Caching | [Laboratory, questions and answers](chapters/08/README.md) | [Source code](chapters/08/) |
| 9 | Invalidation, Consistency, Freshness and Provenance | [Laboratory, questions and answers](chapters/09/README.md) | [Source code](chapters/09/) |
| 10 | Security, Tenant Isolation and Cache Poisoning | [Laboratory, questions and answers](chapters/10/README.md) | [Source code](chapters/10/) |
| 11 | Cost, Latency, Energy and Adaptive Cache Policies | [Laboratory, questions and answers](chapters/11/README.md) | [Source code](chapters/11/) |
| 12 | Benchmarking, Replay, Observability and Production Architecture | [Laboratory, questions and answers](chapters/12/README.md) | [Source code](chapters/12/) |

## Running the laboratories

Requirements: **Python 3.10 or later**, with the standard library. No API keys, external services, network access or third-party packages are required by the supplied synthetic labs.

From the repository root, run a chapter's script, for example:

```bash
python3 chapters/01/helix_ch01.py
```

Run all scripts from the repository root with:

```bash
python3 scripts/run_all_labs.py
```

The verification workflow compiles and runs every exercise script in isolation. These checks confirm program behaviour only within its stated synthetic assumptions.

## Scope and source attribution

- The **book manuscript** remains in the [cache repository](https://github.com/danraid/cache/tree/main/manuscript); its repository may require author access.
- This repository is the canonical home for hands-on laboratories, runnable code, exercise questions and checked solutions.
- Architecture diagrams and in-text conceptual notation remain in the book because they are explanatory content rather than standalone exercise code.
- The original chapter's limitations, assumptions and examples are preserved in each companion guide; readers should not extrapolate synthetic outputs to real deployments.

## Chapters

Open a chapter from the table above. Changes to the manuscript's learning objectives should be reflected in the corresponding chapter guide and Python lab.
