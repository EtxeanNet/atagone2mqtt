
# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim as base

FROM base as builder
RUN apt-get update \
    && apt-get install gcc git -y \
    && apt-get clean
COPY requirements.txt /app/requirements.txt
WORKDIR /tmp
RUN git clone https://github.com/ArdKuijpers/pyatag.git

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
RUN pip install --user -r requirements.txt
COPY . /app

FROM base as app
ADD . /app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /tmp/pyatag/pyatag /app/pyatag

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Access local binaries
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app

# During debugging, this entry point will be overridden. For more information, refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "app.py"]
