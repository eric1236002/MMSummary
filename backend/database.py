# backend/database.py
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
import dotenv
dotenv.load_dotenv()

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        try:
            mongo_url = os.environ.get("MONGODB_URL", "").strip()
            if not mongo_url:
                mongo_url = "mongodb://localhost:27017"
            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client["mmsummary"]
            self.collection = self.db["history"]
        except Exception as e:
            print(f"Warning: Database connection failed. {e}")


    def insert_history(self, data):
        if self.collection is None:
            print("Warning: Skipping DB insert, collection not initialized.")
            return None
        data["created_at"] = datetime.now()
        return self.collection.insert_one(data)

    def get_history(self):
        if self.collection is None:
            return []
        records = list(self.collection.find().sort("created_at", -1).limit(20))
        
        formatted_history = []
        for r in records:
            formatted_history.append({
                "id": str(r["_id"]),
                "original_text": r.get("text", ""),
                "summary": r.get("summary", ""),
                "model": r.get("model", ""),
                "processing_time": r.get("processing_time", 0.0),
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            })
        return formatted_history

    def delete_history(self, id):
        if self.collection is None:
            return None
        return self.collection.delete_one({"_id": ObjectId(id)})