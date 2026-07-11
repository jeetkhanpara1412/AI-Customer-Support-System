# AI Customer Support System

A simple, portfolio-ready customer support chatbot built with Python and scikit-learn.

## Features

- Classifies incoming customer messages into support categories
- Retrieves a relevant response from a knowledge base
- Produces a professional support reply for common support scenarios
- Includes a lightweight test suite for regression checks

## Project Structure

- `main.py` – runs the support workflow
- `classifier.py` – predicts the support category
- `retriever.py` – finds the closest matching support ticket
- `responder.py` – generates the final support reply
- `decision.py` – chooses matched/default/fallback response behavior
- `logger.py` – writes a simple conversation log
- `knowledge_base.csv` – support examples used for classification and retrieval
- `test_support_system.py` – regression tests for core behavior

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py "I forgot my password"
python main.py "Cancel my subscription"
python test_support_system.py
```
