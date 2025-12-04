# GPU Dynamic Batching Alternatives

## The Problem

**Ollama Limitation**: Does not support dynamic batching on GPU. Each request is processed individually, which is inefficient for GPU utilization.

**What is Dynamic Batching?**
- Collecting multiple inference requests
- Processing them together in a single GPU batch
- Significantly improves GPU throughput (2-10x speedup)

---

## Alternative Solutions

### Option 1: vLLM (Recommended) ✅

**vLLM** is a high-performance inference engine with **continuous batching**.

#### Features
- ✅ **Continuous batching**: Dynamically batches requests
- ✅ **PagedAttention**: Efficient memory management
- ✅ **High throughput**: 10-20x faster than naive implementations
- ✅ **OpenAI-compatible API**: Easy integration
- ✅ **Supports many models**: Llama, Mistral, CodeLlama, Qwen, etc.

#### Installation

```bash
pip install vllm
```

#### Usage

**Start vLLM server**:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-7B-Instruct \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
```

**Or with specific settings**:
```bash
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \
    --max-model-len 4096 \
    --max-num-seqs 256 \
    --gpu-memory-utilization 0.9
```

#### Integration

Replace Ollama with vLLM in the worker:

```python
# Instead of Ollama
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-7B-Instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**Benefits**:
- Automatic dynamic batching
- Much higher throughput
- Better GPU utilization
- OpenAI-compatible API

---

### Option 2: TGI (Text Generation Inference) ✅

**Hugging Face's TGI** supports dynamic batching.

#### Features
- ✅ Dynamic batching
- ✅ Tensor parallelism (multi-GPU)
- ✅ Flash Attention
- ✅ Continuous batching
- ✅ Docker-based deployment

#### Installation

```bash
# Using Docker
docker run --gpus all --shm-size 1g -p 8080:80 \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id Qwen/Qwen2.5-Coder-7B-Instruct \
    --max-batch-total-tokens 8192
```

#### Integration

```python
import requests

response = requests.post(
    "http://localhost:8080/generate",
    json={
        "inputs": "What is Python?",
        "parameters": {"max_new_tokens": 100}
    }
)
```

---

### Option 3: Ray Serve with Custom Batching ✅

Use **Ray Serve** with manual batching (already in your codebase!).

#### Features
- ✅ Built-in dynamic batching decorator
- ✅ Multi-GPU support
- ✅ Flexible deployment
- ✅ Already integrated in your project

#### Implementation

Your `ray_worker.py` already has this:

```python
@serve.batch(max_batch_size=32, batch_wait_timeout_s=0.1)
async def handle_batch(self, requests: List[Dict[str, Any]]):
    # Batch processing logic
    batch_tensor = torch.stack(batch_inputs).to(device)
    with torch.no_grad():
        batch_output = self.model(batch_tensor)
    return results
```

**Benefits**:
- Already in your codebase
- Flexible batching configuration
- Works with any PyTorch model
- Multi-GPU support

**Limitation**:
- Requires loading model with transformers/PyTorch
- More manual setup than vLLM

---

### Option 4: TensorRT-LLM ✅

**NVIDIA's TensorRT-LLM** for maximum performance.

#### Features
- ✅ Inflight batching
- ✅ Optimized for NVIDIA GPUs
- ✅ Highest performance
- ✅ Multi-GPU support

#### Installation

```bash
# Requires NVIDIA GPU and TensorRT
pip install tensorrt_llm
```

**Note**: More complex setup, best for production with NVIDIA GPUs.

---

### Option 5: Triton Inference Server ✅

**NVIDIA Triton** with dynamic batching.

#### Features
- ✅ Dynamic batching built-in
- ✅ Multi-framework support
- ✅ Production-ready
- ✅ Monitoring and metrics

#### Configuration

```python
# model_config.pbtxt
dynamic_batching {
  max_queue_delay_microseconds: 100
  preferred_batch_size: [4, 8, 16]
}
```

---

## Comparison Table

| Solution | Batching | Setup | Performance | GPU Support | API |
|----------|----------|-------|-------------|-------------|-----|
| **Ollama** | ❌ No | Easy | Low | Single | Custom |
| **vLLM** | ✅ Continuous | Easy | Very High | Multi | OpenAI |
| **TGI** | ✅ Dynamic | Medium | High | Multi | Custom |
| **Ray Serve** | ✅ Manual | Medium | High | Multi | Custom |
| **TensorRT-LLM** | ✅ Inflight | Hard | Highest | Multi | Custom |
| **Triton** | ✅ Dynamic | Hard | Very High | Multi | gRPC/HTTP |

---

## Recommended Solution: vLLM

For your use case, **vLLM** is the best choice:

### Why vLLM?

1. **Easy to use**: Similar to Ollama, but with batching
2. **High performance**: 10-20x faster than sequential processing
3. **OpenAI-compatible**: Easy integration
4. **Continuous batching**: Automatic optimization
5. **Good model support**: Works with Qwen2.5-Coder

### Migration Path

1. **Install vLLM**:
   ```bash
   pip install vllm
   ```

2. **Start vLLM server**:
   ```bash
   vllm serve Qwen/Qwen2.5-Coder-7B-Instruct \
       --host 0.0.0.0 \
       --port 8000
   ```

3. **Update worker** to use vLLM instead of Ollama

4. **Keep same API**: Your FastAPI endpoints don't change

---

## Performance Comparison

### Sequential (Ollama)
```
Request 1: ████████ 8s
Request 2:         ████████ 8s
Request 3:                 ████████ 8s
Total: 24s
```

### With Dynamic Batching (vLLM)
```
Batch [1,2,3]: ████████ 10s
Total: 10s (2.4x speedup!)
```

### With Multiple GPUs + Batching
```
GPU 1 Batch [1,2]: ████ 5s
GPU 2 Batch [3,4]: ████ 5s
Total: 5s (4.8x speedup!)
```

---

## Next Steps

### Quick Test with vLLM

1. **Install**:
   ```bash
   pip install vllm
   ```

2. **Start server**:
   ```bash
   vllm serve Qwen/Qwen2.5-Coder-7B-Instruct
   ```

3. **Test**:
   ```bash
   curl http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'
   ```

### Integration

I can create a vLLM worker that:
- Replaces Ollama
- Supports dynamic batching
- Uses OpenAI-compatible API
- Works with your existing FastAPI endpoints

Would you like me to create this?

---

## Summary

**Question**: Can demo_api_parallel.py do dynamic batching with Ollama?  
**Answer**: ❌ No, Ollama doesn't support batching

**Alternative**: ✅ Use **vLLM** for:
- Continuous dynamic batching
- 10-20x better throughput
- Easy migration from Ollama
- Same models (Qwen2.5-Coder, etc.)

**Best for your project**: vLLM + Ray Serve
- vLLM handles batching and inference
- Ray Serve handles distribution across GPUs
- Your API stays the same
