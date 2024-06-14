# Use the official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /autoscaler

# Copy the current directory contents into the container at /autoscaler
COPY . /autoscaler

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python-on-whales download-cli

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/

# Set the entrypoint
ENTRYPOINT ["entrypoint.sh"]
