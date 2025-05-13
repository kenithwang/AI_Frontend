**考虑核心代码以后的approach建议**

**核心目标：**

*   **轻量级前端：** 主要负责用户交互、文件选择（本地上传替代 Dropbox 自动获取）、参数配置、任务提交和状态展示。
*   **与后端解耦：** 通过 API 与 FastAPI 后端通信，后端再与你的核心 `audio2memo` Python 脚本逻辑（或其模块化版本）交互。
*   **异步任务处理：** 鉴于整个流程（特别是 LLM 处理）可能耗时较长，采用异步任务队列和状态轮询。
*   **用户友好：** 提供清晰的指引和反馈。

**前端技术选型建议 (保持一致性)：**

*   **框架:** Vue.js 3 (Composition API) - 保持轻量和开发效率。
*   **UI库:** Element Plus - 提供现成的美观组件。
*   **HTTP客户端:** Axios。

**后端调整（与核心代码交互方式）：**

你的 `audio2memo.md` 描述了一个完整的、主要通过 `run.py` 驱动的批处理流程。为了与 Web 前端集成，我们需要将其核心功能模块化，并由 FastAPI + Celery 来调度。

1.  **将 `run.py` 中的逻辑拆分为可由 Celery 调用的任务函数。**
    *   `process_audio.py`, `audio2text.py`, `text_to_wordforword.py`, `wordforword_to_memo.py`, `combine_to_docx.py` 中的核心函数可以被封装成 Celery tasks。
    *   **不再从 Dropbox 自动获取最新文件，而是接收前端上传的文件。**
    *   用户在前端选择的参数 (如语音识别模型) 将作为参数传递给 Celery 任务。

2.  **FastAPI 接口：**
    *   **文件上传接口：** 接收用户上传的音频文件。
    *   **任务创建接口：** 接收文件ID、用户选择的参数（如转录模型、是否生成逐字稿、是否生成纪要、邮件通知设置等），然后将一个主任务（调用 `audio2memo` 核心流程）提交到 Celery。
    *   **任务状态查询接口：** (同前)

**前端实现建议：**

**1. 页面布局与组件规划**

可以设计成一个单页应用 (SPA)，包含以下主要区域/组件：

*   **`App.vue` (主应用组件)**
    *   整体布局（Header, Main Content, Footer）。
    *   管理全局状态或在子组件间传递 props/events。

*   **`FileUpload.vue` (音频上传组件)**
    *   **功能:**
        *   拖拽或点击选择本地音频文件 (MP3, M4A, WAV 等)。
        *   前端进行初步的文件类型和大小校验。
        *   调用后端 `/api/upload_audio` 接口上传文件。
        *   显示上传进度。
        *   上传成功后，将 `file_id` (或完整文件信息) 传递给父组件或通过事件总线/状态管理发送。
    *   **UI元素:**
        *   Element Plus 的 `el-upload` 组件 (支持拖拽)。
        *   文件列表显示（已上传的文件名、大小）。

*   **`ProcessingOptions.vue` (处理选项配置组件)**
    *   **功能:** 允许用户配置 `audio2memo` 流程中的可选参数。
    *   **UI元素 (示例):**
        *   **语音识别模型选择:**
            *   Element Plus `el-radio-group` 或 `el-select`。
            *   选项: `gpt-4o-transcribe` (默认), `gpt-4o-mini-transcribe`, `whisper-1` (与 `run.py` 中的选项一致)。
            *   数据绑定到 Vue data `selectedTranscribeModel`。
        *   **输出内容选择 (可选，如果希望用户能定制):**
            *   Element Plus `el-checkbox-group`。
            *   选项: "生成优化逐字稿", "生成会议纪要"。
            *   数据绑定到 Vue data `outputOptions` (e.g., `{ generateWordForWord: true, generateMemo: true }`)。
        *   **(我们之前讨论的) 邮件通知配置 (`EmailForm.vue` 的复用或集成):**
            *   "To" 邮箱输入 (自动补全 `@bda.com` 后缀，`;` 分隔)。
            *   "CC" 邮箱下拉选择 (白名单，必填，`;` 分隔)。
            *   数据绑定到 Vue data `emailTo`, `emailCc`。

