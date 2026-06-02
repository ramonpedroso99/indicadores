import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def conectar_ao_banco():
        return await asyncpg.connect(
            user=os.getenv("USUARIO"),
            password=os.getenv("SENHA"),
            database=os.getenv("DATABASE"),
            host=os.getenv("HOST"),
            port=os.getenv("PORT"),
        )