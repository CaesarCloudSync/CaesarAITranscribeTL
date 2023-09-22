# Use the official Python 3.9 image
FROM python:3.8

RUN export PYTHONPATH=$PWD

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN pip install --upgrade pip
RUN pip install uvicorn
# Set the working directory to /code
WORKDIR /code
#VOLUME /home/amari/Desktop/CaesarAI/CaesarFastAPI /code
# Copy the current directory contents into the container at /code
COPY ./requirements.txt /code/requirements.txt
 
# Install requirements.txt 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN python -m spacy download en_core_web_sm

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user
# Switch to the "user" user
USER user
# Set home to the user's home directory
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Local,Huggingface
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860","--reload"] 
# Fly.io
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080","--reload"] 
