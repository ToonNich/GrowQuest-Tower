import firebase_admin
from firebase_admin import credentials, firestore

# === Firebase Init ===
cred = credentials.Certificate("D:/Senior_WorkTable/KEYAPI/seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# === Config ===
user_uid = "zG3FGDcmT7hEImtzCKiY73HhGOs2"
collection_path = f"tubeData/{user_uid}/readings"
BATCH_LIMIT = 500  # Firestore batch limit

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0

    batch = db.batch()
    for doc in docs:
        print(f"🗑️ Deleting document: {doc.id}")
        batch.delete(doc.reference)
        deleted += 1

    if deleted > 0:
        batch.commit()
        print(f"✅ Deleted batch of {deleted}")
        delete_collection(coll_ref, batch_size)  # Recursive call for next batch

# === Start Deleting ===
print("⚠️ Starting batch deletion of readings...")
delete_collection(db.collection(collection_path), BATCH_LIMIT)
print("✅ All documents deleted in /readings/")
