import sys
from pathlib import Path

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

import config
from finance_agent.src.lib import agent_utils

def main():
    question = sys.argv[1]

    print(f"user question={question}")

    context = config.AGENT_PROMPT.copy()
    context[1]['content'] = question

    max_loops = 2

    response = ""
    while max_loops > 0:
        # print(f"loop counter = {max_loops}")
        # print(f"context at start === {context}")
        response = agent_utils.get_content_response(context)

        # print(f"response after llm = {response}")
        if agent_utils.response_contains_tool_calls(response):
            print(f"will execute requested tools")
            results = agent_utils.execute_requested_tools(response)
            print(f"adding tools output to the message {results}")
            agent_utils.add_tool_result_to_message(context, results)
            print(f"context= {context}")
        else:
            print(f"response in else== {response}")
            break
        max_loops -= 1
    # if max_loops == 0:
    # print(f"response outside while = {context}")

if __name__ == "__main__":
    main()