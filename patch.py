import re

with open("docker-compose.prod.yml", "r") as f:
    content = f.read()

# Remove vllm-server block
content = re.sub(r'  # --- THÊM MỚI: vLLM SERVER ---.*?shm_size: .8gb. # vLLM requires large shared memory\n', '', content, flags=re.DOTALL)

# Change Kong ports
content = content.replace('- "80:8000"     # Map Kong to port 80 for production access', '- "8080:8000"   # Map Kong to 8080 to avoid clashing with Host vLLM on 8000')

# Remove vllm-server depends_on
content = content.replace('      - vllm-server\n', '')

with open("docker-compose.prod.yml", "w") as f:
    f.write(content)
