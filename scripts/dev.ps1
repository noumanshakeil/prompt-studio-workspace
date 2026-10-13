# Dev server for prompt-studio-workspace
$env:LLM_MODE = "mock"
uvicorn backend.main:app --reload --port 8000
