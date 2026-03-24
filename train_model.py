import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# ==================================================
# 1. Load Datasets
# ==================================================

spam_train_path = "data/train.csv"
spam_test_path = "data/test.csv"
enron_path = "data/Enron legit.csv"
nazario_path = "data/Nazario Phishing.csv"
enron_large_path = "data/emails.csv"

spam_train = pd.read_csv(spam_train_path)
enron = pd.read_csv(enron_path)
nazario = pd.read_csv(nazario_path)
enron_large = pd.read_csv(enron_large_path)

print("Spam train columns:", spam_train.columns.tolist())
print("Enron columns:", enron.columns.tolist())
print("Nazario columns:", nazario.columns.tolist())
print("Large Enron columns:", enron_large.columns.tolist())
print()

# Raw label checks
if "label" in spam_train.columns:
    print("Spam train raw label counts:")
    print(spam_train["label"].value_counts(dropna=False))
    print()
else:
    print("Spam train has no 'label' column.")
    print()

if "label" in enron.columns:
    print("Enron raw label counts:")
    print(enron["label"].value_counts(dropna=False))
    print()
else:
    print("Enron has no 'label' column. It will be treated as legitimate.")
    print()

if "label" in nazario.columns:
    print("Nazario raw label counts:")
    print(nazario["label"].value_counts(dropna=False))
    print()
else:
    print("Nazario has no 'label' column. It will be treated as phishing.")
    print()

# ==================================================
# 2. Clean / Standardise Data
# ==================================================

# ---------- Spam/Ham dataset ----------
# Expected columns: text, label
spam_train = spam_train[["text", "label"]].copy()
spam_train["text"] = spam_train["text"].fillna("").astype(str).str.strip()
spam_train["label"] = spam_train["label"].fillna("").astype(str).str.strip().str.lower()

# Map known label variations to project labels
spam_train["label"] = spam_train["label"].replace({
    "spam": "phishing",
    "ham": "legitimate",
    "1": "phishing",
    "0": "legitimate",
    "phishing": "phishing",
    "legitimate": "legitimate",
    "safe": "legitimate",
    "benign": "legitimate"
})

print("Spam labels after mapping:")
print(spam_train["label"].value_counts(dropna=False))
print()

# ---------- Enron dataset ----------
# Expected columns: subject, body, maybe label
if "label" in enron.columns:
    enron = enron[["subject", "body", "label"]].copy()
    enron["label"] = enron["label"].fillna("legitimate").astype(str).str.strip().str.lower()
else:
    enron = enron[["subject", "body"]].copy()
    enron["label"] = "legitimate"

enron["subject"] = enron["subject"].fillna("").astype(str).str.strip()
enron["body"] = enron["body"].fillna("").astype(str).str.strip()
enron["text"] = (enron["subject"] + " " + enron["body"]).str.strip()

enron["label"] = enron["label"].replace({
    "ham": "legitimate",
    "spam": "phishing",
    "legit": "legitimate",
    "safe": "legitimate",
    "1": "phishing",
    "0": "legitimate",
    "legitimate": "legitimate",
    "phishing": "phishing"
})

enron = enron[["text", "label"]]

print("Enron labels after mapping:")
print(enron["label"].value_counts(dropna=False))
print()

# ---------- Nazario dataset ----------
# Treat as phishing-only unless you want to read labels from file
nazario = nazario[["subject", "body"]].copy()
nazario["subject"] = nazario["subject"].fillna("").astype(str).str.strip()
nazario["body"] = nazario["body"].fillna("").astype(str).str.strip()
nazario["text"] = (nazario["subject"] + " " + nazario["body"]).str.strip()
nazario["label"] = "phishing"
nazario = nazario[["text", "label"]]

print("Nazario labels after mapping:")
print(nazario["label"].value_counts(dropna=False))
print()

# ---------- Large Enron dataset (emails.csv) ----------
enron_large = enron_large[["message"]].copy()

enron_large = enron_large.sample(n=30000, random_state=42)

enron_large["text"] = enron_large["message"].fillna("").astype(str).str.strip()
enron_large["label"] = "legitimate"

enron_large = enron_large[["text", "label"]]

print("Large Enron labels:")
print(enron_large["label"].value_counts())
print()

