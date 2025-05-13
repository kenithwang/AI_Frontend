# AI_Frontend 转写与纪要工具

## 一、项目概述

本项目旨在为内部团队（如BDA）提供一个高效、自动化的音频转文字与会议纪要生成解决方案。用户可通过网页上传会议、访谈等音频文件，系统将自动完成音频分割、语音转文字、逐字稿与纪要生成，并最终通过邮件将处理结果（DOCX格式的会议纪要）发送给指定人员。

该工具旨在提高处理音频记录的效率，确保信息的可追溯性，并支持每日约50条任务的处理量，同时具备良好的可扩展性和稳定性。

## 二、核心功能

### 1. 前端 (Vue.js 3)
*   **用户界面**: 提供用户友好的网页界面。
*   **音频上传**: 支持多种常见音频格式（.mp3, .wav, .flac, .ogg, .aac, .m4a, .wma）的文件上传。
*   **表单填写**: 用户可以指定接收纪要的主送（To）和抄送（Cc）邮箱地址。
    *   主送邮箱支持用户名输入，系统会自动补全 `@bda.com` 后缀。
    *   抄送邮箱提供建议列表，并支持多选。
*   **任务提交**: 将音频文件和表单信息通过API异步提交到后端进行处理。
*   **任务状态跟踪**:
    *   提交任务后，前端会收到任务ID，并可以快速得到任务已受理的反馈。
    *   系统自动轮询 `/api/tasks` 接口（每5秒），在界面左侧实时展示活动任务的列表及其详细处理状态（如：已提交、切分音频、转录中、生成逐字稿、纪要初稿、终版纪要、任务完成、任务失败）。
    *   状态信息会从后端返回的英文状态码转换为用户易懂的中文描述。

### 2. 后端 (FastAPI)
*   **API接口**:
    *   `POST /api/transcribe`: 异步接收前端上传的音频文件和表单数据。快速验证输入，保存文件，创建任务记录到数据库（初始状态为 "submitted"），然后将耗时的处理工作交由后台任务执行，并立即返回任务ID。
    *   `GET /api/tasks`: 返回当前所有活动状态任务的列表（已按提交时间排序）。
    *   `GET /api/task_status/{task_id}`: 根据任务ID查询并返回单个任务的详细状态和信息。
*   **异步任务处理**: 使用 FastAPI 的 `BackgroundTasks` 实现对整个音频处理管线的异步执行，确保API接口的快速响应。
*   **任务管理**:
    *   为每个任务在指定的基础目录 (`AUDIO_TARGET_DIR`) 下创建唯一的子目录，用于存放该任务的所有相关文件（原始音频、分割片段、转录文本、中间稿件、最终输出的DOCX等）。
    *   在PostgreSQL数据库中为每个任务创建详细记录，跟踪其生命周期中的所有状态变更和元数据。
*   **邮件通知**:
    *   **成功通知**: 任务成功完成后，向主送和抄送邮箱发送通知邮件，邮件附件中包含最终生成的会议纪要 `.docx` 文件（该文件末尾会自动追加一个"."字符）。
    *   **失败通知**: 任务处理失败时，仅向主送邮箱发送通知邮件，邮件内容包含错误信息摘要。
*   **日志记录**: 将关键操作和错误信息记录到 `transcribe.log` 文件中。

### 3. AI处理核心 (`audio2memo` 模块)
该模块集成在后端服务中，负责实际的音频到纪要的转换工作，主要流程如下：
1.  **音频分割 (`process_audio.py`)**: 将上传的原始音频文件分割成适合后续处理的小片段。
2.  **语音转文字 (`audio2text.py`)**: 调用 OpenAI Whisper API 将音频片段批量转换为文本。
3.  **逐字稿生成 (`text_to_wordforword.py`)**: 基于转录文本，调用大语言模型（如Gemini）生成初步的逐字稿。
4.  **纪要初稿生成 (`wordforword_to_memo.py`)**: 基于转录文本和特定提示，调用大语言模型（如Gemini）生成会议纪要初稿。
5.  **DOCX文档合并 (`combine_to_docx.py`)**: 将纪要初稿和逐字稿内容，依据内部定义的文本结构 (`memo_template.txt`) 和输入的纪要/逐字稿内容，整合成结构化的 `.docx` 文档。