*   **`TaskSubmit.vue` (任务提交与状态显示组件)**
    *   **功能:**
        *   显示已选择的文件和配置选项的摘要。
        *   “开始处理”按钮。
        *   点击按钮后，收集所有信息 (上传的 `file_id`, `selectedTranscribeModel`, `outputOptions`, `emailTo`, `emailCc`)，调用后端 `/api/create_audiomemo_task` 接口。
        *   后端返回 `task_id` 后，开始轮询 `/api/task_status/{task_id}`。
        *   实时显示任务状态、当前步骤、进度（如果后端提供）、最终结果链接或消息。
    *   **UI元素:**
        *   确认信息区域。
        *   Element Plus `el-button` (提交按钮)。
        *   **任务状态显示区域:**
            *   Element Plus `el-steps` (显示流程步骤：上传 -> 分割 -> 转录 -> 逐字稿 -> 纪要 -> 输出 -> 完成)。
            *   Element Plus `el-progress` (显示整体进度或当前步骤进度)。
            *   文本区域显示详细状态消息 (`task.message`)。
            *   处理完成后，显示下载链接 (如果生成文件可供下载) 或成功/失败提示。
            *   Element Plus `el-alert` (用于显示成功、错误、警告信息)。

*   **`TaskList.vue` (历史任务列表 - 可选高级功能)**
    *   **功能:** 如果希望用户能看到自己提交过的历史任务及其状态。
    *   **UI元素:** Element Plus `el-table`。

**2. 交互流程**

1.  **用户进入页面。**
2.  **上传音频 (FileUpload.vue):**
    *   用户拖拽或选择音频文件。
    *   文件上传到后端，前端获取 `file_id`。
    *   界面显示已上传的文件名。
3.  **配置选项 (ProcessingOptions.vue):**
    *   用户选择语音识别模型。
    *   用户选择希望生成的输出内容 (逐字稿、纪要)。
    *   用户填写邮件通知的 "To" 和 "CC" 地址。
4.  **提交任务 (TaskSubmit.vue):**
    *   用户点击“开始处理”。
    *   前端将 `file_id` 和所有配置选项发送到后端 `/api/create_audiomemo_task`。
    *   后端立即返回 `task_id` 和初始状态 (e.g., "QUEUED")。
5.  **状态跟踪 (TaskSubmit.vue):**
    *   前端开始使用 `task_id` 定期轮询 `/api/task_status/{task_id}`。
    *   根据后端返回的状态 (`QUEUED`, `PREPROCESSING_AUDIO`, `TRANSCRIBING`, `GENERATING_WORD_FOR_WORD`, `GENERATING_MEMO`, `COMBINING_OUTPUTS`, `SENDING_NOTIFICATION`, `COMPLETED`, `FAILED`) 和 `message` 更新界面。
    *   `el-steps` 组件可以根据这些状态高亮当前步骤。
    *   如果 `FAILED`，显示错误信息。
    *   如果 `COMPLETED`：
        *   显示成功消息。
        *   如果后端返回了可下载文件的链接 (例如 OSS 上的 Markdown 文件链接，或一个临时下载链接指向服务器上的 DOCX 文件)，则提供下载按钮。
        *   提示邮件已发送。

**3. 与核心代码的交互方式 (后端视角)**

*   **FastAPI 后端 (`main.py`)**
    *   `POST /api/upload_audio`: (同前) 保存上传的音频，返回 `file_id`。
    *   `POST /api/create_audiomemo_task`:
        *   接收 `file_id`, `transcribe_model`, `output_options`, `email_config` 等。
        *   **将这些参数连同音频文件的路径，传递给一个主 Celery 任务 `run_audio_to_memo_pipeline.delay(...)`。**
        *   返回 `task_id`。
    *   `GET /api/task_status/{task_id}`: (同前) 查询 Celery 任务状态。

