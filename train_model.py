import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from sklearn.model_selection import train_test_split, learning_curve
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
    confusion_matrix,
    ConfusionMatrixDisplay
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

# ----------------------------
# H1. Section printing helper Used to make terminal output easier to read
# ----------------------------

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ----------------------------
# H2. Label normalisation helper Converts different label styles into project labels
# ----------------------------

def normalise_labels(series):
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


# ----------------------------
# H3. Text cleaning helper Removes blanks and standardises text fields
# ----------------------------

def clean_text(series):
    return series.fillna("").astype(str).str.strip()


# ----------------------------
# H4. Final dataset cleaning helper Applies standard cleanup to any text/label dataset
# ----------------------------

def finalise_dataset(df, dataset_name):
    df = df.copy()

    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError(f"{dataset_name} must contain 'text' and 'label' columns.")

    df["text"] = clean_text(df["text"])
    df["label"] = normalise_labels(df["label"])

    df = df[(df["text"] != "") & (df["label"].isin(["phishing", "legitimate"]))]
    df = df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)

    print(f"{dataset_name} labels after cleaning:")
    print(df["label"].value_counts(dropna=False))
    print()

    return df


# ----------------------------
# H5. Dataset builder helper Converts Spam Train into the standard project format
# ----------------------------

def build_spam_train_dataset(df):
    df = df[["text", "label"]].copy()
    return finalise_dataset(df, "Spam Train")


# ----------------------------
# H6. Dataset builder helper Converts Enron into the standard project format
# ----------------------------

def build_enron_dataset(df):
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


# ----------------------------
# H7. Dataset builder helper Converts Nazario into the standard project format
# ----------------------------

def build_nazario_dataset(df):
    df = df[["subject", "body"]].copy()
    df["subject"] = clean_text(df["subject"])
    df["body"] = clean_text(df["body"])
    df["text"] = (df["subject"] + " " + df["body"]).str.strip()
    df["label"] = "phishing"

    df = df[["text", "label"]]
    return finalise_dataset(df, "Nazario")


# ----------------------------
# H8. Dataset builder helper Converts Kaggle phishing data into project format
# ----------------------------

def build_kaggle_dataset(df):
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


# ----------------------------
# H9. Dataset builder helper Converts CEAS dataset into the standard project format
# ----------------------------

def build_ceas_dataset(df):
    df = df[["sender", "subject", "body", "label"]].copy()

    df["sender"] = clean_text(df["sender"])
    df["subject"] = clean_text(df["subject"])
    df["body"] = clean_text(df["body"])
    df["label"] = normalise_labels(df["label"])

    df["text"] = (
        "From: " + df["sender"] +
        " Subject: " + df["subject"] +
        " Body: " + df["body"]
    ).str.strip()

    df = df[["text", "label"]]
    return finalise_dataset(df, "CEAS")


# ----------------------------
# H10. Vectorizer helper Creates the TF-IDF feature extractor
# ----------------------------

def create_vectorizer():
    return TfidfVectorizer(
        stop_words="english",
        max_features=10000,
        ngram_range=(1, 2)
    )


# ----------------------------
# H11. Model helper Creates the ML models used for comparison
# ----------------------------

def create_models():
    return {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Naive Bayes": MultinomialNB(),
        "SVM": LinearSVC()
    }


# ----------------------------
# H12. Contribution analysis helper Trains all models on one dataset combination
# ----------------------------

