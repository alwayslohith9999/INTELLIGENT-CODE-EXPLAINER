"""
Train the local GCC diagnostic classifier from synthetic data (scikit-learn).
Writes models/gcc_explainer.joblib — run once after install or when you extend explainer_catalog.py.

Usage:
  python train_explainer.py
"""
from __future__ import annotations

from pathlib import Path

from explainer_catalog import expanded_training_pairs
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE = Path(__file__).resolve().parent
OUT = BASE / "models" / "gcc_explainer.joblib"


def main() -> None:
    pairs = expanded_training_pairs()
    X = [p[0] for p in pairs]
    y = [p[1] for p in pairs]

    pipe = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 3),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=500,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )
    pipe.fit(X, y)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(pipe, OUT)
    print(f"Saved {OUT} ({len(X)} training rows, {len(set(y))} classes)")


if __name__ == "__main__":
    main()
