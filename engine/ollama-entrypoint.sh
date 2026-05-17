#!/bin/sh
# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready using ollama CLI
echo "Waiting for Ollama to start..."
until ollama list > /dev/null 2>&1; do
  sleep 2
done

echo "Ollama is ready. Pulling models..."

# Pull configured models with retries
for model in qwen3.5:9b qwen3-embedding:8b; do
  retries=3
  while [ $retries -gt 0 ]; do
    ollama pull "$model" && break
    echo "Pull failed for $model, retrying... ($retries attempts left)"
    retries=$((retries - 1))
    sleep 5
  done
done

echo "Models pulled successfully."

# Keep the container running
wait