# ==================================================
# 3. Combine Datasets
# ==================================================

data = pd.concat([spam_train, enron, nazario, enron_large], ignore_index=True)

print("Combined dataset size before cleaning:", len(data))
print()
print("Labels before cleaning/filtering:")
print(data["label"].value_counts(dropna=False))
print()

# Remove empty rows
data["text"] = data["text"].fillna("").astype(str).str.strip()
data["label"] = data["label"].fillna("").astype(str).str.strip().str.lower()
data = data[(data["text"] != "") & (data["label"] != "")]

print("Labels before final phishing/legitimate filter:")
print(data["label"].value_counts(dropna=False))
print()

# Keep only expected labels
data = data[data["label"].isin(["phishing", "legitimate"])]

print("Labels after final phishing/legitimate filter:")
print(data["label"].value_counts(dropna=False))
print()

# Remove duplicates
data = data.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)

print("Combined dataset size after cleaning:", len(data))
print()
print("Final label counts:")
print(data["label"].value_counts(dropna=False))
print()

# Safety check
if data["label"].nunique() < 2:
    raise ValueError(
        "Training data only contains one class after cleaning. "
        "You need both 'phishing' and 'legitimate' examples."
    )

# ==================================================
# 4. Train / Test Split
# ==================================================

X = data["text"]
y = data["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training set label counts:")
print(y_train.value_counts(dropna=False))
print()

print("Test set label counts:")
print(y_test.value_counts(dropna=False))
print()

# ==================================================
# 5. TF-IDF Vectorization
# ==================================================

vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=10000,
    ngram_range=(1, 2)
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# ==================================================
# 6. Train and Compare Models
# ==================================================

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Naive Bayes": MultinomialNB(),
    "SVM": LinearSVC()
}

results = []
best_model = None
best_model_name = None
best_f1 = 0.0

for name, model in models.items():
    print(f"\n{'=' * 50}")
    print(f"MODEL: {name}")
    print(f"{'=' * 50}")

    model.fit(X_train_vec, y_train)
    predictions = model.predict(X_test_vec)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, pos_label="phishing", zero_division=0)
    recall = recall_score(y_test, predictions, pos_label="phishing", zero_division=0)
    f1 = f1_score(y_test, predictions, pos_label="phishing", zero_division=0)

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-score : {f1:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions, labels=["legitimate", "phishing"]))

    print("\nClassification Report:")
    print(classification_report(y_test, predictions, zero_division=0))

    results.append({
        "model": name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    })

    if f1 > best_f1:
        best_f1 = f1
        best_model = model
        best_model_name = name

# ==================================================
# 7. Save Best Model + Results
# ==================================================

os.makedirs("models", exist_ok=True)

joblib.dump(best_model, "models/phishing_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

results_df = pd.DataFrame(results)
results_df.to_csv("models/model_results.csv", index=False)

print("\n" + "=" * 50)
print(f"Best model: {best_model_name}")
print(f"Best F1-score: {best_f1:.4f}")
print("Saved model to: models/phishing_model.pkl")
print("Saved vectorizer to: models/vectorizer.pkl")
print("Saved results to: models/model_results.csv")
print("=" * 50)

# ==================================================
# 8. Test on data/test.csv
# ==================================================

if os.path.exists(spam_test_path):
    spam_test = pd.read_csv(spam_test_path)
    print("\nFound data/test.csv")

    if "text" in spam_test.columns:
        spam_test["text"] = spam_test["text"].fillna("").astype(str).str.strip()
        spam_test = spam_test[spam_test["text"] != ""]

        spam_test_vec = vectorizer.transform(spam_test["text"])
        spam_test["predicted_label"] = best_model.predict(spam_test_vec)

        if hasattr(best_model, "predict_proba"):
            probs = best_model.predict_proba(spam_test_vec)
            class_index = list(best_model.classes_).index("phishing")
            spam_test["phishing_confidence"] = probs[:, class_index]
        else:
            spam_test["phishing_confidence"] = None

        spam_test.to_csv("models/test_predictions.csv", index=False)
        print("Saved test predictions to: models/test_predictions.csv")
    else:
        print("test.csv does not contain a 'text' column, so predictions were skipped.")
else:
    print("\ndata/test.csv not found, so external test predictions were skipped.")