
# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim as base

FROM base as builder
RUN apt-get update \
    && apt-get install gcc=4:10.* git=1:2.* -y \
    && apt-get clean
COPY requirements.txt /app/requirements.txt
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
RUN pip install --user -r requirements.txt
COPY . /app

FROM base as app
COPY . /app
COPY --from=builder /root/.local /root/.local

# # Keeps Python from generating .pyc files in the container
# ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Access local binaries
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app

# During debugging, this entry point will be overridden. For more information, refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "app.py"]
