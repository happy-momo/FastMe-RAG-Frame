# 贡献指南 (Contributing to FastMe RAG)

首先，感谢您对 FastMe RAG 感兴趣！我们欢迎各种形式的贡献，包括代码提交、Bug 报告、功能建议、文档改进等。

## 📑 目录

- [行为准则](#行为准则)
- [我能贡献什么？](#我能贡献什么)
- [开发环境设置](#开发环境设置)
- [提交流程](#提交流程)
- [代码规范](#代码规范)
- [测试要求](#测试要求)
- [Pull Request 指南](#pull-request-指南)
- [常见问题](#常见问题)

## 行为准则

请尊重其他贡献者，保持友好和专业的交流氛围。

## 我能贡献什么？

### 1. 报告 Bug

如果您发现 Bug，请创建 Issue 并提供：
- 清晰的标题和描述
- 复现步骤
- 预期行为和实际行为
- 环境信息（Python 版本、OS 等）

### 2. 功能建议

欢迎提出新功能建议，请说明：
- 功能描述
- 使用场景
- 为什么需要这个功能

### 3. 提交代码

我们欢迎以下类型的代码贡献：
- Bug 修复
- 新功能实现
- 文档改进
- 测试用例
- 性能优化

## 开发环境设置

```bash
# 1. Fork 仓库
git fork https://github.com/happy-momo/FASTME-RAG

# 2. 克隆到本地
git clone https://github.com/YOUR_USERNAME/FASTME-RAG.git
cd FASTME-RAG

# 3. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 4. 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt

# 5. 运行测试
pytest tests/ -v
```

## 提交流程

### 1. 创建分支

```bash
# 同步主分支
git checkout main
git pull upstream main

# 创建功能分支
git checkout -b feat/your-feature-name
# 或修复分支
git checkout -b fix/bugfix-description
```

### 2. 进行修改

- 保持代码简洁、可读
- 添加必要的注释和文档字符串
- 编写测试用例

### 3. 运行测试

```bash
# 确保所有测试通过
pytest tests/ -v

# 检查代码风格（如配置了 flake8/black）
flake8 .
black .
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能描述"
# 或
git commit -m "fix: 修复某问题描述"
```

**提交信息规范**：
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具配置

### 5. 推送并创建 Pull Request

```bash
git push origin feat/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## 代码规范

### Python 风格

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 4 空格缩进
- 行宽限制 100 字符

### 文档字符串

所有公共类、函数、方法都应包含文档字符串：

```python
def chat(self, question: str, scene: str = "default") -> dict:
    """
    场景化问答

    Args:
        question (str): 用户问题
        scene (str, optional): 场景名称，默认 "default"

    Returns:
        dict: 包含 answer 和 sources 的字典

    Example:
        >>> result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
        >>> print(result["answer"])
    """
```

### 类型注解

鼓励使用类型注解：

```python
def ingest(self, file_path: str, doc_type: str) -> dict:
    ...
```

## 测试要求

- 新功能必须包含测试用例
- 所有现有测试必须通过
- 测试覆盖率不应下降（如配置了覆盖率检查）

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_scene_router.py -v

# 运行单个测试用例
pytest tests/test_scene_router.py::TestSceneRouter::test_route_exists -v
```

## Pull Request 指南

### PR 标题规范

```
feat: 添加新功能
fix: 修复某问题
docs: 更新文档
refactor: 重构代码
test: 添加测试
chore: 配置/工具更新
```

### PR 描述模板

```markdown
## 变更说明
简要描述此 PR 的变更内容

## 相关 Issue
关联的 Issue 编号（如有）

## 测试清单
- [ ] 已添加测试用例
- [ ] 所有测试通过
- [ ] 已更新文档

## 截图/示例（如适用）
```

## 常见问题

### Q: 如何开始第一个贡献？

**A:** 从简单的开始，如：
- 修复文档中的错别字
- 添加测试用例
- 改进注释和文档

查看 GitHub Issues 中标记为 `good first issue` 的问题。

### Q: 我的 PR 多久会被审核？

**A:** 通常在 1-3 个工作日内会有回复。请耐心等待。

### Q: 如何联系维护者？

**A:** 可以通过以下方式：
- GitHub Issues
- PR 评论
- Email: your-email@example.com

---

**再次感谢您的贡献！** 🎉
