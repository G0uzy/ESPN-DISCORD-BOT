FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir discord.py espn-api matplotlib python-dotenv requests

CMD ["python", "bot.py"]
