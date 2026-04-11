"""
train_model.py

Purpose:
This script trains and evaluates a mcahine learning model for phishing email deteection

What this script does:
1. Loads multiple phishing and legitimate email datasets
2. Cleans and standardises all data into a common format
3. Combines datasets into one training dataset
4. Extracts features using:
    - TF-IDF 
    - Engineered features
5. Trains multiple models:
    - Logistic Regression
    - Naive Bayes
    - Support Vector Machine (SVM)
6. Compares models using accuracy, precision, recall, and F1-score
7. Selects and saves the best model
8. Generates evaluation outputs including:
    - Confusion matrix
    - Learning curve
    - Feature importance
    - Error analysis
    - Dataset contribution analysis

This script forms the core machine learning pipeline for the PhishDefender system
"""

# Imports

import os                           # Used for file and folder checks/creation
import joblib                       # Used to save and load trained model files
import pandas as pd                 # Used for reading, cleaning, and combining datasets 
import matplotlib.pyplot as plt     # Used to create graphs and evaluation plots
import numpy as np                  # Used for arrays, numeric operations, and plotting helpers
import re                           # Used for regex based text checks

from sklearn.model_selection import train_test_split, learning_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from scipy.sparse import issparse, hstack, csr_matrix
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay
)

# Helper Functions

"""
This section contains reusable helper functions used throughout the script 

These functions handle:
- text cleaning and preprocessing
- label standardisation
- feature engineering
- dataset transformation
- model evaluation and visualisation

Using helper function keeps the script easier to read and maintain
"""

# Section printing helper 
# Used to make terminal output easier to read
def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

# Label normalisation helper
# Converts different label styles into project labels

def normalise_labels(series):
    """
    Different datasets yuse differnt label formats 
    This function converts them into the two labels used in the project:
    - phishing
    - legitimate
    """
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({
            "spam": "phishing",
            "ham": "legitimate",
            "1": "phishing",
            "0": "legitimate",
            1: "phishing",
            0: "legitimate",
            "phishing email": "phishing",
            "safe email": "legitimate",
            "safe": "legitimate",
            "benign": "legitimate",
            "legitimate": "legitimate",
            "phishing": "phishing"
        })
    )


# Text cleaning helper
# Removes blanks and standardises text fields

def clean_text(series):
    """
    Cleans raw email text by:
    - replacing missing values
    - removing repeated spaces
    - removing structural labels such as Subject:, From:, Body:
    - converting to lowercase

    This helps make all datasets more consistent before training
    """
    return (
        series.fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"(?i)\bsubject:\b", " ", regex=True)
        .str.replace(r"(?i)\bfrom:\b", " ", regex=True)
        .str.replace(r"(?i)\bbody:\b", " ", regex=True)
        .str.strip()
        .str.lower()
    )

# Feature Engineering Helpers
"""
In addition to TF-IDF, the script builds several handcrafted features.

These are useful becuase phishing emails often include patters such as:
- links
- urgent wording
- account/security language
- payment/banking language
- excessive punctuation
- unusual use of capiutal letter
"""
def count_links(text):
    # Counts how many visible links appear in the text.
    text = str(text or "")
    return len(re.findall(r"http[s]?://|www\.", text, flags=re.IGNORECASE))

def contains_urgent_words(text):
    # Returns 1 if urgent or threatening languageappears, otherwise 0.
    text = str(text or "").lower()
    urgent_words = [
        "urgent", "immediately", "suspended", "verify now",
        "action required", "limited time", "warning", "alert"
    ]
    return int(any(word in text for word in urgent_words))

def contains_account_words(text):
    # Returns 1 if account or login related words appear, otherwise 0.
    text = str(text or "").lower()
    account_words = [
        "account", "login", "sign in", "password", "username",
        "verify", "authentication", "security"
    ]
    return int(any(word in text for word in account_words))

def contains_payment_words(text):
    # Retruns 1 if payment or banking related words appear, otherwise 0.
    text = str(text or "").lower()
    payment_words = [
        "payment", "invoice", "bank", "card", "refund",
        "billing", "transaction", "transfer"
    ]
    return int(any(word in text for word in payment_words))

