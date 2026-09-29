import streamlit as st
import pandas as pd
import re
from ai_api import Chat
import dynamic


class PromptManager:
    SYSTEM_PROMPT = "You are an expert in Python data visualization and analysis."

    PROMPT_TEMPLATE = """
You are working with a pandas DataFrame named `df`.
This is the result of `print(df.head())`:
{df_str}

Column names and types:
{col_info}

Follow these instructions:
{instruction_str}

Query: {query_str}
"""

    INSTRUCTION_STR = """\
1. Generate a Python function named "graph(df)" for visualizing the query.
2. The function should take the DataFrame as the only argument.
3. Make necessary transformations within the function.
4. Use Plotly Express for interactive charts.
5. Use st.plotly_chart(fig, use_container_width=True) to render.
6. Output ONLY raw Python code. NO markdown code blocks. NO explanations."""

    @classmethod
    def generate_prompt(cls, df, query):
        df_head_str = df.head().to_string()
        col_info = "\n".join([f"  - {c}: {d}" for c, d in df.dtypes.items()])
        return cls.PROMPT_TEMPLATE.format(
            df_str=df_head_str,
            col_info=col_info,
            instruction_str=cls.INSTRUCTION_STR,
            query_str=query,
        )


class ChatClient:
    def __init__(self, api_key):
        self.api_key = api_key

    @staticmethod
    def extract_code_from_code_block(output):
        match = re.search(r"```python\n(.*)```", output, re.DOTALL)
        return output if match is None else match.group(1)

    def get_response_code(self, prompt, system_prompt=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        chat = Chat(self.api_key, messages=messages)
        response_message = chat.get_response_message(stream=True)
        return self.extract_code_from_code_block(response_message["content"])


class DataVisualizer:
    def __init__(self, data_path, api_key):
        self.df = pd.read_csv(data_path)
        self.api_key = api_key

    def generate_graph_code(self, query):
        prompt = PromptManager.generate_prompt(self.df, query)
        chat_client = ChatClient(self.api_key)
        code = chat_client.get_response_code(
            prompt, system_prompt=PromptManager.SYSTEM_PROMPT
        )
        with open("dynamic.py", "w") as f:
            f.write(code)

    def show_graph(self):
        try:
            with st.spinner("Loading..."):
                dynamic.graph(self.df)
        except Exception as e:
            st.error("Error: {}".format(e))