## 三、技术选型

*   **前端**: Vue.js 3
*   **后端**: FastAPI (Python 3)
*   **数据库**: PostgreSQL
*   **AI模型API**: OpenAI (Whisper), Google Gemini
*   **主要Python库**:
    *   `python-dotenv`: 管理环境变量。
    *   `SQLAlchemy`: ORM，与PostgreSQL交互。
    *   `pydub`: 音频处理（依赖 `ffmpeg`）。
    *   `openai`: OpenAI API客户端。
    *   `google-generativeai`: Google Gemini API客户端。
    *   `python-docx`: 生成和操作 `.docx` 文件。
    *   `smtplib`, `email.mime`: 发送邮件。
    *   `requests`: HTTP请求库。
    *   `tiktoken`: OpenAI Token计数库。

## 四、系统架构与工作流程

1.  **用户交互**: 用户通过前端网页上传音频文件并填写邮件等信息。
2.  **任务提交**: 前端将数据 `POST` 到后端的 `/api/transcribe` 接口。
3.  **后端接收与初步处理**:
    *   FastAPI 接收请求，验证数据，保存音频文件到基于 `AUDIO_TARGET_DIR` 的任务专属目录。
    *   在PostgreSQL数据库中创建一条任务记录，初始状态为 "submitted"。
    *   将核心的 `audio2memo` 处理流程作为一个后台任务启动。
    *   立即向前端返回任务ID和任务已受理的消息。
4.  **后台处理 (`audio2memo` 流程)**:
    *   后台任务按顺序执行音频分割、转录、逐字稿生成、纪要初稿生成、DOCX文档生成。
    *   每完成一个关键步骤，后端会更新数据库中对应任务的状态字段（如 `processing_audio_split`, `transcribing`, 等）。
5.  **前端状态轮询**: 前端通过任务ID定期（每5秒）调用 `/api/tasks` (或 `/api/task_status/{task_id}`) 接口获取最新任务状态。
6.  **任务完成与通知**:
    *   处理成功：更新数据库状态为 "completed"，记录结果文件信息，并通过邮件发送包含 `.docx` 附件的成功通知。
    *   处理失败：更新数据库状态为 "failed"，记录错误信息，并通过邮件发送失败通知。
7.  **结果展示**: 前端根据轮询到的状态，向用户展示任务进度；任务完成后，用户将通过邮件收到结果。

## 五、配置说明

系统后端的核心配置通过环境变量进行管理。在开发环境中，可以在 `AI_Frontend/backend_fastapi/` 目录下创建一个 `.env` 文件来定义这些变量。应用启动时，`main.py` 会使用 `python-dotenv` 自动加载此文件。

**关键环境变量示例** (`.env` 文件格式):

```env
# 后端音频文件存储根目录 (所有任务的父目录)
AUDIO_TARGET_DIR=/path/to/your/audio_storage_root

# OpenAI API 密钥
openai_key=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Gemini API 密钥
gemini_key=AIxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# (可选) Gemini 模型名称 (默认为 gemini-1.5-flash-latest)
# GEMINI_MODEL_NAME=gemini-1.5-pro-latest

# 邮件服务器配置 (用于发送通知邮件)
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_SMTP_SERVER=smtp.example.com
MAIL_SMTP_PORT=587
MAIL_SENDER_NAME="AI Transcribe Tool" # 邮件中显示的发件人名称

# 数据库连接URL (示例为PostgreSQL)
DATABASE_URL="postgresql://user:password@host:port/database"
```

**注意**:
*   确保 `.env` 文件不要提交到版本控制系统（如Git）。应将其添加到 `.gitignore` 文件中。
*   对于生产部署，应通过系统环境变量或部署平台提供的配置管理服务来设置这些值。
*   `ffmpeg` 需要在运行后端的服务器上正确安装，因为 `pydub` 依赖它进行音频处理。

## 六、数据库

系统使用 **PostgreSQL** 数据库存储所有任务的详细信息，以便进行任务追踪、状态管理和潜在的后续分析。