def exclamation_count(text):
    # Counts exclamation marks, which can indicate aggressive or urgent tone.
    return str(text or "").count("!")

def uppercase_ratio(text):
    # Calcualtes the ratio of uppercase letters.
    # Very high uppercase usage can sometimes suggeset suspicious wording.
    text = str(text or "")
    letters = [c for c in text if c.isalpha()]
    if not letters: 
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters)

def build_engineered_features(text_series):
    """
    Builds all handcrafted features into a single DataFrame.

    This DataFrame is later converted into a sparse matrix and combined with the TF-IDF features.
    """
    features_df = pd.DataFrame({
        "link_count": text_series.apply(count_links),
        "has_urgent_words": text_series.apply(contains_urgent_words),
        "has_account_words": text_series.apply(contains_account_words),
        "has_payment_words": text_series.apply(contains_payment_words),
        "exclamation_count": text_series.apply(exclamation_count),
        "uppercase_ratio": text_series.apply(uppercase_ratio)
    })
    return features_df

# Final dataset cleaning helper
# Applies standard cleanup to any text/label dataset
def finalise_dataset(df, dataset_name):
    """
    Applies the final standard cleaning steps to a dataset.

    Required columns:
    - text
    - labek

    This ensures every dataset ends up in the same standard format. 
    """
    df = df.copy()

    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError(f"{dataset_name} must contain 'text' and 'label' columns.")

    # Keep only valid rows usable text and one of the two accepted labels
    df["text"] = clean_text(df["text"])
    df["label"] = normalise_labels(df["label"])

    df = df[(df["text"] != "") & (df["label"].isin(["phishing", "legitimate"]))]
    df = df.reset_index(drop=True)

    print(f"{dataset_name} labels after cleaning:")
    print(df["label"].value_counts(dropna=False))
    print()
    
    return df

# Dataset Builders
"""
Each dataset comes in a different structure.
These functions convery each one into the common project format:
- text
- label
""" 

# Spam Train dataset builder

def build_spam_train_dataset(df):
    # Converts Spam Train into standard text + label format.
    df = df[["text", "label"]].copy()
    return finalise_dataset(df, "Spam Train")

# Enron dataset builder

def build_enron_dataset(df):
    """
    Converts Enron into standard format.

    Even if Enron contains a label column, it is treated as legitimate here becyuase it is being used a a trusted/legitimate dataset.
    """
    if "label" in df.columns:
        df = df[["subject", "body", "label"]].copy()
    else:
        df = df[["subject", "body"]].copy()
        df["label"] = "legitimate"

    df["subject"] = clean_text(df["subject"])
    df["body"] = clean_text(df["body"])
    df["text"] = (df["subject"] + " " + df["body"]).str.strip()
    df["label"] = "legitimate"

    df = df[["text", "label"]]
    return finalise_dataset(df, "Enron")

# Nazario dataset builder

def build_nazario_dataset(df):
    # Converts Nazario dataset into standard format and marks all rows as phishing.
    df = df[["subject", "body"]].copy()
    df["subject"] = clean_text(df["subject"])
    df["body"] = clean_text(df["body"])
    df["text"] = (df["subject"] + " " + df["body"]).str.strip()
    df["label"] = "phishing"

    df = df[["text", "label"]]
    return finalise_dataset(df, "Nazario")

# Kaggle phishing dataset builder

def build_kaggle_dataset(df):
    """
    Converts Kaggle phishing dataset into project format.

    This dataset is filtered so only phishing examples are kept
    """
    df = df[["Email Text", "Email Type"]].copy()
    df = df.rename(columns={
        "Email Text": "text",
        "Email Type": "label"
    })

    df["text"] = clean_text(df["text"])
    df["label"] = normalise_labels(df["label"])

    print("Kaggle phishing labels before filtering:")
    print(df["label"].value_counts(dropna=False))
    print()

    df = df[df["label"] == "phishing"]
    df = df[["text", "label"]]

    return finalise_dataset(df, "Kaggle Phishing")

# CEAS dataset builder

