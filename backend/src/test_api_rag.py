# test file for api_rag.py

import api_rag

async def test_rag():
  prompt = "/help une variable gaussienne?"
  res = await api_rag.root(api_rag.Body(prompt=prompt))
  print(res["response"])

if __name__ == "__main__":
  import asyncio
  asyncio.run(test_rag())
  print("Test completed.")