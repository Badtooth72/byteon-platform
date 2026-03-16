from pymongo import MongoClient

# Connect to MongoDB (update this if needed)
client = MongoClient("mongodb://mongo:27017/")
db = client["auth_db"]
users = db["users"]

# Track how many we fix
updated = 0
skipped = 0

for user in users.find():
    original_username = user.get("username")
    if not original_username:
        continue

    lowercase_username = original_username.lower()

    # Only fix if the username is not already lowercase
    if original_username != lowercase_username:
        conflict = users.find_one({"username": lowercase_username})
        if conflict:
            print(f"⚠️ Skipping '{original_username}' → '{lowercase_username}' — already exists.")
            skipped += 1
            continue

        print(f"🔁 Updating '{original_username}' → '{lowercase_username}'")

        # Update username and display_name if needed
        user["username"] = lowercase_username
        if "display_name" in user:
            user["display_name"] = lowercase_username

        # Insert new document and delete the old one
        user.pop("_id", None)
        users.insert_one(user)
        users.delete_one({ "_id": user["_id"] })

        updated += 1

print(f"\n✅ Done! Lowercased {updated} users. Skipped {skipped} due to conflicts.")