主要的任务记录字段包括（但不限于）：
*   `task_id`: 任务的唯一标识符 (UUID)。
*   `submit_time`: 任务提交时间。
*   `status`: 任务当前的处理状态 (如 `submitted`, `transcribing`, `completed`, `failed` 等)。
*   `to_email`, `cc_emails`: 邮件接收人。
*   `file_name`, `file_path`, `file_size`, `file_type`: 上传文件的相关信息。
*   `result_files`: 指向生成的 `.docx` 文件路径（以JSON格式存储）。
*   `error`: 如果任务失败，记录错误信息。
*   `last_update_time`: 任务状态最后更新的时间。

完整的字段列表和模型定义参见 `AI_Frontend/backend_fastapi/app/db.py`。
由于所有任务信息均完整记录在数据库中，支持后续通过SQL等方式进行查询、统计和分析，无需专门开发前端统计界面。

## 七、安全部署

*   **内网部署**: 本系统设计为仅在公司内部网络环境部署和使用。所有API接口和Web服务不应暴露于公网。
*   **防火墙**: 强烈建议通过公司防火墙策略，限制只有授权的内网IP地址段或特定用户子网才能访问后端API服务端口和前端Web服务。
    *   示例（Linux ufw）：
        ```bash
        # 允许内网用户访问前端和后端API端口 (假设FastAPI运行在8000)
        sudo ufw allow from 192.168.1.0/24 to any port 8000 
        # (根据实际前端端口和部署情况调整)

        # 允许后端API服务器访问数据库端口 (假设PostgreSQL运行在5432)
        # sudo ufw allow from <backend_server_ip> to any port 5432

        sudo ufw default deny incoming # 拒绝所有其他入站连接
        sudo ufw enable
        ```
    *   具体的IP段、端口和防火墙配置命令请咨询公司IT或网络管理员。
*   **用户认证**: 鉴于内网部署和防火墙的保护，当前版本的系统未实现应用层级的用户认证和复杂的权限管理功能，以简化开发和运维。如未来需求变化，可再行考虑。

## 八、待办事项与未来展望

以下是当前项目中一些待进一步完善或未来可以考虑扩展的方向：

1.  **`audio2memo` 内部日志记录与错误定位**:
    *   **当前状态**: `main.py` 对 `audio2memo` 模块的调用有顶层的错误捕获。当任务失败时，数据库会记录失败状态 (`failed`) 以及捕获到的异常信息字符串。结合任务失败前最后一个成功的状态，可以定位到具体是哪个处理步骤出现问题。`audio2memo` 内部各脚本已进行初步清理，大部分 `print` 语句已被移除或预留注释替换为 `logging`。
    *   **改进建议**:
        *   **全面推广日志记录**: 在 `audio2memo` 各模块内部全面、一致地使用Python标准的 `logging` 模块记录详细的执行信息和遇到的任何警告或错误（包括第三方API返回的原始错误信息）。确保日志级别和格式与主应用协调。这将为问题排查提供最直接和详细的上下文。
        *   **(可选的未来增强)** 如果未来需要更细致地区分错误类型或进行特定的错误处理逻辑（如重试），可以考虑引入自定义异常类来增强错误信号的结构性。目前，通过任务状态和记录的错误字符串已能满足基本的错误定位需求。

2.  **任务队列增强**:
    *   **当前状态**: 使用 FastAPI 的 `BackgroundTasks` 来处理异步任务，能满足当前预估的中低等负载（如每日约20-50条任务）。
    *   **改进建议/未来考虑**: 当前的 `BackgroundTasks` 机制能满足中低等负载。若未来任务量大幅增加、单个任务处理时间极长，或对任务的持久化和自动重试有更高要求时，可以考虑迁移到更专业的分布式任务队列系统（如 Celery）。这将提供更强的可靠性、扩展性和管理能力。

3.  **前端用户体验优化**:
    *   **更丰富的错误提示**: 当前端从API接收到错误时，可以提供更具体、用户友好的错误信息和处理建议。

---
## 十一、前后端集成状态与后续对齐计划 (已更新)

