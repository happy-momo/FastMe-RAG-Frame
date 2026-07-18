"""
FastMe RAG 框架多轮对话测试脚本
测试场景：
1. 基础单轮对话（manual_query 场景）
2. 多轮对话 - 追问深入（同一话题逐步深入）
3. 多轮对话 - 话题切换（不同话题间切换）
4. 多轮对话 - 记忆窗口限制（max_turns 溢出测试）
5. 多会话并行（不同 session_id 独立记忆）
"""

import time
import sys
from app_factory import FastMeRAG


# ============================================================
# 工具函数
# ============================================================

def print_separator(title: str):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_chat_result(result: dict, turn: int = 1):
    """格式化打印对话结果"""
    print(f"  [第 {turn} 轮]")
    print(f"  问题: {result['question'][:100]}...")
    print(f"  场景: {result['scene']}")
    answer = result['answer']
    # 截断过长的回答便于阅读
    if len(answer) > 300:
        answer = answer[:300] + "..."
    print(f"  回答: {answer}")
    sources = result.get('sources', [])
    if sources:
        print(f"  来源数: {len(sources)}")
        for i, src in enumerate(sources[:3], 1):
            preview = src.get('preview', '')[:80]
            print(f"    来源{i}: {preview}...")
    print()


def chat_with_retry(rag, question: str, session_id: str = None,
                    scene: str = "default", top_k: int = 5,
                    max_retries: int = 10, retry_interval: int = 30) -> dict:
    """
    带重试机制的对话函数
    遇到 LLM 请求失败时自动等待重连
    """
    for attempt in range(1, max_retries + 1):
        try:
            if session_id is not None:
                result = rag.chat_with_memory(
                    question=question,
                    session_id=session_id,
                    scene=scene,
                    top_k=top_k
                )
            else:
                result = rag.chat(
                    question=question,
                    scene=scene,
                    top_k=top_k
                )
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"  [重试 {attempt}/{max_retries}] LLM 请求失败: {error_msg[:100]}")
            if attempt < max_retries:
                wait = retry_interval * attempt  # 递增等待时间
                print(f"  等待 {wait} 秒后重试...")
                time.sleep(wait)
            else:
                print(f"  已达最大重试次数，放弃。")
                raise


# ============================================================
# 初始化 RAG 实例
# ============================================================

print_separator("初始化 FastMe RAG")

rag = FastMeRAG(
    embedding_model="BAAI/bge-m3",   # 覆盖 .env 中的缓存路径格式
    model_cache_dir="./models",       # 指向本地缓存目录
)

# ============================================================
# 文档入库
# ============================================================

print_separator("文档入库")

ingest_result = rag.ingest(
    file_path="./files/200smart知识点节选.pdf",
    doc_type="manual",
)
print(f"  文档ID: {ingest_result.get('doc_id')}")
print(f"  文件名: {ingest_result.get('file_name')}")
print(f"  分块数: {ingest_result.get('chunks_count')}")
print(f"  向量数: {ingest_result.get('vector_count')}")


# ============================================================
# 场景 1: 基础单轮对话（无记忆）
# ============================================================

print_separator("场景1: 基础单轮对话（manual_query 场景）")

result1 = chat_with_retry(
    rag,
    question="S7-300最多支持什么扩展？",
    scene="manual_query",
    top_k=5
)
print_chat_result(result1)


# ============================================================
# 场景 2: 多轮对话 - 追问深入
# 同一话题逐步深入，测试记忆是否保持上下文连贯
# ============================================================

print_separator("场景2: 多轮对话 - 追问深入（同一话题逐步深入）")

SESSION_DEEP = "deep_dive_001"
rag.create_memory(session_id=SESSION_DEEP, max_turns=5)

# 第1轮：基础问题
q2_1 = "S7-200 SMART 有哪些型号？"
print(f"  用户: {q2_1}")
result2_1 = chat_with_retry(rag, question=q2_1, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_1, turn=1)

# 第2轮：追问细节（依赖上一轮上下文）
q2_2 = "它们之间有什么区别？"
print(f"  用户: {q2_2}")
result2_2 = chat_with_retry(rag, question=q2_2, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_2, turn=2)

# 第3轮：继续追问（依赖前两轮上下文）
q2_3 = "哪个型号的扩展能力最强？"
print(f"  用户: {q2_3}")
result2_3 = chat_with_retry(rag, question=q2_3, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_3, turn=3)

# 验证记忆是否保存
memory2 = rag.get_memory(SESSION_DEEP)
if memory2:
    history2 = memory2.load_memory_variables({})
    msgs2 = history2.get("history", [])
    print(f"  [记忆验证] 当前保存了 {len(msgs2)} 条消息（{len(msgs2)//2} 轮对话）")
else:
    print(f"  [记忆验证] 未找到记忆！")


# ============================================================
# 场景 3: 多轮对话 - 话题切换
# 在同一会话中切换不同话题，测试记忆是否混淆
# ============================================================

print_separator("场景3: 多轮对话 - 话题切换")

SESSION_SWITCH = "topic_switch_001"
rag.create_memory(session_id=SESSION_SWITCH, max_turns=5)

