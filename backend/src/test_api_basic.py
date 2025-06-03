# test file for api_basic.py

from . import api_basic

async def test_basic():
  prompt = "/source Qui est henri 4?"
  res = await api_basic.root(api_basic.Body(prompt=prompt))
  print(res)
