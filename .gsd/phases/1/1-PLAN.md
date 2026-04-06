---
phase: 1
plan: 1
wave: 1
---

# Plan 1.1: Project Structure & Synthetic Data Generator

## Objective
Create the backend directory skeleton and write the standalone data generation
module (`generate_data.py`) that produces ~50,000 synthetic UPI transaction records
with a realistic ~2% fraud rate. This is the raw input the SMOTE + training plan
depends on. No model work happens here — only structure and data.

## Context
- `.gsd/SPEC.md` — Feature list (9 features), fraud label definition
- `.gsd/ROADMAP.md` — Phase 1 deliverables

## Tasks

<task type="auto">
  <name>Create backend directory skeleton</name>
  <files>
    backend/__init__.py
    backend/ml_pipeline/__init__.py
    backend/ml_pipeline/generate_data.py
    backend/models/.gitkeep
    backend/app/__init__.py
    backend/app/api/__init__.py
    backend/app/core/__init__.py
    backend/app/db/__init__.py
    backend/app/ml/__init__.py
    backend/app/schemas/__init__.py
    backend/requirements.txt
  </files>
  <action>
    1. Create the full directory tree for backend/ as specified in SPEC.md.
       All __init__.py files should be empty. backend/models/ should contain
       a .gitkeep so it's tracked but the actual model artifacts are gitignored.

    2. Write backend/requirements.txt with these exact pinned packages:
       ```
       fastapi==0.111.0
       uvicorn[standard]==0.29.0
       sqlalchemy==2.0.30
       aiosqlite==0.20.0
       python-jose[cryptography]==3.3.0
       passlib[bcrypt]==1.7.4
       tensorflow==2.16.1
       scikit-learn==1.4.2
       imbalanced-learn==0.12.2
       numpy==1.26.4
       pandas==2.2.2
       pydantic==2.7.1
       pydantic-settings==2.2.1
       python-multipart==0.0.9
       python-dotenv==1.0.1
       ```

    3. Add to .gitignore (append, do not overwrite):
       ```
       backend/models/*.h5
       backend/models/*.pkl
       backend/*.db
       backend/__pycache__/
       backend/app/**/__pycache__/
       backend/ml_pipeline/__pycache__/
       ```
  </action>
  <verify>
    cd backend && python -c "import pathlib; dirs=['app/api','app/core','app/db','app/ml','app/schemas','ml_pipeline','models']; missing=[d for d in dirs if not pathlib.Path(d).exists()]; print('MISSING:',missing) if missing else print('Structure OK')"
  </verify>
  <done>
    - backend/ directory tree matches SPEC.md structure exactly
    - requirements.txt exists with all listed packages
    - .gitignore updated with model artifact patterns
  </done>
</task>

<task type="auto">
  <name>Write synthetic UPI transaction data generator</name>
  <files>
    backend/ml_pipeline/generate_data.py
  </files>
  <action>
    Write backend/ml_pipeline/generate_data.py with a single function:
    `generate_upi_transactions(n_samples=50000, fraud_rate=0.02, random_state=42) -> pd.DataFrame`

    The function must produce a DataFrame with exactly these columns:
    ['hour', 'day', 'month', 'year', 'merchant_category', 'amount', 'user_age',
     'state_code', 'zip_prefix', 'is_fraud']

    **Generation rules for LEGITIMATE transactions (98%):**
    - hour: weighted toward business hours (8-22), use np.random.choice with weights
    - day: 1-28 uniform
    - month: 1-12 uniform
    - year: 2023 or 2024 (random choice)
    - merchant_category: 0-7 uniform int (0=Food, 1=Retail, 2=Travel, 3=Entertainment,
      4=Healthcare, 5=Education, 6=Utilities, 7=Other)
    - amount: log-normal distribution, loc=5.5, scale=1.2 (produces realistic INR amounts
      like 50-5000), clip to [10, 50000]
    - user_age: normal distribution, mean=32, std=10, clip to [18, 70], cast to int
    - state_code: 0-28 uniform int (29 Indian states/UTs)
    - zip_prefix: 100-999 uniform int (first 3 digits of 6-digit Indian PIN)
    - is_fraud: 0

    **Generation rules for FRAUDULENT transactions (2%):**
    All features same ranges as legitimate EXCEPT these anomaly signals:
    - hour: heavily weighted toward night hours (0-5, 23) — use
      np.random.choice([0,1,2,3,4,5,23], size=n_fraud)
    - amount: much higher — log-normal loc=8.5, scale=1.5, clip to [5000, 200000]
    - user_age: slightly younger skew, mean=25, std=8, clip [18, 50]
    - merchant_category: weighted toward Travel(2) and Other(7) — riskier categories

    Concatenate legitimate + fraudulent rows, shuffle with random_state=42, reset index.
    Return the DataFrame.

    Also write a `if __name__ == "__main__":` block that:
    - Calls generate_upi_transactions()
    - Prints shape, fraud count, fraud rate
    - Prints df.describe() for sanity check
    - Saves to backend/ml_pipeline/sample_data_check.csv (first 100 rows only)

    DO NOT use any ML libraries in this file — only numpy, pandas, random.
    DO NOT save the full dataset to disk — it will be generated in memory by train.py.
  </action>
  <verify>
    cd backend && python -c "
from ml_pipeline.generate_data import generate_upi_transactions
df = generate_upi_transactions(n_samples=1000, fraud_rate=0.02)
assert list(df.columns) == ['hour','day','month','year','merchant_category','amount','user_age','state_code','zip_prefix','is_fraud'], 'Wrong columns'
assert df['is_fraud'].sum() > 0, 'No fraud samples generated'
fraud_rate = df['is_fraud'].mean()
assert 0.01 <= fraud_rate <= 0.05, f'Fraud rate out of range: {fraud_rate}'
assert df['hour'].between(0,23).all(), 'Invalid hours'
assert df['amount'].min() >= 10, 'Amount too low'
assert df['user_age'].between(18,70).all(), 'Invalid ages'
print(f'PASS — {len(df)} rows, fraud rate={fraud_rate:.3f}')
"
  </verify>
  <done>
    - `generate_upi_transactions(n_samples=1000)` runs without error
    - Returns DataFrame with exactly 9 features + is_fraud column
    - Fraud rate is approximately 2% (within 1%-5% for small n)
    - All feature values within specified ranges
    - Fraudulent transactions exhibit anomaly patterns (higher amounts, night hours)
  </done>
</task>

## Success Criteria
- [ ] `backend/` directory tree created with all subdirectories and __init__.py files
- [ ] `backend/requirements.txt` exists with all 15 packages listed
- [ ] `backend/ml_pipeline/generate_data.py` exists and is importable
- [ ] Running the verify command in the `generate_data.py` task outputs PASS
- [ ] `.gitignore` updated with model artifact patterns
