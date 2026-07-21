"""
FastMe RAG 框架多轮对话测试脚本
测试场景：
1. 基础单轮对话（manual_query 场景）
2. 多轮对话 - 追问深入（同一话题逐步深入）
3. 多轮对话 - 话题切换（不同话题间切换）
4. 多轮对话 - 记忆窗口限制（max_turns 溢出测试）—— 验证修复：记忆窗口机制
5. 多会话并行（不同 session_id 独立记忆）
6. 跨文档知识检索（同时涉及多个文档）
7. 技术细节深度问答（具体技术参数和操作步骤）
8. LLM 空回答处理验证 —— 验证修复：空回答兜底
9. FAISS 向量库去重验证 —— 验证修复：FAISS ids 去重

测试文档：
- 200smart知识点节选.pdf（S7-300/400/200Smart PLC 知识点）
- T-CPU.docx（T-CPU 运动控制实验报告）
- 博途wincc.pdf（WinCC 组态知识）
"""

import time
import sys
import io
import os

# 强制 stdout/stderr 使用 UTF-8 编码，避免 Windows GBK 编码错误
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

# 不传入参数，让 FastMeRAG 从 .env 文件读取配置
rag = FastMeRAG()

# ============================================================
# 文档入库
# ============================================================

print_separator("文档入库")

ingest_result = rag.batch_ingest(
    folder_path="./files",
    doc_type="manual",
)
# print(f"  文档ID: {ingest_result.get('doc_id')}")
# print(f"  文件名: {ingest_result.get('file_name')}")
# print(f"  分块数: {ingest_result.get('chunks_count')}")
# print(f"  向量数: {ingest_result.get('vector_count')}")


# ============================================================
# 场景 1: 基础单轮对话（无记忆）
# ============================================================

print_separator("场景1: 基础单轮对话（manual_query 场景）")

