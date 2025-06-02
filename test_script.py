
# Write test for ../backend/script.py

from backend import TEST_script
import asyncio

async def test():
  prompt = "/source Qui est henri 4?"
  res = await TEST_script.root(TEST_script.Body(prompt=prompt))
  print(res)

asyncio.run(test())