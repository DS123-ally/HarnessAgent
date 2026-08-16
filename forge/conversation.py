class Conversation:
    def __init__(self):
        self.messages = []

    def add_system(self, content: str):
        self.messages.append({
            "role": "system",
            "content": content
        })

    def add_user(self, content: str):
        self.messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant(self, content: str):
        self.messages.append({
            "role": "assistant",
            "content": content
        })

    def get_messages(self):
        return self.messages