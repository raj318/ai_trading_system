import json
import requests

test_question_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/src/test/rag_test_reliance_annual_reports_2024.json'
test_result_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/src/test/rag_test_results_reliance_annual_reports_2024.json'
rag_endpoint = 'http://127.0.0.1:8005/quary'

with open(test_question_path, 'r', encoding='utf-8') as fd:
    test_questions = json.load(fd)

results = []

for question in test_questions:
    print(question['question'])
    payload = {
        'quary': question['question']
    }
    response = requests.post(rag_endpoint, json=payload)
    result = {
        'question': question['question'],
        'response': None
    }
    resp = ""
    if response.status_code == 200:
        print(response.json())
        resp = response.json()
    else:
        print(response.text)
        resp = "None"
    result = {
            'question': question['question'],
            'response': resp,
            'expected_answer': question['expected_answer']
    }
    results.append(result)

with open(test_result_path, 'w', encoding='utf-8') as fd:
    json.dump(results, fd, indent=2)
