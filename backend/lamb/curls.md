# test lamb assistant no streaming

curl -X POST 'http://localhost:9099/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer 0p3n-w3bu!' \
-d '{
  "model": "LAMB:t1",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ],
  "stream": false
}'

## same test but to openai gpt-4o

curl -X POST 'https://api.openai.com/v1/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer ' \
-d '{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ],
  "stream": false
}'


# test lamb assistant streaming

curl -X POST 'http://localhost:9099/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer 0p3n-w3bu!' \
-d '{
  "model": "LAMB Assistant:test assistant 1",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ],
  "stream": true
}'


### test with prompt

curl -X POST 'http://localhost:9099/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer 0p3n-w3bu!' \
  -d '{
    "model": "LAMB Assistant:test assistant 1",
    "prompt": ["hi"],
    "stream": false
  }'


## test litellm no streaming

curl -X POST 'http://localhost:4000/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer 0p3n-w3bu!' \
-d '{
  "model": "LAMB Assistant:test assistant 1",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ],
  "stream": false
}'


## test litellm streaming

curl -X POST 'http://localhost:4000/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer 0p3n-w3bu!' \
-d '{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ],
  "stream": false
}'