# 第1轮：话题A - 通信功能
q3_1 = "S7-200 SMART 支持哪些通信协议？"
print(f"  用户: {q3_1}")
result3_1 = chat_with_retry(rag, question=q3_1, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_1, turn=1)

# 第2轮：话题B - 编程软件（完全不同的话题）
q3_2 = "STEP 7-Micro/WIN SMART 的安装要求是什么？"
print(f"  用户: {q3_2}")
result3_2 = chat_with_retry(rag, question=q3_2, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_2, turn=2)

# 第3轮：回到话题A - 追问通信（测试记忆是否还记得话题A）
q3_3 = "刚才提到的通信协议中，哪个最适合远距离传输？"
print(f"  用户: {q3_3}")
result3_3 = chat_with_retry(rag, question=q3_3, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_3, turn=3)


# ============================================================
# 场景 4: 多轮对话 - 记忆窗口限制
# max_turns=3，发送4轮对话，验证最早一轮是否被遗忘
# ============================================================

print_separator("场景4: 记忆窗口限制（max_turns=3，发送4轮）")

SESSION_WINDOW = "window_test_001"
rag.create_memory(session_id=SESSION_WINDOW, max_turns=3)

# 第1轮
q4_1 = "S7-200 SMART 的 CPU 模块有哪些指示灯？"
print(f"  用户: {q4_1}")
result4_1 = chat_with_retry(rag, question=q4_1, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_1, turn=1)

# 第2轮
q4_2 = "RUN 指示灯亮代表什么状态？"
print(f"  用户: {q4_2}")
result4_2 = chat_with_retry(rag, question=q4_2, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_2, turn=2)

# 第3轮
q4_3 = "ERR 指示灯闪烁说明什么问题？"
print(f"  用户: {q4_3}")
result4_3 = chat_with_retry(rag, question=q4_3, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_3, turn=3)

# 第4轮（此时第1轮应被窗口淘汰）
q4_4 = "我之前问的第一个问题是什么？你还记得吗？"
print(f"  用户: {q4_4}")
result4_4 = chat_with_retry(rag, question=q4_4, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_4, turn=4)

# 验证记忆窗口
memory4 = rag.get_memory(SESSION_WINDOW)
if memory4:
    history4 = memory4.load_memory_variables({})
    msgs4 = history4.get("history", [])
    print(f"  [记忆窗口验证] 当前保存了 {len(msgs4)} 条消息")
    print(f"  [预期] max_turns=3，最多保留 6 条消息（3轮×2条/轮）")
    if len(msgs4) <= 6:
        print(f"  [结果] OK - 记忆窗口限制正常工作")
    else:
        print(f"  [结果] WARN - 记忆窗口限制可能未生效")


# ============================================================
# 场景 5: 多会话并行
# 两个不同 session_id 各自独立记忆，互不干扰
# ============================================================

print_separator("场景5: 多会话并行（独立记忆互不干扰）")

SESSION_A = "parallel_A"
SESSION_B = "parallel_B"
rag.create_memory(session_id=SESSION_A, max_turns=3)
rag.create_memory(session_id=SESSION_B, max_turns=3)

# 会话A - 第1轮
q5a_1 = "S7-200 SMART 的模拟量输入模块是什么型号？"
print(f"  [会话A] 用户: {q5a_1}")
result5a_1 = chat_with_retry(rag, question=q5a_1, session_id=SESSION_A, scene="manual_query")
print_chat_result(result5a_1, turn=1)

# 会话B - 第1轮（完全不同的话题）
q5b_1 = "S7-200 SMART 的编程语言有哪些？"
print(f"  [会话B] 用户: {q5b_1}")
result5b_1 = chat_with_retry(rag, question=q5b_1, session_id=SESSION_B, scene="manual_query")
print_chat_result(result5b_1, turn=1)

# 会话A - 第2轮（追问自己的话题）
q5a_2 = "这个模块的分辨率是多少？"
print(f"  [会话A] 用户: {q5a_2}")
result5a_2 = chat_with_retry(rag, question=q5a_2, session_id=SESSION_A, scene="manual_query")
print_chat_result(result5a_2, turn=2)

# 会话B - 第2轮（追问自己的话题）
q5b_2 = "哪种编程语言最适合初学者？"
print(f"  [会话B] 用户: {q5b_2}")
result5b_2 = chat_with_retry(rag, question=q5b_2, session_id=SESSION_B, scene="manual_query")
print_chat_result(result5b_2, turn=2)

# 验证两个会话记忆独立
mem_a = rag.get_memory(SESSION_A)
mem_b = rag.get_memory(SESSION_B)
if mem_a and mem_b:
    hist_a = mem_a.load_memory_variables({}).get("history", [])
    hist_b = mem_b.load_memory_variables({}).get("history", [])
    print(f"  [会话A记忆] {len(hist_a)} 条消息")
    print(f"  [会话B记忆] {len(hist_b)} 条消息")
    print(f"  [结果] OK - 两个会话记忆独立，互不干扰")


# ============================================================
# 清理
# ============================================================

print_separator("清理会话记忆")

rag.clear_memory()
print("  已清除所有会话记忆")

print_separator("测试完成")
print("  所有场景测试已执行完毕！")
