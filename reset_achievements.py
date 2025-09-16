from pathlib import Path
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account
from google.cloud.firestore_v1 import DELETE_FIELD

# ---- EDIT THESE TWO LINES ----
SERVICE_ACCOUNT_FILE = r"D:\Senior_WorkTable\KEYAPI\seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json"
USER_ID = "zG3FGDcmT7hEImtzCKiY73HhGOs2"     # <- put the target user's UID (doc id) here
# --------------------------------

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
db = firestore.Client(credentials=creds, project=creds.project_id)

doc_ref = db.collection("userAchievements").document(USER_ID)
snap = doc_ref.get()

if not snap.exists:
    raise SystemExit(f"❌ No doc at userAchievements/{USER_ID}")

data = snap.to_dict()

# Optional: quick backup to a JSON file next to this script
backup_name = Path(f"backup_userAchievements_{USER_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
backup_name.write_text(str(data), encoding="utf-8")
print(f"🗄  Backed up current document to {backup_name}")

# Build a single update payload that:
# - sets *.unlocked = False
# - deletes *.unlockedAt
updates = {}
for ach_key, ach_val in (data or {}).items():
    if isinstance(ach_val, dict):
        updates[f"{ach_key}.unlocked"] = False
        updates[f"{ach_key}.unlockedAt"] = DELETE_FIELD  # remove the field

if not updates:
    raise SystemExit("ℹ️  No nested achievement maps found to update.")

doc_ref.update(updates)
print(f"✅ Reset {len(updates)//2} achievements for user {USER_ID}")
