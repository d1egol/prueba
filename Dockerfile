FROM python:3.11-slim

WORKDIR /app

COPY mi-agente/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "mi-agente/bot.py"]
