import uvicorn
import sys

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends, Request
from pathlib import Path


current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
sys.path.append(str(parent_dir))

from services import retreivar
from schemas.basic import UserQuary
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.qdrant = retreivar.QdrantRetreivar()
    yield
    # qdrant.close()

app = FastAPI(title="RAG retreival system", lifespan=lifespan)

def get_db_wrapper(request: Request):
    wrapper = getattr(request.app.state, "qdrant", None)
    if wrapper is None:
        raise HTTPException(status_code=500, detail="Database service not initialized.")
    return wrapper

@app.get('/')
def health_check():
    return {'status': 'ok', "message": "FastAPI for backend RAG retrieval system"}

@app.post('/quary')
def user_quary(request: UserQuary, db= Depends(get_db_wrapper)):

    return db.get_top_n_results(query=request.quary)



if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8005, reload=True)