def evaluate_models_on_dataset(dataset_name, df, results_list):
    df = finalise_dataset(df, dataset_name)

    if df["label"].nunique() < 2:
        print(f"Skipping {dataset_name} - only one class found after cleaning.")
        return

    X = df["text"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    vectorizer = create_vectorizer()
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

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


# ----------------------------
# H13. Graph saving helper Saves dataset contribution analysis line graphs
# ----------------------------

def save_dataset_contribution_graphs(contrib_df):
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


# ----------------------------
# H14. Learning curve helper Saves a learning curve for the best model
# ----------------------------

def save_learning_curve(estimator, X, y, model_name, save_path):
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


# ============================================================
# 1. LOAD DATASETS
# ============================================================

print_section("1. LOAD DATASETS")

# ----------------------------
# 1.1 Define file paths
# ----------------------------

spam_train_path = "data/train.csv"
spam_test_path = "data/test.csv"
enron_path = "data/Enron legit.csv"
nazario_path = "data/Nazario Phishing.csv"
phish_kaggle_path = "data/Phishing_Email.csv"
ceas_path = "data/CEAS_08.csv"

# ----------------------------
# 1.2 Read raw dataset files
# ----------------------------

spam_train_raw = pd.read_csv(spam_train_path)
enron_raw = pd.read_csv(enron_path)
nazario_raw = pd.read_csv(nazario_path)
phish_kaggle_raw = pd.read_csv(phish_kaggle_path)
ceas_raw = pd.read_csv(ceas_path)

# ----------------------------
# 1.3 Show dataset columns
# ----------------------------

print("Spam train columns:", spam_train_raw.columns.tolist())
print("Enron columns:", enron_raw.columns.tolist())
print("Nazario columns:", nazario_raw.columns.tolist())
print("Kaggle phishing columns:", phish_kaggle_raw.columns.tolist())
print("CEAS phishing columns:", ceas_raw.columns.tolist())
print()

# ----------------------------
# 1.4 Show raw label counts
# ----------------------------

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


# ============================================================
# 2. CLEAN AND STANDARDISE DATASETS
# ============================================================

print_section("2. CLEAN AND STANDARDISE DATASETS")

# ----------------------------
# 2.1 Convert each raw dataset into text + label format
# ----------------------------

spam_train = build_spam_train_dataset(spam_train_raw)
enron = build_enron_dataset(enron_raw)
nazario = build_nazario_dataset(nazario_raw)
phish_kaggle = build_kaggle_dataset(phish_kaggle_raw)
ceas = build_ceas_dataset(ceas_raw)


# ============================================================
# 3. COMBINE DATASETS
# ============================================================

print_section("3. COMBINE DATASETS")

# ----------------------------
# 3.1 Merge all cleaned datasets
# ----------------------------

data = pd.concat(
    [spam_train, enron, nazario, phish_kaggle, ceas],
    ignore_index=True
)

print("Combined dataset size before final cleaning:", len(data))
print()
print("Labels before final cleaning:")
print(data["label"].value_counts(dropna=False))
print()

# ----------------------------
# 3.2 Final cleanup after merge
# ----------------------------

data = finalise_dataset(data, "Combined Dataset")

print("Combined dataset size after cleaning:", len(data))
print()
print("Final label counts:")
print(data["label"].value_counts(dropna=False))
print()

# ----------------------------
# 3.3 Safety check for classes
# ----------------------------

if data["label"].nunique() < 2:
    raise ValueError(
        "Training data only contains one class after cleaning. "
        "You need both 'phishing' and 'legitimate' examples."
    )


# ============================================================
# 4. DATASET CONTRIBUTION ANALYSIS
# ============================================================

print_section("4. DATASET CONTRIBUTION ANALYSIS")

# ----------------------------
# 4.1 Create output folder
# ----------------------------

os.makedirs("models", exist_ok=True)

# ----------------------------
# 4.2 Run incremental dataset tests
# ----------------------------

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

# ----------------------------
# 4.3 Save contribution table
# ----------------------------

contrib_df = pd.DataFrame(dataset_results)
contrib_df.to_csv("models/dataset_contribution_results.csv", index=False)

print("Saved dataset contribution table to:")
print("- models/dataset_contribution_results.csv")

# ----------------------------
# 4.4 Save contribution graphs
# ----------------------------

save_dataset_contribution_graphs(contrib_df)


# ============================================================
# 5. TRAIN / TEST SPLIT
# ============================================================

print_section("5. TRAIN / TEST SPLIT")

# ----------------------------
# 5.1 Split features and labels
# ----------------------------

X = data["text"]
y = data["label"]

# ----------------------------
# 5.2 Create training and test sets
# ----------------------------

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


# ============================================================
# 6. TF-IDF VECTORIZATION
# ============================================================

print_section("6. TF-IDF VECTORIZATION")

# ----------------------------
# 6.1 Create TF-IDF vectorizer
# ----------------------------

vectorizer = create_vectorizer()

# ----------------------------
# 6.2 Fit on training set and transform both datasets
# ----------------------------

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("Vectorization complete.")
print()


# ============================================================
# 7. TRAIN AND COMPARE MODELS
# ============================================================

print_section("7. TRAIN AND COMPARE MODELS")

# ----------------------------
# 7.1 Create model list
# ----------------------------

models = create_models()

# ----------------------------
# 7.2 Train each model and collect evaluation results
# ----------------------------

results = []
best_model = None
best_model_name = None
best_f1 = 0.0

for name, model in models.items():
    print("\n" + "-" * 50)
    print(f"MODEL: {name}")
    print("-" * 50)

    model.fit(X_train_vec, y_train)
    predictions = model.predict(X_test_vec)

    report = classification_report(y_test, predictions, zero_division=0)

    with open(f"models/{name}_classification_report.txt", "w") as f:
        f.write(report)

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


# ============================================================
# 8. SAVE BEST MODEL AND RESULTS
# ============================================================

print_section("8. SAVE BEST MODEL AND RESULTS")

# ----------------------------
# 8.1 Save trained model files
# ----------------------------

joblib.dump(best_model, "models/phishing_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

# ----------------------------
# 8.2 Save results table
# ----------------------------

results_df = pd.DataFrame(results)
results_df.to_csv("models/model_results.csv", index=False)

# ----------------------------
# 8.3 Save model comparison chart
# ----------------------------

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


# ============================================================
# 9. SAVE LEARNING CURVE AND CONFUSION MATRIX
# ============================================================

print_section("9. SAVE LEARNING CURVE AND CONFUSION MATRIX")

# ----------------------------
# 9.1 Save learning curve
# ----------------------------

save_learning_curve(
    best_model,
    X_train_vec,
    y_train,
    best_model_name,
    "models/learning_curve.png"
)

print("Saved learning curve to:")
print("- models/learning_curve.png")

# ----------------------------
# 9.2 Save confusion matrix
# ----------------------------

best_predictions = best_model.predict(X_test_vec)

best_report = classification_report(y_test, best_predictions, zero_division=0)

with open("models/best_model_classification_report.txt", "w")as f:
    f.write(best_report)

# Save classification report for this model
report = classification_report(y_test, predictions, zero_division=0)
with open(f"models/{name.lower().replace(' ', '_')}_classification_report.txt", "w") as f:
    f.write(report)
    
# Save false positives and false negatives for this model
best_test_results = pd.DataFrame({
    "text": X_test.reset_index(drop=True),
    "actual": y_test.reset_index(drop=True),
    "predicted": pd.Series(best_predictions)
})

false_negatives = best_test_results[
    (best_test_results["actual"] == "phishing") &
    (best_test_results["predicted"] == "legitimate")
]

false_positives = best_test_results[
    (best_test_results["actual"] == "legitimate") &
    (best_test_results["predicted"] == "phishing")
]

false_negatives.to_csv("models/false_negatives.csv", index=False)
false_positives.to_csv("models/false_positives.csv", index=False)

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


# ============================================================
# 10. TEST ON EXTERNAL TEST DATA
# ============================================================

print_section("10. TEST ON EXTERNAL TEST DATA")

# ----------------------------
# 10.1 Check if external test file exists
# ----------------------------

if os.path.exists(spam_test_path):
    spam_test = pd.read_csv(spam_test_path)
    print("Found data/test.csv")

    # ----------------------------
    # 10.2 Clean external test text
    # ----------------------------

    if "text" in spam_test.columns:
        spam_test["text"] = clean_text(spam_test["text"])
        spam_test = spam_test[spam_test["text"] != ""]

        # ----------------------------
        # 10.3 Predict labels
        # ----------------------------

        spam_test_vec = vectorizer.transform(spam_test["text"])
        spam_test["predicted_label"] = best_model.predict(spam_test_vec)

        # ----------------------------
        # 10.4 Add confidence scores if supported
        # ----------------------------

        if hasattr(best_model, "predict_proba"):
            probs = best_model.predict_proba(spam_test_vec)
            class_index = list(best_model.classes_).index("phishing")
            spam_test["phishing_confidence"] = probs[:, class_index]
        else:
            spam_test["phishing_confidence"] = None

        # ----------------------------
        # 10.5 Save predictions
        # ----------------------------

        spam_test.to_csv("models/test_predictions.csv", index=False)
        print("Saved test predictions to:")
        print("- models/test_predictions.csv")
    else:
        print("test.csv does not contain a 'text' column, so predictions were skipped.")
else:
    print("data/test.csv not found, so external test predictions were skipped.")