
from transformers import AutoModelForCausalLM, AutoTokenizer

from src import config

class Model():
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(config.LLM_MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(
                        config.LLM_MODEL,
                        device_map="mps"
                    )

    def create_message(self, query, context):
        user_context = f"CONTEXT:\n{context}\n\nQUESTION: {query}"
        config.USER_QUARY['content'] = user_context
        return [config.CONTEXT, config.USER_QUARY]

    def get_tokenize_text(self, message):
        return self.tokenizer.apply_chat_template(
            message, tokenize=False, add_generation_prompt=True
        )

    def get_model_input(self, token_message):
        return self.tokenizer([token_message], return_tensors="pt").to("mps")

    def get_llm_response(self, model_input):
        generated_ids = self.model.generate(
            **model_input,
            max_new_tokens=256,
            temperature=0.1,
            do_sample=False,
        )
        return generated_ids

    def get_output_tokens(self, model_inputs, response):
        input_length = model_inputs.input_ids.shape[1]
        return response[0][input_length:]

    def get_text_from_tokens(self, output_tokens):
        return self.tokenizer.decode(output_tokens, skip_special_tokens=True)

    def get_response(self, query, context):
        message = self.create_message(query, context)
        tokenized_message = self.get_tokenize_text(message)
        model_input = self.get_model_input(tokenized_message)
        response = self.get_llm_response(model_input)

        output_tokens = self.get_output_tokens(model_input, response)
        return self.get_text_from_tokens(output_tokens)
    