import argparse
import time

import torch
from llama import Llama

parser = argparse.ArgumentParser()
parser.add_argument("--cpu_bind", type=int, default=None)
parser.add_argument("--mem_bind", type=int, default=None)
parser.add_argument("--description", type=str, default="")
args = parser.parse_args()

ckpt_dir = "benchmark/llm_bench/models/meta-llama/Meta-Llama-3-8B"
tokenizer_path = "benchmark/llm_bench/models/meta-llama/Meta-Llama-3-8B/tokenizer.model"
max_seq_len = 128
max_batch_size = 1

generator = Llama.build(
    ckpt_dir=ckpt_dir,
    tokenizer_path=tokenizer_path,
    max_seq_len=max_seq_len,
    max_batch_size=max_batch_size,
    model_parallel_size=1,
)
device = torch.device("cpu")
generator.model.to(device)

with open("benchmark/llm_bench/datasets/wiki.test.raw", "r", encoding="utf-8") as file:
    test_data = file.read()

tokenizer = generator.tokenizer
tokens = tokenizer.encode(test_data, bos=True, eos=True)
chunks = [tokens[i : i + max_seq_len] for i in range(0, len(tokens), max_seq_len)]

record_latency = True
latencies = []
tokens_per_second = []
index = 0
for chunk in chunks:
    input_ids = torch.tensor(chunk).unsqueeze(0).to(device)
    start_time = time.time()
    with torch.no_grad():
        outputs = generator.model(input_ids, start_pos=0)
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    latencies.append(latency)
    generated_tokens = outputs.shape[1]
    tokens_per_second.append(generated_tokens / (latency / 1000))
    average_tokens_per_second = sum(tokens_per_second) / len(tokens_per_second)
#    print(f"Average tokens per second: {average_tokens_per_second}")
#    index += 1
#    if index > 50:
#        break

average_latency = sum(latencies) / len(latencies)

if record_latency:
    average_latency = sum(latencies) / len(latencies)
    output_file = "latency_results.txt"
    with open(output_file, "a") as f:
        f.write(
            f"Configuration: CPU bind={args.cpu_bind}, "
            f"Memory bind={args.mem_bind}, "
            f"Description={args.description}\n"
        )
        for i, latency in enumerate(latencies):
            f.write(f"Token {i} Latency: {latency:.2f} ms\n")
        f.write(f"Average Latency per Chunk: {average_latency:.2f} ms\n")
    print(f"Results written to {output_file}")
