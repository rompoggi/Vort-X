# test file for api_rag.py

import api_rag

async def test_rag():
  prompt = "/source C'est quoi la définition d'une variable gaussienne multivariée ?"
  res = await api_rag.root(api_rag.Body(prompt=prompt, context=""))
  print(res["response"])

if __name__ == "__main__":
  import asyncio
  asyncio.run(test_rag())
  print("Test completed.")