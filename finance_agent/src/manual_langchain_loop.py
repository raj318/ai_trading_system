import sys
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

import config
from global_lib import models
from finance_agent.src.lib.tool_functions import search_fundamentals, TOOL_REGISTRY
from finance_agent.src.lib.qwan_chat_model import QwenToolChatModel

import os

from langchain_core.prompts import ChatPromptTemplate
from transformers import pipeline
# model_id = "Qwen/Qwen3-0.6B"
model_id = config.LLM_MODEL

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
tools = list(TOOL_REGISTRY.values())
print(f"\n\ntools = {tools}\n\n")

model_with_tools = qwen_chat.bind_tools(tools)


messages = [
    SystemMessage("You are a financial agent you work with tools to get a company fundamentals like revenue, profits, ebitda etc.."),
    HumanMessage(
            content="What is Reliance Industries' EBITDA for last financial year?"
        )
]

response = model_with_tools.invoke(messages)

max_iterations = 5

while max_iterations> 0: 
    messages.append(response)
    
    if response.tool_calls:
        print(f"tool calls = {response.tool_calls}")
        for tool_call in response.tool_calls:
            if tool_call['name'] in TOOL_REGISTRY.keys():
                fun = TOOL_REGISTRY[tool_call['name']]
                tool_resp = fun.invoke(tool_call['args'])
                t_message = ToolMessage(
                        content=str(tool_resp),
                        tool_call_id=tool_call['id']
                    )
                messages.append(t_message)
        response = model_with_tools.invoke(messages)
            
    else:
        break

print(response.content)