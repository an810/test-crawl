import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
import joblib
import os

# === 1. Load data ===
df = pd.read_csv("cleaning/output/processed_data.tsv", sep="\t")

# === 2. Preprocess ===
features = ['price', 'area', 'number_of_bedrooms', 'number_of_toilets', 'district', 'legal']
df_clean = df.dropna(subset=features + ['url_id']).copy()  # include url_id for deduplication

# === 3. Define user preference ===
user_pref = {
    'price': 14,
    'area': 70,
    'number_of_bedrooms': 3,
    'number_of_toilets': 3,
    'district': [1, 2, 3],
    'legal': 2,  # e.g., user wants listings with red book or clear ownership
}

# === 4. Compute similarity score ===
def compute_similarity_score(row, pref):
    score = 0
    score += abs(row['price'] - pref['price']) / pref['price']
    score += abs(row['area'] - pref['area']) / pref['area']
    score += abs(row['number_of_bedrooms'] - pref['number_of_bedrooms']) / (pref['number_of_bedrooms'] + 1)
    score += abs(row['number_of_toilets'] - pref['number_of_toilets']) / (pref['number_of_toilets'] + 1)

    preferred_districts = pref['district'] if isinstance(pref['district'], list) else [pref['district']]
    score += 0 if row['district'] in preferred_districts else 1

    legal_diff = abs(row['legal'] - pref['legal'])
    score += 0 if legal_diff == 0 else (0.5 if legal_diff == 1 else 1)

    return 1 / (1 + score)

df_clean['score'] = df_clean.apply(lambda row: compute_similarity_score(row, user_pref), axis=1)

# === 5. Train model ===
X = df_clean[features]
y = df_clean['score']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

pipeline.fit(X_train, y_train)

# === 6. Evaluate ===
y_pred = pipeline.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Test MSE: {mse:.6f}")

# === 6.1 Save model ===
# Create models directory if it doesn't exist
os.makedirs('models/saved', exist_ok=True)

# Save the model
model_path = 'models/saved/recommendation_model.joblib'
joblib.dump(pipeline, model_path)
print(f"Model saved to {model_path}")

# === 7. Recommend listings ===
def recommend(df: pd.DataFrame, model: Pipeline, user_pref: dict, top_n: int = 5) -> pd.DataFrame:
    X_input = df[features].copy()
    predicted_scores = model.predict(X_input)

    df_result = df.copy()
    df_result['predicted_score'] = predicted_scores

    # Filter by preferred districts
    preferred_districts = user_pref['district'] if isinstance(user_pref['district'], list) else [user_pref['district']]
    df_result = df_result[df_result['district'].isin(preferred_districts)]

    # Remove duplicates based on `url_id`
    df_result = df_result.drop_duplicates(subset='url_id')

    # Return top-N
    return df_result.sort_values(by="predicted_score", ascending=False).head(top_n)

# === 8. Get top recommendations ===
recommendations = recommend(df_clean, pipeline, user_pref, top_n=5)
print(recommendations[['url_id', 'title', 'price', 'area', 'number_of_bedrooms',
                       'number_of_toilets', 'district', 'legal', 'predicted_score']])
