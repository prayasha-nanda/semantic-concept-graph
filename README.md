# Semantic Concept Graph Generator

Transform unstructured text into an interactive semantic knowledge graph powered by Gemini, NetworkX, and PyVis.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Gemini%20AI-2.5%20Flash-orange?style=flat&logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/NetworkX-Graph%20Engine-green?style=flat" alt="NetworkX">
  <img src="https://img.shields.io/badge/PyVis-Interactive%20Visualization-teal?style=flat" alt="PyVis">
  <img src="https://img.shields.io/badge/Pydantic-Validation-red?style=flat" alt="Pydantic">
  <img src="https://img.shields.io/badge/license-MIT-purple?style=flat" alt="License">
</p>


Ever tried reading a massive block of text and wished you could just *see* how all the ideas, themes, and characters smash into each other?

This tool takes raw, unstructured text and uses **Gemini 2.5 Flash** to extract semantic concepts (meaningful entities, themes, emotions, concepts, and relationships from natural language text), validates them with **Pydantic**, crunches the mathematical clusters using **NetworkX**, and spins up an interactive network graph courtesy of **PyVis** (that you can play with thanks to the physics setting!).

---
## Quick TL;DR - What It Does

1. Reads raw text
2. Extracts semantic concepts using Gemini
3. Builds a knowledge graph
4. Detects communities and central concepts
5. Generates an interactive visualization

Input:
Article, novel chapter, research paper, design document, etc. (Save as sample.txt)

Output:
Interactive semantic concept graph + static Matplotlib rendering of the same graph

---

## Features

### Semantic Extraction

Uses Gemini 2.5 Flash to identify nodes like:

* Characters
* Themes
* Events
* Technologies
* Emotions
* Settings
* and so on...

Each extracted node includes:

* Label
* Category
* Description
* Importance score
* Source reference

Then the system identifies semantic relationships between concepts and assigns:

* Relationship type
* Confidence score

Low-confidence edges are automatically filtered to improve graph quality (minimum confidence of `0.55` required!).

### Community Detection

NetworkX's modularity-based clustering algorithm groups related concepts into semantic communities (clusters).

Community membership is visualized through node border colors.

---

### Interactive Visualization

Built using PyVis.

Features include zooming, panning, node dragging, and hover tooltips with all the relevant relationship labels.

A static preview image is also generated using Matplotlib for documentation and sharing.

You can look at my sample outputs for this [article](https://medium.com/@prayasha/i-wrote-a-novel-without-learning-how-to-love-deadlines-11dfa5656c7f) I've written:

* `sample_graph.html`
* `sample_static_blueprint.png`

### Small Preview
![Sample Graph Screenshot](samples/sample_graph_screenshot.png)
You can zoom, drag nodes around, and explore the graph!

The static graph struggles with many relationships and connections, which you can see here, but it is still very helpful if you just want to get to the point! Sometimes the interactive graph may feel like it gives too much information.

![Sample Static Graph](samples/sample_static_blueprint.png)

---

## Architecture

```text
Input Text
    │
    ▼
Gemini 2.5 Flash
    │
    ▼
Structured JSON Graph
    │
    ▼
Validation Layer
(Pydantic)
    │
    ▼
NetworkX Graph
    │
    ├── Centrality Analysis
    ├── Community Detection
    └── Graph Metrics
    │
    ▼
PyVis Visualization
    │
    ▼
Interactive HTML Graph
```

---

## Project Structure

```text
semantic-concept-graph/
│
├── cache/                  # Local JSON cache
│   └── *.json
│
├── samples/                # Repository documentation assets
│   ├── sample_graph_screenshot.png
│   ├── sample_graph.html
│   └── sample_static_blueprint.png
│
├── sample.txt              # Feed your raw text data here!
├── main.py                 # The system core execution loop
├── graph.html              # Interactive DOM masterpiece
├── static_blueprint.png    # Matplotlib image asset
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/prayasha-nanda/semantic-concept-graph.git
cd semantic-concept-graph
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy:

```bash
cp .env.example .env
```

Add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## Usage

Place the text you want to analyze inside sample.txt.

Then run:

```bash
py main.py
```

Generated outputs:

```text
graph.html
static_blueprint.png
```

Open graph.html in your browser to explore the interactive graph!

---

## Caching

To reduce API usage and speed up experimentation, extraction results are cached locally.

Cache files are stored in cache/

The cache key is generated using the MD5 hash of:

* Input text
* Prompt configuration

This ensures that changing extraction instructions automatically invalidates old cache results.

---

## Node Visualization

### Fill Color

Represents semantic category.

### Border Color

Represents detected community cluster.

Community clusters are generated using modularity-based graph analysis and indicate groups of closely related concepts.

### Node Size

Determined by:

* Importance score
* Graph centrality

Larger nodes generally represent more influential concepts.

---

## Tech Stack

- AI: Gemini 2.5 Flash
- Validation: Pydantic
- Graph Analysis: NetworkX
- Visualization: PyVis & Matplotlib
- Utilities: python-dotenv

---

## Example Use Cases
- Literature Analysis
- Research Papers
- Software Documentation
- Knowledge Mapping

---

## Future Improvements

* Multi-document graph merging (mainly!)
* Export to GraphML
* Graph search and filtering
* Custom clustering strategies
* Perhaps a "talk to your graph" type bot?

---

## Built by yours truly

Prayasha Nanda.
Initially started out as a fun experiment to see how structured (or unstructured!) my writing was, and then I built this fun way to summarize the content to make even 3,000 word articles interesting to explore!

## License
MIT License.

Copyright (c) 2026 Prayasha Nanda
