uvicorn mock_vllm:app --port 8001
uvicorn demo_api_parallel:app --reload --port 8000
npm run dev