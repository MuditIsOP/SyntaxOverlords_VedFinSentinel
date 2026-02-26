# IEEE-CIS Fraud Detection Dataset

**Source:** [Kaggle IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection)

## Directory Structure

```
data/ieee-cis/
├── raw/                     # Original competition CSV files
│   ├── train_transaction.csv   (~683 MB, 590,540 rows)
│   ├── train_identity.csv      (~26 MB)
│   ├── test_transaction.csv    (~613 MB)
│   ├── test_identity.csv       (~25 MB)
│   └── sample_submission.csv
└── README.md
```

## Dataset Description

The IEEE-CIS Fraud Detection dataset contains real-world e-commerce transaction data
provided by Vesta Corporation. It includes:

- **Transaction table**: TransactionAmt, ProductCD, card details, address info,
  count features (C1-C14), time-delta features (D1-D15), match/mismatch flags (M1-M9),
  and Vesta-engineered features (V1-V339)
- **Identity table**: Device information, identity matching scores

**Fraud rate**: ~3.5% of transactions are fraudulent.

## Usage

The `backend/generate_model.py` script reads from `data/ieee-cis/raw/` and trains
the XGBoost + Isolation Forest ensemble used by VedFin Sentinel.
