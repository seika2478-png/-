
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN 설정을 확인해 주세요!")

# Ollama 로컬 AI 연결
ai = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

histories = {}

PERSONALITY = """
너의 이름은 이안(IAN)이다.
너는 디스코드에서 활동하는 친근한 AI 대화형 로봇이다.

- 친절하고 자연스럽게 대화한다.
- 기본적으로 한국어를 사용한다.
- 적절한 유머를 사용한다.
- 자신을 이안이라고 소개한다.
"""

CALL_NAME = "이안아"


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("이안아라고 불러 주세요!")
    )
    print(f"이안 접속 완료! {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ! 명령어 처리
    await bot.process_commands(message)

    # 명령어에는 AI가 반응하지 않음
    if message.content.startswith("!"):
        return

    # '이안아'가 없으면 무시
    if CALL_NAME not in message.content:
        return

    # 호출어 제거
    user_message = message.content.replace(CALL_NAME, "", 1).strip()

    if not user_message:
        user_message = "나를 불렀어?"

    user_id = message.author.id

    if user_id not in histories:
        histories[user_id] = []

    histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    histories[user_id] = histories[user_id][-6:]

    async with message.channel.typing():
        try:
            print(f"AI 응답 요청: {message.author}")

            response = await ai.chat.completions.create(
                model="qwen2.5:1.5b",
                messages=[
                    {"role": "system", "content": PERSONALITY},
                    *histories[user_id]
                ],
                 max_tokens=120,
                 temperature=0.7
            )

            answer = (
                response.choices[0].message.content
                or "답변을 만들지 못했어요."
            )

            histories[user_id].append({
                "role": "assistant",
                "content": answer
            })

            histories[user_id] = histories[user_id][-6:]

            for i in range(0, len(answer), 1900):
                await message.reply(
                    answer[i:i + 1900],
                    mention_author=False,
                    allowed_mentions=discord.AllowedMentions.none()
                )

        except Exception as e:
            print("Ollama 오류:", repr(e))
            await message.reply(
                "AI 연결에 문제가 생겼어요. Ollama를 확인해 주세요!",
                mention_author=False
            )


@bot.command()
async def 안녕(ctx):
    await ctx.send("안녕하세요!")


@bot.command()
async def 정보(ctx):
    await ctx.send("저는 AI 대화형 로봇 이안입니다!")


@bot.command()
async def 초기화(ctx):
    histories.pop(ctx.author.id, None)
    await ctx.send("대화 기록을 초기화했어요!")


bot.run(DISCORD_TOKEN)