def build_ceas_dataset(df):
    # Converts CEAS dataset into standard format by combining sender, subject, and body. 
    df = df[["sender", "subject", "body", "label"]].copy()

    df["sender"] = clean_text(df["sender"])
    df["subject"] = clean_text(df["subject"])
    df["body"] = clean_text(df["body"])
    df["label"] = normalise_labels(df["label"])

    df["text"] = (
        df["sender"] + " " + df["subject"] + " " + df["body"]
    ).str.strip()

    df = df[["text", "label"]]
    return finalise_dataset(df, "CEAS")

# Vectorizer helper
# Creates the TF-IDF feature extractor

def create_vectorizer():
    """
    Creates the TF-IDF vectorizer used to turn email text into numeric features.

    Settings used here:
    - English stop words removed
    - maximum of 15,000 features 
    - unigrams and bigrams
    - ignore very rare terms
    - use sublinear term frequency scaling
    """
    return TfidfVectorizer(
        stop_words="english",
        max_features=15000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True
    )

# Model helper
# Creates the ML models used for comparison

def create_models():
    # Returns the set of machine learning models used in teh comparison stage.
    return {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Naive Bayes": MultinomialNB(),
        "SVM": LinearSVC()
    }

# Contribution analysius helper
# Trains all models on one dataset combination 

def evaluate_models_on_dataset(dataset_name, df, results_list):
    """
    Trains all comparison models on a particular dataset combination and records the results
    
    This is used for dataset contribution analysis to show how each added dataset affects performance
    """
    df = finalise_dataset(df, dataset_name)

    if df["label"].nunique() < 2:
        print(f"Skipping {dataset_name} - only one class found after cleaning.")
        return

    X = df["text"]
    y = df["label"]

    # Split into training and test data
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    vectorizer = create_vectorizer()

    # Build text features 
    X_train_text_vec = vectorizer.fit_transform(X_train)
    X_test_text_vec = vectorizer.transform(X_test)

    # Build handcrafted features
    X_train_extra = csr_matrix(build_engineered_features(X_train).values)
    X_test_extra = csr_matrix(build_engineered_features(X_test).values)

    # Combine both feature sets 
    X_train_vec = hstack([X_train_text_vec, X_train_extra])
    X_test_vec = hstack([X_test_text_vec, X_test_extra])
    
    # Train and evaluate each model
    for model_name, model in create_models().items():
        model.fit(X_train_vec, y_train)
        predictions = model.predict(X_test_vec)

        results_list.append({
            "dataset": dataset_name,
            "model": model_name,
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, pos_label="phishing", zero_division=0),
            "recall": recall_score(y_test, predictions, pos_label="phishing", zero_division=0),
            "f1": f1_score(y_test, predictions, pos_label="phishing", zero_division=0)
        })

        print(f"{dataset_name} | {model_name} complete")

# Graph saving helper
# Saves dataset contribution analysis line graphs 

def save_dataset_contribution_graphs(contrib_df):
    """
    Saves two graphs showing how model performance changes as more datasets are added:
    - F1 score graph
    - Recall graph
    """
    if contrib_df.empty:
        print("No dataset contribution results were generated, so graphs were skipped.")
        return

    plt.figure(figsize=(11, 6))
    for model_name in contrib_df["model"].unique():
        subset = contrib_df[contrib_df["model"] == model_name]
        plt.plot(subset["dataset"], subset["f1"], marker="o", label=model_name)

    plt.title("Dataset Contribution Analysis - F1 Score")
    plt.xlabel("Dataset Combination")
    plt.ylabel("F1 Score")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig("models/dataset_contribution_f1.png")
    plt.close()

    plt.figure(figsize=(11, 6))
    for model_name in contrib_df["model"].unique():
        subset = contrib_df[contrib_df["model"] == model_name]
        plt.plot(subset["dataset"], subset["recall"], marker="o", label=model_name)

    plt.title("Dataset Contribution Analysis - Phishing Recall")
    plt.xlabel("Dataset Combination")
    plt.ylabel("Recall")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig("models/dataset_contribution_recall.png")
    plt.close()

    print("Saved dataset contribution graphs:")
    print("- models/dataset_contribution_f1.png")
    print("- models/dataset_contribution_recall.png")

