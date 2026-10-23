import sys
from pathlib import Path

from transformers import pipeline
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace
from langchain_ollama import ChatOllama

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

import config

from global_lib import models
from finance_agent.src.lib.tool_functions import search_fundamentals, TOOL_REGISTRY
from finance_agent.src.lib.qwan_chat_model import QwenToolChatModel


qwen_chat = ChatOllama(
    model="qwen2.5:7b",
    temperature=0,
)

tools = list(TOOL_REGISTRY.values())

checkpointer = InMemorySaver()

agent = create_agent(
    model=qwen_chat,
    tools = tools,
    system_prompt="""
"You are a financial expert, you try to understand the question and use available tools to get a company fundamentals like revenue, profits, ebitda etc.. from tools and also use your interlligence to answer user questions
""",
    checkpointer=checkpointer,
)

agent_config = {
    "configurable": {
        "thread_id": "fundamental_agent_0001"
    }
}

while True:
    user_input = input("\nYou: ").strip()

    if user_input.lower() in {"exit", "quit"}:
        print("Ending conversation.")
        break

    if not user_input:
        continue


    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": user_input}
            ]
        },
        config=agent_config,
    )

    state = agent.get_state(agent_config)

    history = state.values.get("messages", [])

    final_answer = next(
        (
            message
            for message in reversed(result["messages"])
            if message.type == "ai" and not message.tool_calls
        ),
        None,
    )

    if final_answer:
        print(f"\nAssistant: {final_answer.content}")
    else:
        print("\nAssistant: No final answer was returned.")
        break
