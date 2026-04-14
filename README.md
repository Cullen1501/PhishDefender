# PhishDefender

PhishDefender is a machine learning-based web application that detects phishing emails within a user's inbox. It classifies emails as either phishing or legitimate using a trained model and displays the results in an easy-to-understand interface.

## Features

- Gmail inbox integration (IMAP)
- Automatic email classification
- Separate lists for:
- Possible phishing emails and Legitimate emails
- Email viewer panel
- Confidence scores for predictions
- Clean and interactive UI

## Tech Stack
- **Python**
- **Flask**
- **HTML, CSS, JavaScript**
- **Scikit-learn (Machine Learning)**
- **IMAP (Email retrieval)**

## Installation
### 1. Clone the repository:
```bash
git clone https://github.com/Cullen1501/PhishDefender.git
cd PhishDefender
```

### 2. Install dependencies:
``` bash
pip install -r requirements.txt
```

### 3. Run the backend:
``` bash
python Backend/app.py
```

### 4. Open the frontend:
Open index.html in your browser
OR
Use VS Code Live Server

## How to Use
- Enter your Gmail address
- Enter your Gmail App Password
- Click to load your inbox
- Emails will be classified automatically
#### View results in:
- Phishing emails list
- Legitimate emails list
- Click an email to view full details

## Model Overview
- TF-IDF feature extraction
- Logistic Regression classifier
- Trained on multiple phishing datasets
- Outputs classification + confidence score

## Project Structure
Backend/
    app.py
    email_service.py

Frontend/
    index.html
    about.html
    css/
    js/

models/
    phishing_model.pkl
    vectorizer.pkl

data/
    datasets

train_model.py
requirements.txt
README.md
Future Improvements
Explainable AI (LIME / SHAP)
Improved classification accuracy
Real-time email monitoring
UI enhancements

## Author
Cullen Ledraw-Carrick
BEng (Hons) Cybersecurity & Digital Forensics
Edinburgh Napier University
