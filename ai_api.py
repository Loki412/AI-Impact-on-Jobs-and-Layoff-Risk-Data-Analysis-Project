import json
from openai import OpenAI


class Chat:
    def __init__(
        self,
        api_key,
        messages=None,
        model="MiniMaxAI/MiniMax-M2.5",
        base_url="https://api.siliconflow.cn/v1",
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.messages = messages or []

    def add_messages(self, messages):
        if isinstance(messages, dict):
            messages = [messages]
        self.messages.extend(messages)

    def get_streamed_response_message(self, response):
        content = ""
        message = {"role": "assistant", "content": None}
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                content += delta.content
                print(delta.content, end="")
        if content:
            message["content"] = content
            print()
        return message

    def get_response_message(self, new_message_or_prompt=None, stream=True):
        if new_message_or_prompt:
            if isinstance(new_message_or_prompt, str):
                self.add_messages([{"role": "user", "content": new_message_or_prompt}])
            else:
                self.add_messages(new_message_or_prompt)
        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages, stream=stream
        )
        if stream:
            message = self.get_streamed_response_message(response)
        else:
            message = response.choices[0].message.model_dump()
        self.add_messages([message])
        return message
