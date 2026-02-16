# Option 1: Ensure context and COPY of requirements file
FROM python:3.12.12

# Install system dependencies for audio processing (pipecat/LiveKit)
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    pulseaudio \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /super_services/prefect_setup

# Copy the requirements file into the container
COPY super_services/orchestration/task/deployments/requirements.txt requirements.txt
COPY super_services/prefect_setup/requirements.txt /prefect_setup/requirements.txt

# Install packages in a single RUN command to reduce image layers
RUN pip install -r /requirements.txt --use-deprecated=legacy-resolver

ENV NLTK_DATA=/usr/share/nltk_data
# Download required NLTK data at build time (punkt_tab is required by pipecat)
RUN python -m nltk.downloader -d /usr/share/nltk_data punkt punkt_tab stopwords wordnet averaged_perceptron_tagger