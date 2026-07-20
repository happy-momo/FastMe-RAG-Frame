"""
FastMe RAG 场景化问答示例

演示 4 种预置场景的使用方法：
- fault_diagnosis: 故障诊断
- manual_query: 设备手册查询
- work_order_trace: 工单追溯
- default: 默认问答
"""

from app_factory import FastMeRAG

rag = FastMeRAG()

print("=" * 60)
print("FastMe RAG 场景化问答示例")
print("=" * 60)

# ========== 场景 1: 故障诊断 (fault_diagnosis) ==========
print("\n【场景 1】故障诊断 - 基于运维日志和故障记录")
print("-" * 60)

# 假设已入库故障日志
# rag.ingest("故障日志.log", doc_type="log")

result = rag.chat(
    question="E001 设备常见故障有哪些？如何处理？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

print(f"问题：{result['question']}")
print(f"场景：{result['scene']}")
print(f"答案：{result['answer']}")
print(f"溯源字段：device_id, line_id, fault_code, timestamp")

# ========== 场景 2: 设备手册查询 (manual_query) ==========
print("\n【场景 2】设备手册查询 - 操作步骤和技术参数")
print("-" * 60)

# 假设已入库设备手册
# rag.ingest("设备操作手册.pdf", doc_type="manual")

result = rag.chat(
    question="如何更换设备的润滑油？具体步骤是什么？",
    scene="manual_query"
)

print(f"问题：{result['question']}")
print(f"场景：{result['scene']}")
print(f"答案：{result['answer']}")
print(f"溯源字段：source, file_path, chapter_num, device_model")

# ========== 场景 3: 工单追溯 (work_order_trace) ==========
print("\n【场景 3】工单追溯 - 生产记录和质检信息")
print("-" * 60)

# 假设已入库工单
# rag.ingest("工单记录.xlsx", doc_type="business")

result = rag.chat(
    question="工单 WO-2024001 的质检结果如何？",
    scene="work_order_trace",
    filters={"work_order_id": "WO-2024001"}
)

print(f"问题：{result['question']}")
print(f"场景：{result['scene']}")
print(f"答案：{result['answer']}")
print(f"溯源字段：work_order_id, material_id, quality_result")

# ========== 场景 4: 默认问答 (default) ==========
print("\n【场景 4】默认问答 - 通用知识查询")
print("-" * 60)

result = rag.chat(
    question="什么是预防性维护？",
    scene="default"
)

print(f"问题：{result['question']}")
print(f"场景：{result['scene']}")
print(f"答案：{result['answer']}")
print(f"溯源字段：source, doc_type")

# ========== 对比：带过滤 vs 不带过滤 ==========
print("\n【对比】带过滤条件 vs 不带过滤条件")
print("-" * 60)

# 不带过滤 - 查询所有设备的故障
result_all = rag.chat(
    question="有哪些故障记录？",
    scene="fault_diagnosis"
)
print(f"不带过滤 - 溯源数量：{len(result_all['sources'])}")

# 带过滤 - 只查询特定设备的故障
result_filtered = rag.chat(
    question="有哪些故障记录？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)
print(f"带过滤 (device_id=EQ001) - 溯源数量：{len(result_filtered['sources'])}")

# ========== 自定义 top_k ==========
print("\n【高级】自定义召回数量")
print("-" * 60)

result = rag.chat(
    question="设备故障处理方法",
    scene="fault_diagnosis",
    top_k=10  # 召回 10 条
)
print(f"top_k=10 - 溯源数量：{len(result['sources'])}")

result = rag.chat(
    question="设备故障处理方法",
    scene="fault_diagnosis",
    top_k=3  # 召回 3 条
)
print(f"top_k=3 - 溯源数量：{len(result['sources'])}")
