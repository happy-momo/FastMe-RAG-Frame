"""
FastMe RAG 流式输出使用示例

流式输出的优势：
- 首字更快：不需要等待完整回答，立即看到内容
- 体验更好：类似 ChatGPT 的打字机效果
- 内存更省：不需要缓存完整回答
"""

from app_factory import FastMeRAG
import sys

# 初始化 RAG
rag = FastMeRAG(
    chunk_max_size=1000,
    ingest_batch_size=32,
    embedding_batch_size=32,
    show_progress_bar=False  # 建议关闭，避免干扰流式输出
)

# ==============================================================================
# 方式 1: 基础流式输出
# ==============================================================================
print("=" * 60)
print("方式 1: 基础流式输出")
print("=" * 60)

print("\n用户问题：如何使用流式输出？\n")
print("AI 回答：", end="", flush=True)

for chunk in rag.chat_stream(
    question="如何使用流式输出？",
    scene="manual_query"
):
    print(chunk, end="", flush=True)

print("\n")


# ==============================================================================
# 方式 2: 带场景的流式输出
# ==============================================================================
print("=" * 60)
print("方式 2: 带场景的流式输出")
print("=" * 60)

print("\n用户问题：设备报警怎么处理？ (scene=fault_diagnosis)\n")
print("AI 回答：", end="", flush=True)

for chunk in rag.chat_stream(
    question="设备报警怎么处理？",
    scene="fault_diagnosis"
):
    print(chunk, end="", flush=True)

print("\n")


# ==============================================================================
# 方式 3: 带过滤条件的流式输出
# ==============================================================================
print("=" * 60)
print("方式 3: 带过滤条件的流式输出")
print("=" * 60)

print("\n用户问题：E001 设备有哪些故障？ (带设备过滤)\n")
print("AI 回答：", end="", flush=True)

for chunk in rag.chat_stream(
    question="E001 设备有哪些故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}  # 过滤条件
):
    print(chunk, end="", flush=True)

print("\n")


# ==============================================================================
# 方式 4: 对比普通 chat 和 chat_stream
# ==============================================================================
print("=" * 60)
print("方式 4: 对比普通 chat 和 chat_stream")
print("=" * 60)

# 普通 chat - 等待完整回答
print("\n[普通 chat] 等待完整回答...")
result = rag.chat(question="什么是 RAG？", scene="default")
print(f"完整回答长度：{len(result['answer'])} 字符")
print(f"溯源数量：{len(result.get('sources', []))}")

# 流式 chat - 逐字输出
print("\n[chat_stream] 逐字输出...")
print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(question="什么是 RAG？", scene="default"):
    print(chunk, end="", flush=True)
print()


# ==============================================================================
# 方式 5: 在 Web 应用中使用（Flask 示例）
# ==============================================================================
"""
在 Flask 中使用流式输出：

from flask import Flask, Response, stream_with_context

app = Flask(__name__)
rag = FastMeRAG()

@app.route('/chat', methods=['POST'])
def chat():
    question = request.json.get('question')

    def generate():
        for chunk in rag.chat_stream(question, scene="default"):
            yield f"data: {chunk}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )

# 前端使用 EventSource 接收
"""

print("\n" + "=" * 60)
print("流式输出使用示例完成!")
print("=" * 60)
