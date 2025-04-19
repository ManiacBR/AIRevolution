import json
import os

MEMORY_FILE = "memory.json"

class MemoryManager:
    def __init__(self):
        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "w") as f:
                json.dump({}, f)
        with open(MEMORY_FILE, "r") as f:
            self.data = json.load(f)

    def get_history(self, user_id):
        return self.data.get(user_id, [])

    def save_user_message(self, user_id, message):
        if user_id not in self.data:
            self.data[user_id] = []
        self.data[user_id].append({"role": "assistant" if "gpt" in message.lower() else "user", "content": message})
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.data, f, indent=2)