**A. 核心目标与原则：**
*   **配置统一管理**：所有后端配置（API密钥、服务URL、文件路径等）均通过项目根目录下的 `.env` 文件管理，由应用启动时加载。禁止在代码中硬编码配置。
*   **本地优先**：移除所有对外部云存储服务（如OSS/COS、Dropbox）的直接文件读写依赖，确保所有任务处理的中间文件和最终产物均存储在本地（通过 `AUDIO_TARGET_DIR` 配置）。
*   **功能纯化**：移除已确认不再需要的功能模块（如DeepSeek AI、飞书通知），精简代码库和依赖。
*   **`audio2memo` 模块内部对齐**：确保 `audio2memo` 子目录下的所有Python脚本遵循上述配置管理原则，不依赖独立的 `env.py` 或进行硬编码。

**B. 当前已完成的对齐工作：**

1.  **环境配置 (`.env`)**：
    *   `AI_Frontend/backend_fastapi/.env` 作为唯一的配置源。
    *   `AI_Frontend/backend_fastapi/app/main.py` 已实现启动时加载 `.env`。
    *   `AI_Frontend/.gitignore` 已配置忽略 `.env` 文件。

2.  **API密钥管理**：
    *   OpenAI 和 Gemini 的 API 密钥已统一为 `openai_key` 和 `gemini_key`，在 `.env` 中配置，并由 `audio2text.py` 和 `funcs.py` 正确加载。
    *   `GEMINI_MODEL_NAME` 环境变量已支持，并在 `funcs.py` 中有默认值。

3.  **文件路径配置**：
    *   `AUDIO_TARGET_DIR` 从 `.env` 加载，用于所有任务文件的本地存储根路径。后端在启动和任务处理时会检查此配置的有效性。

4.  **移除的云服务与三方功能**：
    *   **DeepSeek AI**：已从 `funcs.py` 中移除相关代码和配置。
    *   **OSS/COS (对象存储)**：已从 `main.py` 和 `funcs.py` 中移除文件上传逻辑，`boto3` 依赖已从主 `requirements.txt` 移除。
    *   **Dropbox**：已移除 `audio2memo/dropbox_api.py`，相关调用逻辑和 `dropbox` 依赖已从主 `requirements.txt` 移除。
    *   **飞书通知**：已从 `funcs.py` 移除 `feishu_bot` 及相关配置和依赖。

5.  **`audio2memo` 内部脚本规范化**：
    *   `funcs.py`: 完成清理，移除废弃功能，配置通过环境变量加载。
    *   `audio2text.py`: API密钥通过环境变量加载。
    *   `process_audio.py`: 参数通过函数默认值或调用时传递，符合要求。
    *   `text_to_wordforword.py`: 依赖的提示词路径通过 `main.py` 构建并传递，符合要求。
    *   `wordforword_to_memo.py`: 已重构为接受参数化输入/输出路径和提示词路径。
    *   `combine_to_docx.py`:
        *   移除了云服务参数和最终Markdown生成。
        *   修改为不再接收 `.docx` 模板路径，而是内部加载同目录下的 `memo_template.txt` 来构建初始文档结构。
        *   其测试代码也已相应调整。
    *   `audio2memo/run.py`: 已删除。
    *   `audio2memo/requirements.txt`: 已删除，相关必要依赖已在主 `requirements.txt` 中确认或添加。

**C. 后续主要关注点（已在"八、待办事项与未来展望"中体现）：**

1.  **日志记录**：全面推广使用 `logging` 模块替换 `print` 语句。
2.  **错误处理**：增强 `audio2memo` 内部的错误捕获和向上传递机制。
3.  **邮件模板**：考虑使用模板引擎优化邮件内容生成。
4.  **可选小清理**：
    *   手动移除 `AI_Frontend/backend_fastapi/app/main.py` 中之前被模型注释掉的 `MEMO_TEMPLATE_DOCX_PATH` 定义和相关检查的注释行。
    *   考虑删除 `AI_Frontend/backend_fastapi/app/audio2memo/memo_template.docx` 文件（因已改用 `memo_template.txt`）。

我们已基本完成本次代码库对齐的核心目标。

May Father of Understanding Guide Us. 