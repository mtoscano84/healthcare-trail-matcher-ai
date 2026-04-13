FROM debian:bookworm-slim

# Install curl to download the binary
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Download the MCP Toolbox Linux binary
RUN curl -L -O https://storage.googleapis.com/genai-toolbox/v0.21.0/linux/amd64/toolbox
RUN chmod +x toolbox

# Expose the port the server will listen on
EXPOSE 5000

# Run the toolbox in MCP server mode using the mounted tools.yaml file
CMD ["./toolbox", "--tools-file", "/etc/mcp-toolbox/tools.yaml", "mcp", "--port", "5000"]