# Learning curve helper
# Saves a learning curve for the best model

def save_learning_curve(estimator, X, y, model_name, save_path):
    """
    Generates and saves a learning curve for the best model.

    This helps show how performance changes as more training examples are used.
    """
    train_sizes, train_scores, test_scores = learning_curve(
        estimator,
        X,
        y,
        cv=5,
        scoring="f1_weighted",
        train_sizes=np.linspace(0.1, 1.0, 5),
        n_jobs=-1
    )

    train_mean = train_scores.mean(axis=1)
    test_mean = test_scores.mean(axis=1)

    plt.figure(figsize=(8, 5))
    plt.plot(train_sizes, train_mean, marker="o", label="Training score")
    plt.plot(train_sizes, test_mean, marker="o", label="Validation score")
    plt.title(f"Learning Curve - {model_name}")
    plt.xlabel("Training Examples")
    plt.ylabel("F1 Score")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

# Error analysis  helper
# Saves all misclassified emails and seperates false positives / false negatives 
def save_error_analysis(X_test, y_test, predictions, confidences=None, save_dir="models"):
    """
    Saves:
    - all misclassified emails
    - false positives
    - false negatives 

    Useful for analysing where the model made mistakes 
    """
    results_df = pd.DataFrame({
        "text": X_test.reset_index(drop=True),
        "actual": y_test.reset_index(drop=True),
        "predicted": pd.Series(predictions).reset_index(drop=True)
    })

    if confidences is not None:
        results_df["phishing_confidence"] = pd.Series(confidences).reset_index(drop=True)

    misclassified = results_df[results_df["actual"] != results_df["predicted"]].copy()

    false_positives = misclassified[
        (misclassified["actual"] == "legitimate") &
        (misclassified["predicted"] == "phishing")
    ].copy()

    false_negatives = misclassified[
        (misclassified["actual"] == "phishing") &
        (misclassified["predicted"] == "legitimate")
    ].copy()

    misclassified.to_csv(f"{save_dir}/misclassified_emails.csv", index=False)
    false_positives.to_csv(f"{save_dir}/false_positives.csv", index=False)
    false_negatives.to_csv(f"{save_dir}/false_negatives.csv", index=False)

    print("Saved error analysis files:")
    print("- models/misclassified_emails.csv")
    print("- models/false_positives.csv")
    print("- models/false_negatives.csv")

# Confidence helper
# Adds phishing confidence where supported

def get_phishing_confidence(model, X_vec):
    """
    Returns phishing confidence scores if the model supports predict_proba.

    If not supported, returns a list of None values
    """
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_vec)
        class_index = list(model.classes_).index("phishing")
        return probs[:, class_index]
    
    return [None] * X_vec.shape[0]

# Feature importance helper
# Saves top phishing and legitimate terms for linear models

def save_feature_importance(model, vectorizer, top_n=20, save_dir="models"):
    """
    Saves the most important features fro linear models such ash:
    - Logistic Regression
    - Linear SVM (if coefficient structure allows)

    Positive coefficients suggest phishing
    Negative coefficients suggest legitimate
    """
    if not hasattr(model, "coef_"):
        print("Feature importance skipped: this model does not expose coef_.")
        return

    # Get test feature names from TF-IDF
    feature_names = np.array(vectorizer.get_feature_names_out())

    # Flatten coefficients to 1D
    coefficients = np.asarray(model.coef_).ravel()

    # Safety check
    if len(feature_names) != len(coefficients):
        print("Feature importance skipped: feature and coefficient lengths do not match.")
        print(f"Feature count     : {len(feature_names)}")
        print(f"Coefficient count : {len(coefficients)}")
        return

    # Make sure top_n is not bigger than number of features
    top_n = min(top_n, len(feature_names))

    # Highest positive weights = phishing
    # Most negative weights = legitimate
    top_phishing_idx = np.argsort(coefficients)[-top_n:][::-1]
    top_legitimate_idx = np.argsort(coefficients)[:top_n]

    phishing_df = pd.DataFrame({
        "feature": feature_names[top_phishing_idx].tolist(),
        "coefficient": coefficients[top_phishing_idx].tolist()
    })

    legitimate_df = pd.DataFrame({
        "feature": feature_names[top_legitimate_idx].tolist(),
        "coefficient": coefficients[top_legitimate_idx].tolist()
    })

    phishing_df.to_csv(f"{save_dir}/top_phishing_features.csv", index=False)
    legitimate_df.to_csv(f"{save_dir}/top_legitimate_features.csv", index=False)

    # Plot both groups together
    combined_df = pd.concat([
        legitimate_df.assign(group="Legitimate"),
        phishing_df.assign(group="Phishing")
    ], ignore_index=True)

    plt.figure(figsize=(12, 8))
    plt.barh(combined_df["feature"], combined_df["coefficient"])
    plt.title("Top Feature Importance - Legitimate vs Phishing")
    plt.xlabel("Coefficient Weight")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(f"{save_dir}/feature_importance.png")
    plt.close()

    print("Saved feature importance files:")
    print("- models/top_phishing_features.csv")
    print("- models/top_legitimate_features.csv")
    print("- models/feature_importance.png")

