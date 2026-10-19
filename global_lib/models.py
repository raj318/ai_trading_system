from transformers import AutoModelForCausalLM, AutoTokenizer
import config

TOKENIZER = AutoTokenizer.from_pretrained(config.LLM_MODEL)
MODEL = AutoModelForCausalLM.from_pretrained(
                        config.LLM_MODEL,
                        device_map="mps"
                    )
