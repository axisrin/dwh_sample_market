import os

# Local constants
DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# MinIO buckets
BUCKET_DIR = "shop-transactions"