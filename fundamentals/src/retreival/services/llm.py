
from transformers import AutoModelForCausalLM, AutoTokenizer

from src import config
from src.storage import metadata_models
import outlines
from importlib.metadata import version



class Model():
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(config.LLM_MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(
                        config.LLM_MODEL,
                        device_map="mps"
                    )
        self.outline_model = outlines.from_transformers(
            self.model,
            self.tokenizer
        )

    def get_metadata_filter_response(self, query, catelog_context):
        print(f"inside model = {query}")
        outline_generator = outlines.Generator(self.outline_model, catelog_context)
        user_q = config.USER_QUARY.copy()
        context = config.CONTEXT.copy()
        context['content'] = metadata_models.get_system_prompt()
        user_q['content'] = query
        query_prompt = self.get_tokenize_text([context, user_q])
        query_result = outline_generator(query_prompt, max_new_tokens=200, temperature=0.1)
        print(f"query result = {query_result}")
        return query_result

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
            max_new_tokens=300,
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
    