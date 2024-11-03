FROM python:3.12

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

#Run the application on port 8080
ENTRYPOINT ["streamlit", "run", "app.py", "--theme.base=dark", "--theme.primaryColor=#77dd77", "--server.port=8080", "--server.enableCORS=false", "--server.enableWebsocketCompression=false", "--server.address=0.0.0.0"]
