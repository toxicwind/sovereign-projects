import os, asyncio, aiohttp, json, uuid, hashlib
from dataclasses import dataclass, field
from enum import Enum

class TransportType(str, Enum):
    REST = "rest"
    TRITON_GRPC = "triton-grpc"
    TRITON_GRPC_STREAM = "triton-grpc-stream"
    BLEEDING_TRITON = "bleeding-triton"

@dataclass
class LensProfile:
    name: str
    transport: TransportType
    persistent_conn: bool
    concurrency: int
    tps_target: int
    batch_size_min: int = 16
    batch_size_max: int = 32
    kv_block_size: int = 16
    enable_paged_attention: bool = True
    triton_url: str = field(default_factory=lambda: os.getenv("TRITON_GRPC_URL", "127.0.0.1:8001"))
    model_name: str = field(default_factory=lambda: os.getenv("TRITON_MODEL_NAME", "meta/llama-3.3-70b-instruct"))

    @classmethod
    def bleeding_triton(cls):
        return cls(name="bleeding-triton", transport=TransportType.BLEEDING_TRITON, persistent_conn=True, concurrency=128, tps_target=3500)
    @classmethod
    def balanced(cls):
        return cls(name="balanced-triton-grpc", transport=TransportType.TRITON_GRPC, persistent_conn=True, concurrency=64, tps_target=1800)
    @classmethod
    def baseline_rest(cls):
        return cls(name="baseline-rest", transport=TransportType.REST, persistent_conn=False, concurrency=8, tps_target=150, enable_paged_attention=False)

# --- This is the only part that works with your NVIDIA_API_KEY today ---
async def call_nvidia_rest(model: str, messages: list):
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    async with aiohttp.ClientSession() as sess:
        async with sess.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "max_tokens": 1024, "temperature": 0.2}
        ) as r:
            data = await r.json()
            return data["choices"][0]["message"]["content"]

if __name__ == "__main__":
    import sys
    print(asyncio.run(call_nvidia_rest(sys.argv[1] if len(sys.argv)>1 else "meta/llama-3.3-70b-instruct", [{"role":"user","content":"ping"}])))
