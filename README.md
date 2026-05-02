# Multi-Domain Support Triage Agent

A terminal-based AI system that processes support tickets across multiple domains and intelligently decides whether to respond or escalate based on risk and confidence.

---

## 🚀 Overview

This project simulates a real-world support triage system. It classifies user issues, retrieves relevant documentation, and ensures safe handling by prioritizing escalation for sensitive or low-confidence cases.

---

## ⚙️ Features

* 🔍 Rule-based issue classification
* 🧠 Product detection (HackerRank, Claude, Visa)
* 📄 TF-IDF based document retrieval
* ⚠️ Safety-first decision engine
* ❌ No hallucination (uses only provided data)
* 📝 Detailed logging (log.txt)
* 📊 Structured output (output.csv)

---

## 🧩 System Pipeline

Read → Classify → Retrieve → Decide → Respond → Log

---

## 🛠️ Tech Stack

* Python
* scikit-learn (TF-IDF, cosine similarity)

---

## 📁 Project Structure

```
main.py
classifier.py
retriever.py
decision.py
responder.py
logger.py
```

---

## ▶️ How to Run

```bash
python main.py
```

---

## 🧠 Design Decisions

* Used TF-IDF for lightweight offline retrieval
* Implemented rule-based classification for simplicity
* Designed safety-first logic to avoid incorrect responses
* Escalates high-risk or low-confidence cases

---

## ⚠️ Limitations

* Limited semantic understanding (keyword-based)
* May escalate more queries due to strict safety rules

---

## 🚀 Future Improvements

* Use semantic embeddings for better matching
* Improve classification with NLP models
* Add tiered confidence handling

---

## 💡 Key Insight

This system is designed to **prioritize safety over incorrect answers**, which is critical in real-world support systems.

---

## 📌 Author

Developed as part of a support triage challenge.
