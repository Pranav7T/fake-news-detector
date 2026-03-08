import pandas as pd
import numpy as np
import pickle
import re
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Load datasets
print("Loading datasets...")
fake = pd.read_csv("dataset/Fake.csv")
real = pd.read_csv("dataset/True.csv")

# Add labels
fake["label"] = 0
real["label"] = 1

# Combine datasets
data = pd.concat([fake, real])
print(f"Total samples: {len(data)}")
print(f"Fake news: {len(fake)}, Real news: {len(real)}")

# Shuffle data
data = data.sample(frac=1).reset_index(drop=True)

# Use article text and title for better features
data['combined_text'] = data['title'] + ' ' + data['text']
texts = data["combined_text"]
labels = data["label"]

# Enhanced text cleaning
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    # Remove special characters but keep letters and numbers
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove single characters
    text = re.sub(r'\b[a-zA-Z0-9]\b', '', text)
    return text.strip()

print("Cleaning text...")
texts = texts.apply(clean_text)

# Enhanced TF-IDF Vectorizer
vectorizer = TfidfVectorizer(
    stop_words="english", 
    max_df=0.7,
    min_df=3,
    ngram_range=(1, 3),  # Use trigrams
    max_features=15000
)

print("Vectorizing text...")
X = vectorizer.fit_transform(texts)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42, stratify=labels
)

# Test multiple models
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Naive Bayes': MultinomialNB(),
    'SVM': SVC(probability=True, random_state=42)
}

print("\nTraining and evaluating models...")
best_model = None
best_accuracy = 0
best_name = ""

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train, y_train)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    print(f"Cross-validation accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Test accuracy
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Test accuracy: {accuracy:.4f}")
    
    if accuracy > best_accuracy:
        best_accuracy = accuracy
        best_model = model
        best_name = name

print(f"\n=== BEST MODEL: {best_name} ===")
print(f"Best accuracy: {best_accuracy:.4f}")

# Final predictions with best model
final_predictions = best_model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, final_predictions, target_names=['Fake', 'Real']))

# Save best model and vectorizer
print("\nSaving best model...")
with open("model.pkl", "wb") as f:
    pickle.dump(best_model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print(f"Model and Vectorizer saved successfully.")
print(f"Best model: {best_name} with accuracy: {best_accuracy:.4f}")
