from src import config

class QDecomposer():
    def __init__(self, llm_model):
        self.llm = llm_model

    def get_sys_context(self):
        return config.query_sys_prompt

    def get_query_context(self, query):
        user_query = config.USER_QUARY.copy()
        user_query['content'] = query

    def get_context(self, query):
        return [self.get_sys_context(), self.get_query_context(query)]

    def get_decomposed_query(self, query):
        context = self.get_context(query)
        return self.llm.get_response(query, context[0])