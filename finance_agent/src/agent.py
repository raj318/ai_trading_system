import sys
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode, tools_condition

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
# print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

import config

from global_lib import models
from finance_agent.src.lib.tool_functions import search_fundamentals, TOOL_REGISTRY
from finance_agent.src.lib import agent_utils

qwen_chat = ChatOllama(
    model=config.MODEL_NAME,
    temperature=0,
)

tools = list(TOOL_REGISTRY.values())

llm_with_tools = qwen_chat.bind_tools(tools)


def llm_node(state: MessagesState):
    # print(f"message = {messages}")
    # Generate a response (illustrative)
    response = llm_with_tools.invoke(state['messages'])

    return {"messages": [response]}

def get_user_input(message) -> str:
    """function to get user input"""
    return input(f"\n{message}: ").strip()

builder = StateGraph(MessagesState)

builder.add_node("llm", llm_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "llm")
builder.add_conditional_edges('llm', tools_condition)
builder.add_edge("tools", 'llm')

graph = builder.compile(checkpointer=MemorySaver())

agent_config = {'configurable': {'thread_id': '12345'}}

context_str = json.dumps(agent_utils.get_backtesting_schemas(), indent=2)
# print(f"context str = {context_str}")
while True:
    user_input = input("\nUser: ").strip()

    if user_input.lower() in ['exit', 'quit']:
        print(f"Closing Chat!")
        break

    result = graph.invoke(
        {
        "messages": [
            SystemMessage(content=context_str),
            HumanMessage(content=user_input)
        ]},
        config=agent_config
        )

    if result:
        print(result['messages'][-1])
        print(f"AI: {result['messages'][-1].content}")