*   **Celery 任务 (`tasks.py`)**
    *   `@celery_app.task(bind=True)`
      `def run_audio_to_memo_pipeline(self, audio_path, transcribe_model, output_options, email_config, ...):`
        *   **此任务将编排 `audio2memo.md` 中描述的整个流程。**
        *   **步骤1: 音频预处理与分割 (调用 `process_audio.py` 中的逻辑)**
            *   `self.update_state(state='PREPROCESSING_AUDIO', meta={'message': '正在分割音频...'})`
            *   调用 `split_audio(audio_path, output_dir_for_split_audio)`
            *   获取分割后的音频片段路径列表。
        *   **步骤2: 语音转文字 (调用 `audio2text.py` 中的逻辑)**
            *   `self.update_state(state='TRANSCRIBING', meta={'message': '正在进行语音识别...'})`
            *   遍历分割后的音频片段，对每个片段调用 `audio2text(segment_path, transcribe_model, output_dir_for_transcripts)`
            *   合并转录稿 (使用 `funcs.combine_transcripts`) 得到完整的原始转录稿路径。
        *   **步骤3: 生成逐字稿 (如果 `output_options.generateWordForWord`)**
            *   `self.update_state(state='GENERATING_WORD_FOR_WORD', meta={'message': '正在生成优化逐字稿...'})`
            *   调用 `text_to_wordforword(combined_transcript_path, output_dir_for_wordforword, llm_config)`
            *   获取优化逐字稿文件路径。
        *   **步骤4: 生成会议纪要 (如果 `output_options.generateMemo`)**
            *   `self.update_state(state='GENERATING_MEMO', meta={'message': '正在生成会议纪要...'})`
            *   **注意 `audio2memo.md` 中指出的逻辑问题：** 确保这里使用的是正确的输入（原始转录稿还是优化逐字稿）。假设使用优化逐字稿 (如果已生成)，否则使用原始转录稿。
            *   调用 `wordforword_to_memo(input_text_for_memo_path, output_dir_for_memo, llm_config)`
            *   获取纪要文件路径。
        *   **步骤5: 合并输出与分发 (调用 `combine_to_docx.py` 中的逻辑)**
            *   `self.update_state(state='COMBINING_OUTPUTS', meta={'message': '正在生成输出文件并分发...'})`
            *   调用 `combine_to_docx(memo_path, wordforword_path, docx_output_dir, markdown_output_dir, oss_config)`
            *   这里不再从 Dropbox 复制，因为源文件是前端上传的。可以考虑将生成的 DOCX 和 MD 文件保存到服务器上一个可供临时下载的目录，或者直接上传到 OSS 并返回链接。
        *   **步骤6: (我们之前讨论的) 文件“编辑”以触发加密 (如果需要)**
            *   如果生成的 DOCX/MD 需要邮件发送前加密，在这里插入加密触发和等待逻辑。
            *   获取加密后的文件路径。
        *   **步骤7: 发送邮件通知 (使用 `EmailForm` 的配置)**
            *   `self.update_state(state='SENDING_NOTIFICATION', meta={'message': '正在发送邮件通知...'})`
            *   使用 `email_config` 中的 `toEmails`, `ccEmails`。
            *   附件为加密后的文件（如果执行了步骤6）或 `combine_to_docx` 生成的原始文件。
        *   **步骤8: 清理临时文件 (可选)**
        *   **返回结果:**
            ```python
            return {
                "status": "COMPLETED",
                "message": "处理完成！",
                "docx_oss_url": "...", # 如果上传到OSS
                "markdown_oss_url": "...", # 如果上传到OSS
                # 或 "download_links": {"docx": "/api/download/task_id/file.docx"}
            }
            ```
        *   **错误处理:** 在每个步骤中使用 `try-except`，并在失败时 `self.update_state(state='FAILED', meta={'message': '错误信息'})` 并 `raise` 异常。

**4. 数据结构建议 (前端 Vue data)**

*   `uploadedFile: null` (Object: `{ id: 'backend_file_id', name: 'audio.mp3', size: 102400 }`)
*   `transcribeModel: 'gpt-4o-transcribe'`
*   `outputSelection: { wordForWord: true, memo: true }`
*   `emailToRaw: ''`
*   `selectedCcEmails: []`
*   `currentTask: null` (Object: `{ id: 'celery_task_id', status: 'QUEUED', message: '...', step: '...', progress: 0, resultUrls: {} }`)
*   `isSubmitting: false`
*   `isPolling: false`

**前端文件结构示例:**

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── FileUpload.vue
│   │   ├── ProcessingOptions.vue
│   │   ├── EmailFormPartial.vue  # (如果邮件表单部分被复用)
│   │   └── TaskSubmitDisplay.vue # (任务提交按钮和状态显示区域)
│   ├── views/
│   │   └── HomePage.vue          # 组合所有组件的主页面
│   ├── services/
│   │   └── api.js                # Axios 实例和 API 调用函数
│   ├── App.vue
│   └── main.js                 # Vue 初始化, Element Plus, Axios
├── package.json
└── vue.config.js (可选)
```

**关键交互点总结：**

*   **前端的轻量化:** 前端不执行任何 `audio2memo` 的核心逻辑，只负责收集用户输入和展示后端反馈。
*   **后端的模块化:** 将 `audio2memo` 的各个 Python 脚本功能封装成函数，由 Celery 任务统一调度。
*   **清晰的API边界:** FastAPI 提供上传、任务创建、状态查询的接口。
*   **详细的状态反馈:** Celery 任务在执行不同阶段时，通过 `update_state` 更新其状态和元信息，前端轮询获取并展示给用户，提升用户体验。

这种设计将前端的复杂性降到最低，同时充分利用了你现有后端代码的强大功能，并通过异步任务队列保证了系统的响应性和可扩展性。