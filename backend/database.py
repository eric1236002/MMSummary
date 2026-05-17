# backend/database.py
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
import dotenv
dotenv.load_dotenv()

class Database:
    def __init__(self):
        # 這個類別封裝 MongoDB 存取，讓 API 不需要直接處理連線細節。
        # 失敗時不直接丟出例外，而是保留 None，讓上層可以選擇降級（例如跳過寫入）。
        self.client = None
        self.db = None
        self.collection = None
        try:
            # 優先使用環境變數的 MongoDB 位址，沒有設定就退回本機預設。
            mongo_url = os.environ.get("MONGODB_URL", "").strip()
            if not mongo_url:
                mongo_url = "mongodb://localhost:27017"
            # 先建立 client 並 ping，確保連線真的可用，再初始化 db/collection。
            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client["mmsummary"]
            self.collection = self.db["history"]
        except Exception as e:
            # 連線失敗時只記錄警告，避免 API 啟動完全失敗。
            print(f"Warning: Database connection failed. {e}")


    def insert_history(self, data):
        # 若 collection 尚未初始化，代表 DB 不可用，這裡直接略過寫入。
        if self.collection is None:
            print("Warning: Skipping DB insert, collection not initialized.")
            return None
        # 寫入時間由後端統一補上，避免前端或呼叫端自己帶值造成格式不一致。
        data["created_at"] = datetime.now()
        return self.collection.insert_one(data)

    def get_history(self):
        # 讀取最近 20 筆並轉成前端易用的格式，避免 API 層重複處理 ObjectId / datetime。
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
                # 回傳固定字串格式，方便前端列表顯示與排序。
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            })
        return formatted_history

    def delete_history(self, id):
        # 依 ObjectId 刪除單筆歷史紀錄；若 collection 不可用則直接回傳 None。
        if self.collection is None:
            return None
        return self.collection.delete_one({"_id": ObjectId(id)})