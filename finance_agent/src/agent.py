import sys
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
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
    # print(f"@ llm node!")
    response = llm_with_tools.invoke(state['messages'])
    # print(f"response == {response}")
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

def invoke_query(query):
    result = graph.invoke(
            {
            "messages": [
                SystemMessage(content=context_str),
                HumanMessage(content=query)
            ]},
            config=agent_config
            )
    return result

def invoke_query_stream(query):
    # Pass input as human message. Keep SystemMessage in thread state initialization or prompt template.
    input_payload = {"messages": [HumanMessage(content=query)]}
    
    print("\n🚀 Starting End-to-End Pipeline...", flush=True)

    # Uses .stream() (synchronous) to run through all nodes until END
    for event in graph.stream(input_payload, config=config, stream_mode="updates"):
        for node_name, node_update in event.items():
            print(f"🔄 [Step Completed]: {node_name}", flush=True)
            
            if node_name == "agent":
                msg = node_update["messages"][-1]
                if msg.tool_calls:
                    print(f"   └─ Generated Schema & Issued Tool Call: {msg.tool_calls[0]['name']}")
                else:
                    print(f"   └─ Generated Final Summary")
                    
            elif node_name == "tools":
                msg = node_update["messages"][-1]
                print(f"   └─ Engine Output Received: {msg.content}")

    print("\n🏁 Full Execution Complete!")

def print_response(result):
    if result:
        print(result['messages'][-1])
        print(f"AI: {result['messages'][-1].content}")

def start_conversation():
    print("Starting Conversation!")
    while True:
        user_input = input("\nUser: ").strip()

        if user_input.lower() in ['exit', 'quit']:
            print(f"Closing Chat!")
            break

        result = invoke_query(user_input)

        print_response(result)

def invoke_single_command(query):
    print(f"Invoking single command : {query}")
    # result = invoke_query(query)
    result = invoke_query(query)
    print_response(result)


if __name__ == "__main__":
    # start_conversation()
    invoke_single_command("Create a buy strategy when the 9-period EMA crosses above the 21-period EMA AND the 14-period RSI is greater than 50."
"Generate a sell signal when RSI crosses below 70.")
