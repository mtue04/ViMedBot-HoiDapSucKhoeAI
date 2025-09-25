# ViMedBot 🩺

## Description
**ViMedBot** is an intelligent Retrieval-Augmented Generation (RAG) system designed to **provide healthcare consultation for Vietnamese users**. The system leverages cutting-edge natural language processing (NLP) and vector search technologies to deliver accurate, context-aware, and user-friendly answers to medical and health-related queries.

![ViMedBot Pipeline](assets/ViMedBot_pipeline.png)

## Demo

## Methodology
### Data Collection & Processing
Dataset [vietnamese-medical-dataset](https://huggingface.co/datasets/mtue29/vietnamese-medical-dataset) is available now. 

At the foundation of the RAG system is a carefully curated knowledge source derived from reliable Vietnamese material(s). The workflow for preparing this data consists of several stages:
- **Data Collection:** Content such as articles, reports, domain-specific knowledge, and other reference texts is automatically collected through web crawlers and API connections to trusted source(s).
- **Data Preprocessing:** The raw text is standardized by removing unnecessary elements (ads, navigation menus, formatting noise) and resolving issues like duplicates or inconsistent characters.
- **Data Organization:** After cleaning, the corpus is segmented into meaningful chunks (sections, paragraphs, or semantic units) with metadata (source, title, publication date) attached, enabling more precise retrieval.
- **Data Storage:** The structured data is embedded into dense vector representations and stored in a vector database (`Qdrant`). This allows semantic search to match user queries against the most relevant passages, ensuring accurate and efficient retrieval for the RAG pipeline.

### Model


### Deployment


## Installation


## Limitation & Future Works


## Disclaimer ⚠️
ViMedBot is **not a replacement for professional medical advice**. Always consult a qualified doctor or healthcare provider for medical concerns.