# Load Datasets 

print_section("1. LOAD DATASETS")

# Define file paths 
spam_train_path = "data/train.csv"
spam_test_path = "data/test.csv"
enron_path = "data/Enron legit.csv"
nazario_path = "data/Nazario Phishing.csv"
phish_kaggle_path = "data/Phishing_Email.csv"
ceas_path = "data/CEAS_08.csv"

# Read raw dataset files
spam_train_raw = pd.read_csv(spam_train_path)
enron_raw = pd.read_csv(enron_path)
nazario_raw = pd.read_csv(nazario_path)
phish_kaggle_raw = pd.read_csv(phish_kaggle_path)
ceas_raw = pd.read_csv(ceas_path)

# Show dataset columns 
print("Spam train columns:", spam_train_raw.columns.tolist())
print("Enron columns:", enron_raw.columns.tolist())
print("Nazario columns:", nazario_raw.columns.tolist())
print("Kaggle phishing columns:", phish_kaggle_raw.columns.tolist())
print("CEAS phishing columns:", ceas_raw.columns.tolist())
print()

# Show raw label counts
if "label" in spam_train_raw.columns:
    print("Spam train raw label counts:")
    print(spam_train_raw["label"].value_counts(dropna=False))
    print()

if "label" in enron_raw.columns:
    print("Enron raw label counts:")
    print(enron_raw["label"].value_counts(dropna=False))
    print()

if "label" in nazario_raw.columns:
    print("Nazario raw label counts:")
    print(nazario_raw["label"].value_counts(dropna=False))
    print()


# Clean and Standardise Datasets
print_section("2. CLEAN AND STANDARDISE DATASETS")

# Convert each raw dataset into the common project format
spam_train = build_spam_train_dataset(spam_train_raw)
enron = build_enron_dataset(enron_raw)
nazario = build_nazario_dataset(nazario_raw)
phish_kaggle = build_kaggle_dataset(phish_kaggle_raw)
ceas = build_ceas_dataset(ceas_raw)

# Combine Datasets

print_section("3. COMBINE DATASETS")

# Merge all cleaned datasets together into one combined dataset
data = pd.concat(
    [spam_train, enron, nazario, phish_kaggle, ceas],
    ignore_index=True
)

print("Combined dataset size before final cleaning:", len(data))
print()
print("Labels before final cleaning:")
print(data["label"].value_counts(dropna=False))
print()

# Apply final cleaning after merge and remove duplicate rows
data = finalise_dataset(data, "Combined Dataset")
data = data.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)

print("Combined dataset size after cleaning:", len(data))
print()
print("Final label counts:")
print(data["label"].value_counts(dropna=False))
print()

# Saftey check to make sure both classes still exist
if data["label"].nunique() < 2:
    raise ValueError(
        "Training data only contains one class after cleaning. "
        "You need both 'phishing' and 'legitimate' examples."
    )

# Dataset Contribution Analysis
print_section("4. DATASET CONTRIBUTION ANALYSIS")
"""
This section test how model performance changes as more datasets are added.

It provides evidence for which datasets improved the model
"""

