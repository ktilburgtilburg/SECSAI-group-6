
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss

# Load the existing trained model and processed data
model = joblib.load("models/classifier.joblib")
model.n_jobs = 1

X = np.load("data/processed/X.npy")
y = np.load("data/processed/y.npy", allow_pickle=True)

# Reproduce the same validation split used in train.py
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50,
    stratify=y_temp, random_state=42
)

# Predict validation probabilities
probabilities = model.predict_proba(X_val)
predictions = model.classes_[np.argmax(probabilities, axis=1)]
confidence = np.max(probabilities, axis=1)
correct = predictions == y_val

print(f"Validation accuracy: {accuracy_score(y_val, predictions):.4f}")
print(f"Log loss: {log_loss(y_val, probabilities, labels=model.classes_):.4f}")

# Compare predicted confidence with actual accuracy
print("\nConfidence calibration:")
print(f"{'Confidence':<15} {'Samples':<12} {'Avg conf.':<12} {'Accuracy':<12}")

ece = 0.0

for lower in np.arange(0, 1, 0.1):
    upper = lower + 0.1

    if upper >= 1:
        mask = (confidence >= lower) & (confidence <= upper)
    else:
        mask = (confidence >= lower) & (confidence < upper)

    count = np.sum(mask)

    if count == 0:
        continue

    avg_conf = np.mean(confidence[mask])
    accuracy = np.mean(correct[mask])

    ece += (count / len(confidence)) * abs(avg_conf - accuracy)

    print(
        f"{lower:.1f}-{upper:.1f}         "
        f"{count:<12} "
        f"{avg_conf:<12.3f} "
        f"{accuracy:.3f}"
    )

print(f"\nExpected Calibration Error (ECE): {ece:.4f}")


# Evaluate different uncertainty thresholds

print("\n=== Uncertainty threshold evaluation ===")
print(
    f"{'Threshold':<12} "
    f"{'Flagged':<12} "
    f"{'Flagged %':<12} "
    f"{'Error rate (flagged)':<22} "
    f"{'Error rate (unflagged)':<22}"
)

for threshold in [0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
    uncertain = confidence < threshold

    flagged_count = np.sum(uncertain)
    flagged_pct = np.mean(uncertain) * 100

    flagged_errors = (
        np.mean(~correct[uncertain]) * 100
        if flagged_count > 0 else 0
    )

    unflagged_errors = (
        np.mean(~correct[~uncertain]) * 100
        if np.sum(~uncertain) > 0 else 0
    )

    print(
        f"{threshold:<12.2f} "
        f"{flagged_count:<12} "
        f"{flagged_pct:<12.2f} "
        f"{flagged_errors:<22.2f} "
        f"{unflagged_errors:<22.2f}"
    )


print("\n=== Malicious vs benign confidence ===")

classes = list(model.classes_)
benign_idx = classes.index("benign")

# Probability of any malicious category
malicious_probability = 1.0 - probabilities[:, benign_idx]

# Binary classification based on the model's predicted category
binary_predictions = predictions != "benign"
binary_correct = binary_predictions == (y_val != "benign")

print(f"Binary accuracy: {np.mean(binary_correct):.4f}")
print(f"Average predicted malicious probability: "
      f"{np.mean(malicious_probability):.4f}")

# Inspect ambiguous URLs near the 50% malicious probability boundary
for margin in [0.05, 0.10, 0.20]:
    near_boundary = np.abs(malicious_probability - 0.5) < margin

    count = np.sum(near_boundary)
    error_rate = (
        np.mean(~binary_correct[near_boundary]) * 100
        if count > 0 else 0
    )

    print(
        f"Malicious probability between "
        f"{0.5 - margin:.2f} and {0.5 + margin:.2f}: "
        f"{count} URLs, "
        f"{error_rate:.2f}% binary error"
    )


print("\n=== Combined uncertainty evaluation ===")

category_uncertain = confidence < 0.80

safety_uncertain = (
    (malicious_probability >= 0.30) &
    (malicious_probability <= 0.70)
)

combined_uncertain = category_uncertain | safety_uncertain

print(f"Total validation URLs: {len(y_val)}")
print(f"Category uncertain: {category_uncertain.sum()}")
print(f"Safety uncertain: {safety_uncertain.sum()}")
print(f"Combined uncertain: {combined_uncertain.sum()}")
print(f"Combined flagged %: {combined_uncertain.mean() * 100:.2f}%")

for name, mask in [
    ("Flagged", combined_uncertain),
    ("Unflagged", ~combined_uncertain)
]:
    if mask.sum() == 0:
        continue

    category_error = (~correct[mask]).mean() * 100
    binary_error = (~binary_correct[mask]).mean() * 100

    print(f"\n{name}: {mask.sum()} URLs")
    print(f"Category error rate: {category_error:.2f}%")
    print(f"Binary error rate: {binary_error:.2f}%")


print("\n=== False negative analysis ===")

# Malicious URLs incorrectly predicted as benign
false_negatives = (
    (y_val != "benign") &
    (predictions == "benign")
)

# False negatives not flagged as uncertain
missed_without_warning = (
    false_negatives & ~combined_uncertain
)

total_malicious = np.sum(y_val != "benign")
total_false_negatives = np.sum(false_negatives)
unflagged_false_negatives = np.sum(missed_without_warning)

print(f"Actual malicious URLs: {total_malicious}")
print(f"False negatives: {total_false_negatives}")
print(f"False negatives flagged uncertain: "
      f"{np.sum(false_negatives & combined_uncertain)}")
print(f"False negatives NOT flagged: "
      f"{unflagged_false_negatives}")

print(
    f"Malicious URL miss rate: "
    f"{total_false_negatives / total_malicious * 100:.2f}%"
)
