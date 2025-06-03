# test file for api_rag.py

from . import api_rag

async def test_rag():
  prompt = "/source Qui est henri 4?"
  res = await api_rag.root(api_rag.Body(prompt=prompt))
  print(res)