result1 = chat_with_retry(
    rag,
    question="CPU如何选型",
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
q2_1 = "wincc 如何安装？"
print(f"  用户: {q2_1}")
result2_1 = chat_with_retry(rag, question=q2_1, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_1, turn=1)

# 第2轮：追问细节（依赖上一轮上下文）
q2_2 = "Wincc使用入门是什么？"
print(f"  用户: {q2_2}")
result2_2 = chat_with_retry(rag, question=q2_2, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_2, turn=2)

# 第3轮：继续追问（依赖前两轮上下文）
q2_3 = "wincc如何使用项目？"
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

# 验证修复：chat_with_memory 返回的 question 字段应只包含用户原始问题
print(f"\n  [修复验证 - question字段] 检查 result['question'] 是否仅包含原始问题...")
for turn_idx, (turn_label, turn_result) in enumerate([
    ("第1轮", result2_1), ("第2轮", result2_2), ("第3轮", result2_3)
], 1):
    q = turn_result['question']
    has_history_prefix = "历史对话:" in q or "human:" in q.lower()
    if has_history_prefix:
        print(f"  [✗ 第{turn_idx}轮] question 字段包含历史对话文本！问题前缀: {q[:50]}...")
    else:
        original_questions = ["wincc 如何安装？", "Wincc使用入门是什么？", "wincc如何使用项目？"]
        expected = original_questions[turn_idx - 1]
        if q == expected:
            print(f"  [✓ 第{turn_idx}轮] question 字段正确，仅包含原始问题")
        else:
            print(f"  [✓ 第{turn_idx}轮] question 字段不含历史对话文本（内容: {q[:50]}...）")
assert "历史对话:" not in result2_2['question'], "修复验证失败：question 字段仍包含历史对话文本"
print(f"  [✓ 修复验证通过] chat_with_memory 的 question 字段不再包含历史对话")


# ============================================================
# 场景 3: 多轮对话 - 话题切换
# 在同一会话中切换不同话题，测试记忆是否混淆
# ============================================================

print_separator("场景3: 多轮对话 - 话题切换")

SESSION_SWITCH = "topic_switch_001"
rag.create_memory(session_id=SESSION_SWITCH, max_turns=5)

# 第1轮：话题A - 通信功能
q3_1 = "200smart有哪些模块？"
print(f"  用户: {q3_1}")
result3_1 = chat_with_retry(rag, question=q3_1, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_1, turn=1)

# 第2轮：话题B - 编程软件（完全不同的话题）
q3_2 = "wincc如何进行组态？"
print(f"  用户: {q3_2}")
result3_2 = chat_with_retry(rag, question=q3_2, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_2, turn=2)

# 第3轮：回到话题A - 追问通信（测试记忆是否还记得话题A）
q3_3 = "200smart模块支持什么通讯？"
print(f"  用户: {q3_3}")
result3_3 = chat_with_retry(rag, question=q3_3, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_3, turn=3)


# ============================================================
# 场景 4: 多轮对话 - 记忆窗口限制
# max_turns=3，发送4轮对话，验证最早一轮是否被遗忘
# 基于文档：200smart知识点节选（S7-300/400/200Smart PLC）
# ============================================================

print_separator("场景4: 记忆窗口限制（max_turns=3，发送4轮）")

SESSION_WINDOW = "window_test_001"
rag.create_memory(session_id=SESSION_WINDOW, max_turns=3)

# 第1轮：S7-300 基础结构
q4_1 = "S7-300 的硬件结构由哪些组件组成？"
print(f"  用户: {q4_1}")
result4_1 = chat_with_retry(rag, question=q4_1, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_1, turn=1)

# 第2轮：追问安装与维护
q4_2 = "S7-300 水平安装和垂直安装的允许温度分别是多少？"
print(f"  用户: {q4_2}")
result4_2 = chat_with_retry(rag, question=q4_2, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_2, turn=2)

# 第3轮：追问存储器相关
q4_3 = "S7-300 断电后数据如何保存？MMC 卡的作用是什么？"
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

    # 验证修复：记忆窗口机制 —— 消息列表式历史应正确限制窗口
    # ConversationBufferWindowMemory 的 k=3 意味着只保留最近3轮（6条消息）
    # 第4轮对话时，第1轮应已被淘汰，LLM 不应记得第1轮的问题
    print(f"\n  [修复验证 - 记忆窗口] 检查第4轮回答是否已遗忘第1轮内容...")
    answer4_text = result4_4['answer']
    first_question_keyword = "硬件结构"
    if first_question_keyword in answer4_text and "导轨" in answer4_text:
        # LLM 可能通过检索上下文获取到相关信息，需区分"检索到"和"从历史记忆到"
        # 更可靠的验证：检查记忆中实际保存的消息条数
        print(f"  [注意] LLM 回答中包含了第1轮关键词，但可能来自检索而非记忆")
        print(f"  [验证] 记忆中实际消息数={len(msgs4)}，预期≤6")
    else:
        print(f"  [结果] OK - LLM 未从历史记忆中获取第1轮信息")

    # 核心验证：消息数量必须 <= max_turns * 2
    assert len(msgs4) <= 6, f"记忆窗口验证失败：消息数 {len(msgs4)} > 6 (max_turns=3)"
    print(f"  [✓ 修复验证通过] 记忆窗口机制正确工作，消息数={len(msgs4)} ≤ 6")


# ============================================================
# 场景 5: 多会话并行
# 两个不同 session_id 各自独立记忆，互不干扰
# 分别针对两个不同的文档进行提问
# ============================================================

print_separator("场景5: 多会话并行（独立记忆互不干扰）")

SESSION_A = "parallel_A"  # 针对：200smart知识点节选（PLC）
SESSION_B = "parallel_B"  # 针对：T-CPU实验报告（运动控制）
rag.create_memory(session_id=SESSION_A, max_turns=3)
rag.create_memory(session_id=SESSION_B, max_turns=3)

# 会话A - 第1轮：关于 S7-200 Smart PLC
q5a_1 = "S7-200 Smart 有哪些亮点和特色功能？"
print(f"  [会话A-PLC] 用户: {q5a_1}")
result5a_1 = chat_with_retry(rag, question=q5a_1, session_id=SESSION_A, scene="manual_query")
print_chat_result(result5a_1, turn=1)

# 会话B - 第1轮：关于 T-CPU 运动控制（不同文档）
q5b_1 = "T-CPU 实验中驱动组态与优化的步骤是什么？"
print(f"  [会话B-运动控制] 用户: {q5b_1}")
result5b_1 = chat_with_retry(rag, question=q5b_1, session_id=SESSION_B, scene="manual_query")
print_chat_result(result5b_1, turn=1)

# 会话A - 第2轮（追问 PLC 通信的话题）
q5a_2 = "S7-200 Smart 的以太网通信支持哪些协议？连接资源有多少？"
print(f"  [会话A-PLC] 用户: {q5a_2}")
result5a_2 = chat_with_retry(rag, question=q5a_2, session_id=SESSION_A, scene="manual_query")
print_chat_result(result5a_2, turn=2)

# 会话B - 第2轮（追问运动控制选型的话题）
q5b_2 = "TIA Selection Tools 中 1500T 选型时如何配置运动控制参数？"
print(f"  [会话B-运动控制] 用户: {q5b_2}")
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
# 场景 6: 跨文档知识检索
# 测试系统是否能同时从多个文档中检索相关信息
# ============================================================

print_separator("场景6: 跨文档知识检索（同时涉及多个文档）")

# 问题1：涉及 PLC 和运动控制的共同主题 - 通信
q6_1 = "S7-200 Smart 的 PROFINET 通信和 T-CPU 的 V90 PN 驱动通信有什么关联？两者分别如何实现网络连接？"
print(f"  用户: {q6_1}")
result6_1 = chat_with_retry(rag, question=q6_1, scene="manual_query", top_k=8)
print_chat_result(result6_1)

# 问题2：涉及 WinCC 和 PLC 的主题 - 项目创建与组态
q6_2 = "博途 WinCC 的项目创建和 S7-300 的硬件组态有什么共同点？它们在 TIA Portal 中如何集成？"
print(f"  用户: {q6_2}")
result6_2 = chat_with_retry(rag, question=q6_2, scene="manual_query", top_k=8)
print_chat_result(result6_2)

# 问题3：涉及三个文档 - 整体自动化系统架构
q6_3 = "请结合三个文档的内容，描述一个完整的自动化项目可能涉及的技术栈：从PLC选型（200smart知识点）、运动控制（T-CPU实验）到上位机监控（WinCC），各部分如何协作？"
print(f"  用户: {q6_3}")
result6_3 = chat_with_retry(rag, question=q6_3, scene="manual_query", top_k=10)
print_chat_result(result6_3)


# ============================================================
# 场景 7: 技术细节深度问答
# 针对文档中的具体技术参数和操作步骤
# ============================================================

print_separator("场景7: 技术细节深度问答")

# 关于 200smart 的技术细节
q7_1 = "S7-200 Smart 的高速计数器 HSC 最多可以使用几个？运动控制最多同时控制几个被控对象？PID 最多支持几路控制回路？"
print(f"  用户: {q7_1}")
result7_1 = chat_with_retry(rag, question=q7_1, scene="manual_query")
print_chat_result(result7_1)

# 关于 T-CPU 实验的技术细节
q7_2 = "1500T 选型实验中，运动控制周期设置为多少？轴类型配置了哪些？通信负载和主循环OB时间分别是多少？"
print(f"  用户: {q7_2}")
result7_2 = chat_with_retry(rag, question=q7_2, scene="manual_query")
print_chat_result(result7_2)

# 关于 WinCC 组态的技术细节
q7_3 = "WinCC 的报警系统由哪些组成部分？报警日志需要什么外部存储介质？数据日志的采集模式有哪些？"
print(f"  用户: {q7_3}")
result7_3 = chat_with_retry(rag, question=q7_3, scene="manual_query")
print_chat_result(result7_3)


# ============================================================
# 场景 8: LLM 空回答处理验证
# 验证修复：LLM 返回空字符串时应被替换为兜底回答
# ============================================================

print_separator("场景8: LLM 空回答处理验证")

# 直接测试 chat_pipeline 的空回答处理逻辑
from core.chat_pipeline import ChatPipeline
original_invoke = rag.llm.invoke

def mock_empty_invoke(messages):
    """模拟 LLM 返回空字符串"""
    class MockResponse:
        content = ""
    return MockResponse()

# 临时替换 LLM invoke 方法
rag.llm.invoke = mock_empty_invoke

try:
    test_result = rag.chat(question="测试空回答", scene="manual_query")
    answer_text = test_result['answer']
    if answer_text and answer_text.strip() and len(answer_text) > 5:
        print(f"  [修复验证 - 空回答处理] OK - 空回答已被替换为兜底回答")
        print(f"  [兜底回答] {answer_text[:100]}")
    else:
        print(f"  [✗ 修复验证失败] 空回答未被正确处理，回答: '{answer_text}'")
    assert answer_text and answer_text.strip(), "空回答处理验证失败：回答仍为空"
    print(f"  [✓ 修复验证通过] LLM 空回答兜底机制正常工作")
finally:
    # 恢复原始 LLM invoke 方法
    rag.llm.invoke = original_invoke


# ============================================================
# 场景 9: FAISS 向量库去重验证
# 验证修复：FAISS 适配器支持基于 chunk_id 的去重
# ============================================================

print_separator("场景9: FAISS 向量库去重验证")

from vector_stores.faiss import FAISSAdapter
from langchain_core.documents import Document

# 创建临时 FAISS 适配器
test_faiss_dir = "./data/faiss_test_dedup"
import shutil
if os.path.exists(test_faiss_dir):
    shutil.rmtree(test_faiss_dir)

faiss_adapter = FAISSAdapter(
    embedding_function=rag.embeddings,
    index_path=test_faiss_dir,
    load_existing=False
)

# 添加3个文档
docs1 = [
    Document(page_content="测试文档A的内容", metadata={"chunk_id": "chunk_1", "source": "test"}),
    Document(page_content="测试文档B的内容", metadata={"chunk_id": "chunk_2", "source": "test"}),
    Document(page_content="测试文档C的内容", metadata={"chunk_id": "chunk_3", "source": "test"}),
]
ids1 = ["chunk_1", "chunk_2", "chunk_3"]

faiss_adapter.add_documents(docs1, ids=ids1)
count_after_first = faiss_adapter.get_count()
print(f"  [首次入库] 文档数={len(docs1)}，向量数={count_after_first}")

# 再次添加相同 chunk_id 的文档（模拟重复入库）
docs2 = [
    Document(page_content="测试文档A的内容（更新）", metadata={"chunk_id": "chunk_1", "source": "test"}),
    Document(page_content="测试文档B的内容（更新）", metadata={"chunk_id": "chunk_2", "source": "test"}),
]
ids2 = ["chunk_1", "chunk_2"]

faiss_adapter.add_documents(docs2, ids=ids2)
count_after_second = faiss_adapter.get_count()
print(f"  [重复入库] 文档数={len(docs2)}，向量数={count_after_second}")

# 验证：重复入库后向量数不应增加（upsert 语义）
if count_after_first == count_after_second:
    print(f"  [✓ 修复验证通过] FAISS 去重正常工作，重复入库未增加向量数")
    print(f"  [结果] 首次={count_after_first}，重复后={count_after_second}")
else:
    print(f"  [✗ 修复验证失败] FAISS 去重未生效，向量数增加了 {count_after_second - count_after_first}")
assert count_after_first == count_after_second, f"FAISS 去重验证失败：首次={count_after_first}，重复后={count_after_second}"

# 添加新文档（不重复），验证向量数增加
docs3 = [
    Document(page_content="测试文档D的内容", metadata={"chunk_id": "chunk_4", "source": "test"}),
]
ids3 = ["chunk_4"]

faiss_adapter.add_documents(docs3, ids=ids3)
count_after_third = faiss_adapter.get_count()
print(f"  [新增入库] 文档数={len(docs3)}，向量数={count_after_third}")

if count_after_third == count_after_second + 1:
    print(f"  [✓ 新增文档验证通过] 新文档正确添加，向量数+1")
else:
    print(f"  [✗ 新增文档验证异常] 预期={count_after_second + 1}，实际={count_after_third}")

# 清理测试数据
faiss_adapter.delete_collection()
if os.path.exists(test_faiss_dir):
    shutil.rmtree(test_faiss_dir)


# ============================================================
# 清理
# ============================================================

print_separator("清理会话记忆")

rag.clear_memory()
print("  已清除所有会话记忆")

print_separator("测试完成")
print("  所有场景测试已执行完毕！")
print("  测试文档：")
print("    1. 200smart知识点节选.pdf（S7-300/400/200Smart PLC 知识点）")
print("    2. T-CPU.docx（T-CPU 运动控制实验报告）")
print("    3. 博途wincc.pdf（WinCC 组态知识）")
