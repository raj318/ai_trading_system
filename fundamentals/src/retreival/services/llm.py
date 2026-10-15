
from transformers import AutoModelForCausalLM, AutoTokenizer

from src import config
from src.storage import metadata_models
import outlines
import re
import json
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
        user_q = config.USER_QUARY.copy()
        context = config.CONTEXT.copy()
        context['content'] = metadata_models.get_system_prompt()
        user_q['content'] = query

        prompt_text = self.get_tokenize_text([context, user_q])
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to("mps")

        # 2. Standard Hugging Face Generation
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.1,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )

        # 3. Decode output tokens into raw text (stripping the input prompt tokens)
        input_length = inputs.input_ids.shape[1]
        raw_output_text = self.tokenizer.decode(
            outputs[0][input_length:], 
            skip_special_tokens=True
        )

        clean_json_str = re.sub(r"```json\s*|\s*```", "", raw_output_text).strip()
        
        try:
            query_result = catelog_context.model_validate_json(clean_json_str)
        except Exception as e:
            print(f"JSON Parsing Error: {e}")
            # Fallback to raw JSON dict if Pydantic validation fails
            query_result = json.loads(clean_json_str)

        # print(f"query result = {query_result}")
        return query_result

    def get_metadata_filter_outlines_response(self, query, catelog_context):
        outline_generator = outlines.Generator(self.outline_model, catelog_context)
        user_q = config.USER_QUARY.copy()
        context = config.CONTEXT.copy()
        context['content'] = metadata_models.get_system_prompt()
        user_q['content'] = query
        query_prompt = self.get_tokenize_text([context, user_q])
        query_result = outline_generator(query_prompt, max_new_tokens=350, temperature=0.1)
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
            max_new_tokens=350,
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
    