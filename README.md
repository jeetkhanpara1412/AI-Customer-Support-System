# 🤖 AI Customer Support Ticket Classification System

An AI-powered customer support ticket classification system built using **Python**, **Scikit-learn**, **Natural Language Processing (NLP)**, **TF-IDF**, **Logistic Regression**, and **Cosine Similarity**.

The system automatically classifies customer support requests, retrieves the most similar historical ticket, and generates a professional support response.

---

## Features

- AI-powered support ticket classification
- Natural Language Processing (NLP)
- TF-IDF text vectorization
- Logistic Regression classifier
- Cosine Similarity-based ticket retrieval
- Automatic support response generation
- Intelligent fallback responses
- Modular Python architecture
- Command-line chatbot interface
- Conversation logging
- Unit testing

---

## Tech Stack

- Python
- Scikit-learn
- Natural Language Processing
- TF-IDF Vectorization
- Logistic Regression
- Cosine Similarity
- CSV Knowledge Base

---

## Project Structure

```text
AI-Customer-Support-System/
│
├── main.py
├── classifier.py
├── retriever.py
├── responder.py
├── decision.py
├── logger.py
├── knowledge_base.csv
├── requirements.txt
├── README.md
├── .gitignore
└── test_support_system.py
```

---

## Workflow

Customer Message

↓

Text Preprocessing

↓

TF-IDF Vectorization

↓

Logistic Regression Classification

↓

Predict Support Category

↓

Cosine Similarity Retrieval

↓

Generate Professional Company Response

↓

Display Final Response

---

## Supported Categories

- Account Access
- Billing
- Refund
- Technical Issue
- Payment Issue
- Order / Delivery
- Account Management
- Security / Fraud
- General Inquiry

---

## Example

Customer

```text
I forgot my password and cannot log in.
```

Support

```text
We're sorry you're having trouble signing in.
Please use the "Forgot Password" option to reset your password.
If the issue continues, please contact our support team.
```

---

## Installation

```bash
git clone https://github.com/yourusername/AI-Customer-Support-System.git

cd AI-Customer-Support-System

pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

or

```bash
python main.py "I forgot my password"
```

---

## Testing

```bash
python test_support_system.py
```

---

## Future Improvements

- Transformer models (BERT)
- Retrieval-Augmented Generation (RAG)
- FastAPI REST API
- Web-based chat interface
- Database integration
- Docker deployment
- Multi-language support
- Voice support
- Real-time analytics

---

## Author

Jeet Khanpara

MCA Student | Python Developer | Machine Learning Enthusiast
