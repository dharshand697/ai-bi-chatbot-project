import pickle
import sys
import os

sys.path.append(os.path.dirname(__file__))

with open("models/intent_model.pkl", "rb") as f:
    model = pickle.load(f)
with open("models/vectorizer.pkl", "rb") as f:
    vec = pickle.load(f)

print("Intent Classifier - Interactive Tester")
print("Type any query to see the predicted intent.")
print("Type 'quit' to exit.")
print("-" * 45)

while True:
    query = input("\nYour query: ").strip()

    if query.lower() == "quit":
        print("Exiting.")
        break
    if not query:
        continue

    intent     = model.predict(vec.transform([query]))[0]
    confidence = model.predict_proba(vec.transform([query])).max()

    if confidence >= 0.80:
        level = "High"
    elif confidence >= 0.50:
        level = "Medium"
    else:
        level = "Low - consider adding more training examples"

    print(f"  Intent     : {intent}")
    print(f"  Confidence : {confidence:.0%} ({level})")