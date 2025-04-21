FROM python:3.9-slim-buster  # Use a lightweight Python base image

WORKDIR /site

# Copy the Markdown files into the container
COPY site/ /site/

# Install necessary tools (if needed for templating or markdown conversion)
# Example: If you wanted to use a markdown-to-html converter within the container
# RUN pip install markdown2

# Command to serve the website.  This is a simple example using Python's built-in HTTP server.
CMD ["python", "-m", "http.server", "8080"]
