<div align="center" id="top">

# 📚 科研智能助手

**Scientific Research Assistant** — 面向科学论文的智能检索与深度研究系统

基于多数据源检索、论文去重排序、全文获取与综述生成，为科研人员提供一站式文献调研与报告撰写支持。

</div>

---

## 项目简介

本项目是一个**科研向的智能研究助手**，支持从学术数据库与开放获取渠道检索论文、去重排序、获取全文与摘要，并生成带引用的综述报告。系统采用「规划器 + 执行器」的多智能体架构：规划器分解研究问题并生成检索策略，执行器从多源并行抓取与解析，最终由出版器汇总成结构化报告。

**适用场景**：文献综述、开题调研、领域技术追踪、论文写作辅助。

## 核心能力

### 科学论文检索与管道

- **多数据源检索**：集成 arXiv、Semantic Scholar、OpenAlex、CrossRef、PubMed Central、CORE 等，支持按关键词、作者、年份筛选。
- **开放获取增强**：通过 Unpaywall 解析 DOI，优先获取 OA 全文链接，降低付费墙依赖。
- **论文管道**：检索 → 去重 → 排序 → 全文获取 → 解析（PDF/结构化元数据）→ 长文摘要 → 引用图分析，形成完整流水线。
- **领域适配**：内置通信/电信等领域查询规划与扩展策略，便于做定向文献调研。

### 通用研究能力

- 📝 基于网络与本地文档的深度研究报告生成。
- 📜 长篇幅报告（如 2000+ 字）与多源引用。
- 📄 导出 PDF、Word、Markdown 等格式。
- 🔍 可选的 JavaScript 网页抓取与 MCP 等扩展数据源。

## 系统架构

整体流程：**研究任务 → 规划器生成子问题 → 执行器多源检索与爬取 → 摘要与溯源 → 过滤与聚合 → 最终报告**。

- **规划器**：根据用户 query 生成一组子问题与检索策略（含学术源与通用检索）。
- **执行器**：调用各 Retriever（学术 API + 网页/自定义）并行获取内容。
- **出版器**：汇总、去重、排序后生成带引用的综述报告。

## 快速开始

### 环境要求

- Python 3.11+
- 所需 API：OpenAI（或兼容接口）、Tavily（可选，用于网页检索）等，见 `.env.example`。

### 安装与运行

1. 克隆本仓库并进入目录：

   ```bash
   git clone <你的仓库地址>
   cd gpt-researcher
   ```

2. 配置环境变量（或 `.env`）：

   ```bash
   export OPENAI_API_KEY=你的OpenAI密钥
   export TAVILY_API_KEY=你的Tavily密钥   # 可选，用于网页检索
   ```

3. 安装依赖并启动服务：

   ```bash
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

4. 浏览器访问 [http://localhost:8000](http://localhost:8000)。

### 科研模式与检索源

通过环境变量或配置指定使用的检索器，例如启用学术源与网页混合：

```bash
# 示例：学术检索源（可组合）
# 在配置或 academic_config 中指定 sources：arxiv, semantic_scholar, openalex, crossref, core 等
```

代码示例（异步）：

```python
from gpt_researcher import GPTResearcher

async def run():
    researcher = GPTResearcher(
        query="5G massive MIMO 最新研究进展",
        report_source="auto",  # 或 "local" 使用本地文档
    )
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    return report
```

## 项目结构（与科研相关的扩展）

- `gpt_researcher/retrievers/` — 检索器：`arxiv`、`semantic_scholar`、`openalex`、`crossref`、`unpaywall`、`pubmed_central`、`core` 等。
- `gpt_researcher/papers/` — 论文管道：检索调度、去重排序、全文获取、PDF 解析、长文摘要、引用分析。
- `docs/` — 技术调研与说明（如《科学论文 AI 研究代理—技术调研》）。

## 文档与参考

- 科学论文检索与 API 使用：见 `docs/科学论文AI研究代理-技术调研.md`。
- 更多配置项、报告类型与前端部署可参考仓库内文档与注释。

## 致谢与开源协议

本项目在 **[GPT Researcher](https://github.com/assafelovic/gpt-researcher)** 开源项目基础上进行二次开发，针对科学论文检索、多学术数据源集成与科研报告流程做了扩展与定制。感谢原项目作者与社区。

本项目沿用 **Apache 2.0** 许可证。使用与二次开发请遵守该许可证及所依赖组件的相关条款。

---

<p align="right">
  <a href="#top">⬆ 回到顶部</a>
</p>
