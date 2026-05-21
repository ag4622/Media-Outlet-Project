FROM python:3.13

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard.py filtering.py metrics.py status_tracking.py utils.py /app/
COPY tabs/ /app/tabs/
COPY rag/ /app/rag/

CMD ["streamlit", "run", "dashboard.py"]