# Create output folder if it does not already exist
os.makedirs("models", exist_ok=True)

dataset_results = []

evaluate_models_on_dataset(
    "Spam Only",
    spam_train,
    dataset_results
)

evaluate_models_on_dataset(
    "Spam + Enron",
    pd.concat([spam_train, enron], ignore_index=True),
    dataset_results
)

evaluate_models_on_dataset(
    "Spam + Enron + Nazario",
    pd.concat([spam_train, enron, nazario], ignore_index=True),
    dataset_results
)

evaluate_models_on_dataset(
    "Spam + Enron + Nazario + Kaggle",
    pd.concat([spam_train, enron, nazario, phish_kaggle], ignore_index=True),
    dataset_results
)

evaluate_models_on_dataset(
    "Spam + Enron + Nazario + Kaggle + CEAS",
    pd.concat([spam_train, enron, nazario, phish_kaggle, ceas], ignore_index=True),
    dataset_results
)

# Save the dataset contribution results as a CSV 
contrib_df = pd.DataFrame(dataset_results)
contrib_df.to_csv("models/dataset_contribution_results.csv", index=False)

print("Saved dataset contribution table to:")
print("- models/dataset_contribution_results.csv")

# Save graphs showing the contribution results
save_dataset_contribution_graphs(contrib_df)


# Train / Test Split
print_section("5. TRAIN / TEST SPLIT")

# Seperate features (X) and labels (y)
X = data["text"]
y = data["label"]

# Split into training and test sets using stratification so class balance is preserved
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

# TF-IDF Vectorization
print_section("6. TF-IDF VECTORIZATION")
# This section converts test into numerical features using TF-IDF and then combines those features with the hadncrafted phishing features

# Create TF-IDF vectorizer
vectorizer = create_vectorizer()

# Build TF-IDF text features 
X_train_text_vec = vectorizer.fit_transform(X_train)
X_test_text_vec = vectorizer.transform(X_test)

# Build handcrafted features 
X_train_extra = csr_matrix(build_engineered_features(X_train).values)
X_test_extra = csr_matrix(build_engineered_features(X_test).values)

# Combine TF-IDF and handcrafted features into one final feature set 
X_train_vec = hstack([X_train_text_vec, X_train_extra])
X_test_vec = hstack([X_test_text_vec, X_test_extra])

print("Vectorization complete.")
print("TF-IDF feature count:", X_train_text_vec.shape[1])
print("Engineered feature count:", X_train_extra.shape[1])
print("Total feature count:", X_train_vec.shape[1])
print()

# Train adn Compare Models
print_section("7. TRAIN AND COMPARE MODELS")
"""
This section trains multiple machine learning models and compares them.
The best model is chosen using F1-score, which is especially useful for imbalanced classification tasks like phishing detection.
"""

# Create model list 
models = create_models()

# Variables used to track the best performing model
results = []
best_model = None
best_model_name = None
best_f1 = 0.0
best_predictions = None

# Train and evaluate each model
for name, model in models.items():
    print("\n" + "-" * 50)
    print(f"MODEL: {name}")
    print("-" * 50)

    model.fit(X_train_vec, y_train)
    predictions = model.predict(X_test_vec)

    report = classification_report(y_test, predictions, zero_division=0)

    # Save individual classification report for this model
    with open(f"models/{name}_classification_report.txt", "w") as f:
        f.write(report)

    # Calculate evlauation metrics 
    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, pos_label="phishing", zero_division=0)
    recall = recall_score(y_test, predictions, pos_label="phishing", zero_division=0)
    f1 = f1_score(y_test, predictions, pos_label="phishing", zero_division=0)

    # print summary metrics 
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-score : {f1:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions, labels=["legitimate", "phishing"]))

    print("\nClassification Report:")
    print(classification_report(y_test, predictions, zero_division=0))

    # Store model reults in a list for later saving/plotting
    results.append({
        "model": name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    })

    # Update best model if this one has the highest F1 score so far 
    if f1 > best_f1:
        best_f1 = f1
        best_model = model
        best_model_name = name
        best_predictions = predictions

