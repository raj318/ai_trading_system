import sys
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import HumanMessage

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

from global_lib import models
from finance_agent.src.lib.tool_functions import search_fundamentals
from finance_agent.src.lib.qwan_chat_model import QwenToolChatModel

import os

from langchain_core.prompts import ChatPromptTemplate
from transformers import pipeline
model_id = "Qwen/Qwen3-0.6B"


pipe = pipeline(
    "text-generation",
    model=model_id,
    tokenizer=model_id,
    max_new_tokens=512,
    do_sample=False,
    return_full_text=False
)

llm = HuggingFacePipeline(pipeline=pipe)

chat_model = ChatHuggingFace(llm=llm)

qwen_chat = QwenToolChatModel(
    pipeline=llm.pipeline,
    tokenizer=chat_model.tokenizer,
    generation_kwargs={
        'max_new_tokens': 300,
        'do_sample': False
    }
)
tools = [search_fundamentals]

model_with_tools = qwen_chat.bind_tools(tools)


response = model_with_tools.invoke([
    HumanMessage(
        content="What is Reliance Industries' EBITDA?"
    )
])
print(response.content)
print(response.tool_calls)