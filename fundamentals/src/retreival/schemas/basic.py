from pydantic import BaseModel, Field

class UserQuary(BaseModel):
    quary: str