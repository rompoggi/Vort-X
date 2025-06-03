
import api_moodle
import asyncio

async def test_moodle(username="", password="", session="https://moodle.polytechnique.fr", action="update"):
  body = api_moodle.BodyMoodle(
    username=username,
    password=password,
    session=session,
    action = action,
  )
  res = await api_moodle.root(body)
  print(res)