# Save Best Model and Reults
print_section("8. SAVE BEST MODEL AND RESULTS")
"""
This section saves the best trained model and the TF-IDF vectorizer.
These files are later used by the Flask backend for real time predictions.
"""

# Save best model and vectorizer 
joblib.dump(best_model, "models/phishing_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

# Save results table
results_df = pd.DataFrame(results)
results_df.to_csv("models/model_results.csv", index=False)

# Save model comparison chart 
plt.figure(figsize=(8, 5))
plt.bar(results_df["model"], results_df["f1_score"])
plt.title("Model Comparison by F1 Score")
plt.xlabel("Model")
plt.ylabel("F1 Score")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("models/model_comparison.png")
plt.close()

print("Saved model comparison graph to:")
print("- models/model_comparison.png")

print("\nBest model summary:")
print(f"Best model   : {best_model_name}")
print(f"Best F1-score: {best_f1:.4f}")
print("Saved files:")
print("- models/phishing_model.pkl")
print("- models/vectorizer.pkl")
print("- models/model_results.csv")

# Save Learning Curve, COnfusion Matrix, Error Analysis, and Feature Importance
print_section("9. SAVE LEARNING CURVE, CONFUSION MATRIX, ERROR ANALYSIS, AND FEATURE IMPORTANCE")
"""
This section generates extra outputs that help explain and justify model performance.
"""

# Save learning curve 
save_learning_curve(
    best_model,
    X_train_vec,
    y_train,
    best_model_name,
    "models/learning_curve.png"
)
print("Saved learning curve to:")
print("- models/learning_curve.png")

# Save beset model classification report
best_report = classification_report(y_test, best_predictions, zero_division=0)
with open("models/best_model_classification_report.txt", "w") as f:
    f.write(best_report)

print("Saved best model classification report to:")
print("- models/best_model_classification_report.txt")

# Save confusion matrix plot 
plt.figure(figsize=(6, 5))
ConfusionMatrixDisplay.from_predictions(
    y_test,
    best_predictions,
    labels=["legitimate", "phishing"],
    cmap="Blues"
)
plt.title(f"Confusion Matrix - {best_model_name}")
plt.tight_layout()
plt.savefig("models/confusion_matrix.png")
plt.close()

print("Saved confusion matrix to:")
print("- models/confusion_matrix.png")

# Save error analysis files 
best_confidences = get_phishing_confidence(best_model, X_test_vec)
save_error_analysis(
    X_test,
    y_test,
    best_predictions,
    confidences=best_confidences,
    save_dir="models"
)

# Save feature importance files and graph
save_feature_importance(best_model, vectorizer, top_n=20, save_dir="models")

# Test on External Test Data
print_section("10. TEST ON EXTERNAL TEST DATA")
"""
If external test files exsists, this section applies the trained model to it.
"""

# Check if external test file exsists  
if os.path.exists(spam_test_path):
    spam_test = pd.read_csv(spam_test_path)
    print("Found data/test.csv")

    # Only continue if the file has a text column 
    if "text" in spam_test.columns:
        spam_test["text"] = clean_text(spam_test["text"])
        spam_test = spam_test[spam_test["text"] != ""]

        # Build TF-IDF and handcrafted features for the external data
        spam_test_text_vec = vectorizer.transform(spam_test["text"])
        spam_test_extra = csr_matrix(build_engineered_features(spam_test["text"]).values)
        spam_test_vec = hstack([spam_test_text_vec, spam_test_extra])

        # Predict labels 
        spam_test["predicted_label"] = best_model.predict(spam_test_vec)

        # Add phishing confidence if supported 
        if hasattr(best_model, "predict_proba"):
            probs = best_model.predict_proba(spam_test_vec)
            class_index = list(best_model.classes_).index("phishing")
            spam_test["phishing_confidence"] = probs[:, class_index]
        else:
            spam_test["phishing_confidence"] = None

        # Save prediction to a file
        spam_test.to_csv("models/test_predictions.csv", index=False)
        print("Saved test predictions to:")
        print("- models/test_predictions.csv")
    else:
        print("test.csv does not contain a 'text' column, so predictions were skipped.")
else:
    print("data/test.csv not found, so external test predictions were skipped.")