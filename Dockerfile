# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy all files in the local directory to the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Set the command to run when the container launches
ENTRYPOINT ["python", "run.py"]





#docker build -t eucanimage-image-preprocessing .

#docker run --rm -v D:\Data03\XNAT:/data -p 9000:9000 eucanimage-image-preprocessing -config_path /data/config/xnat_local.json -data_path /data/local_data -log_level info

