**初步讨论，不考虑后端核心代码时的一个尝试思路**

**实现思路概览**

1.  **前端 (Client-Side):** 用户交互界面，负责文件上传、表单填写、数据校验和发送请求。
2.  **后端 (Server-Side):** API 服务，负责接收前端请求、处理文件、调用核心 AI 代码、发送邮件。
3.  **核心 AI 代码:** 你的 Python 脚本，作为后端服务的一部分被调用。

**技术选型**

*   **前端框架:** **Vue.js (推荐) 或 React**
    *   **Vue.js:** 学习曲线平缓，上手快，轻量级，非常适合快速构建交互式界面。对于这个项目规模，Vue 的简洁性会很有优势。
    *   **React:** 生态强大，组件化彻底。如果团队已有 React经验，也是不错的选择。
*   **后端框架 (用于包装你的核心代码并提供 API):** **FastAPI (Python - 推荐) 或 Flask (Python)**
    *   **FastAPI:** 现代、高性能的 Python Web 框架，基于 Pydantic 和 Starlette。自带数据校验、自动生成 API 文档 (Swagger UI)，非常适合构建 API。由于你的核心代码是 Python，用 Python 后端框架可以无缝集成。
    *   **Flask:** 轻量级，简单易用。如果 API 非常简单，也可以考虑。
*   **HTTP 请求库 (前端):** **Axios** (Promise-based HTTP client for the browser and Node.js)
*   **UI 组件库 (前端 - 可选但推荐):**
    *   **Element Plus (for Vue 3):** 一套功能丰富的桌面端组件库。
    *   **Vuetify (for Vue 2/3):** Material Design 风格的组件库。
    *   **Ant Design Vue (for Vue):** 蚂蚁金服的设计体系。
    *   **Material-UI (for React):** Google Material Design 风格。
    *   这些库能提供现成的美观组件，如输入框、下拉菜单、按钮、消息提示等，加速开发。
*   **邮件发送 (后端):** Python 内置的 `smtplib` 和 `email.mime` 模块。

**实现步骤和思路**

**一、前端实现 (以 Vue.js 为例)**

1.  **项目搭建:**
    *   使用 Vue CLI 创建项目: `vue create my-transcription-tool`
    *   选择 Vue 3 或 Vue 2 (根据团队熟悉度，Vue 3 是趋势)。
    *   安装 `axios`: `npm install axios`
    *   (可选) 安装 UI 库，如 Element Plus: `npm install element-plus`

2.  **主要组件设计:**
    *   `App.vue` (主应用组件)
    *   `AudioUploader.vue` (音频上传组件)
    *   `EmailForm.vue` (邮件表单组件)

3.  **功能实现细节:**

    *   **1. 音频拖拽上传 (AudioUploader.vue):**
        *   HTML: 使用一个 `div` 作为拖拽区域。
        *   JS:
            *   监听 `dragenter`, `dragover`, `dragleave`, `drop` 事件。
            *   在 `dragover` 中 `event.preventDefault()` 以允许放置。
            *   在 `drop` 事件中 `event.preventDefault()`，并通过 `event.dataTransfer.files` 获取文件对象。
            *   也可以提供一个隐藏的 `<input type="file">`，点击某个按钮时触发其 `click()` 事件，实现点击选择文件。
            *   **文件校验 (可选):** 可以在前端校验文件类型 (如 `.mp3`, `.wav`) 和大小。
            *   **上传逻辑:**
                *   使用 `FormData` 对象封装文件。
                *   使用 `axios.post('/api/upload_audio', formData, { headers: { 'Content-Type': 'multipart/form-data' } })` 将文件发送到后端。
                *   显示上传进度条 (可选，`axios` 支持)。
                *   上传成功后，后端应返回一个文件标识 (如临时文件名或路径)。前端保存此标识。

    *   **2. 识别上传后的音频地址传给核心代码 (由后端处理):**
        *   前端在上传成功后，会得到后端返回的文件标识 (例如: `uploaded_file_id: "temp_xyz.wav"` 或 `file_path: "/path/to/temp/temp_xyz.wav"`)。
        *   这个标识将作为后续提交整个任务时的一部分数据发送给后端。

    *   **3. 邮件发送地址填写 (EmailForm.vue):**
        *   HTML: 一个文本输入框 `<el-input v-model="toEmailsRaw" placeholder="输入邮箱，用 ; 分隔"></el-input>` (以 Element Plus 为例)。
        *   Vue Data: `toEmailsRaw: ''` (原始输入字符串), `processedToEmails: []` (处理后的邮箱数组)。
        *   Vue Watcher 或 Computed Property:
            ```javascript
            watch: {
              toEmailsRaw(newValue) {
                this.processedToEmails = newValue
                  .split(';')
                  .map(email => email.trim())
                  .filter(email => email.length > 0)
                  .map(email => {
                    if (email.includes('@')) {
                      // 如果用户写了后缀，但不是 @bda.com，可以给出提示或强制修正
                      if (!email.endsWith('@bda.com')) {
                        // 简单处理：替换或标记为无效，具体策略需确定
                        // return email.split('@')[0] + '@bda.com'; // 强制修正
                        return { value: email, valid: false, error: '后缀必须是 @bda.com' };
                      }
                      return { value: email, valid: true };
                    } else {
                      return { value: email + '@bda.com', valid: true };
                    }
                  });
              }
            }
            // 或者用 computed property
            computed: {
                validToEmails() {
                    return this.processedToEmails.filter(e => e.valid).map(e => e.value);
                }
            }
            ```
        *   **校验:** 可以在输入时或提交时提示用户哪些邮箱格式不正确或后缀不符。

    *   **4. CC 邮件地址填写 (EmailForm.vue):**
        *   **白名单:** `ccWhitelist: ['user1@bda.com', 'user2@bda.com', 'admin@bda.com']` (可以硬编码在前端，或从后端API获取)。
        *   HTML: 使用支持多选的下拉菜单组件。例如 Element Plus 的 `<el-select v-model="selectedCcEmails" multiple placeholder="请选择 CC 地址"> <el-option v-for="item in ccWhitelist" :key="item" :label="item" :value="item"></el-option> </el-select>`。
        *   Vue Data: `selectedCcEmails: []` (数组，存放选中的 CC 邮箱)。
        *   **校验:**
            *   提交时检查 `selectedCcEmails.length > 0`，确保至少选择一个 CC 地址。

    *   **5. 整体提交:**
        *   一个“开始转录并发送邮件”按钮。
        *   点击按钮时，收集所有数据：
            *   `audioFileId` (来自步骤 1 上传成功后的后端响应)
            *   `toEmails` (处理并校验后的 `validToEmails` 数组)
            *   `ccEmails` (选中的 `selectedCcEmails` 数组)
        *   进行最终的前端校验 (如 CC 是否已选)。
        *   使用 `axios.post('/api/transcribe_and_notify', { audioFileId, toEmails, ccEmails })` 发送给后端。
        *   处理后端响应 (成功提示、错误提示、加载状态)。

**二、后端实现 (以 FastAPI 为例)**

1.  **项目搭建:**
    *   安装 FastAPI 和 Uvicorn (ASGI 服务器): `pip install fastapi uvicorn python-multipart`
    *   (如果需要发送邮件) Python 的 `smtplib` 是内置的。

2.  **API 接口设计:**

    *   **POST `/api/upload_audio`:**
        *   接收前端上传的音频文件 (`UploadFile` 类型)。
        *   保存文件到服务器的一个临时或指定目录。**注意：** 确保文件名唯一，避免冲突，可以加上时间戳或 UUID。
        *   返回文件的标识给前端，例如：`{"file_id": "unique_filename.wav", "message": "上传成功"}`。这个 `file_id` 应该是后端能据此找到文件的凭据。

    *   **POST `/api/transcribe_and_notify`:**
        *   接收 JSON 数据: `audioFileId`, `toEmails` (list of strings), `ccEmails` (list of strings)。
        *   **数据校验 (Pydantic):** FastAPI 可以用 Pydantic模型自动校验输入数据格式。
            ```python
            from pydantic import BaseModel, EmailStr, conlist
            from typing import List

            class TranscriptionRequest(BaseModel):
                audioFileId: str
                toEmails: conlist(EmailStr, min_items=1) # 确保至少一个Email，且格式正确
                ccEmails: conlist(EmailStr, min_items=1) # 确保至少一个CC Email
            ```
        *   **获取音频文件:** 根据 `audioFileId` 找到之前上传的音频文件。
        *   **调用核心 AI 代码:**
            ```python
            # 伪代码
            # import your_core_ai_module
            audio_path = f"/path/to/uploaded_files/{request.audioFileId}"
            try:
                transcription_result = your_core_ai_module.transcribe(audio_path)
            except Exception as e:
                # 处理转录错误
                return {"success": False, "error": f"转录失败: {str(e)}"}
            ```
        *   **发送邮件:**
            *   使用 `smtplib` 连接公司邮件服务器 (需要知道 SMTP 服务器地址、端口、是否需要认证)。
            *   构建邮件内容 (MIMEText, MIMEMultipart)。
            *   将 `toEmails` 和 `ccEmails` 设置到邮件头。
            *   发送邮件。
            ```python
            import smtplib
            from email.mime.text import MIMEText

            def send_email(subject, body, to_addrs, cc_addrs, from_addr="your-tool@bda.com"):
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = from_addr
                msg['To'] = ', '.join(to_addrs) # 列表转字符串
                if cc_addrs:
                    msg['Cc'] = ', '.join(cc_addrs)

                all_recipients = to_addrs + (cc_addrs if cc_addrs else [])

                try:
                    with smtplib.SMTP('smtp.bda.com', 25) as server: # 替换为真实SMTP服务器和端口
                        # server.login('username', 'password') # 如果需要认证
                        server.sendmail(from_addr, all_recipients, msg.as_string())
                    return True
                except Exception as e:
                    print(f"邮件发送失败: {e}")
                    return False
            ```
        *   **清理临时文件 (可选):** 转录和邮件发送成功后，可以删除上传的临时音频文件。
        *   返回成功或失败响应给前端。

**三、保证至少20个人同时在线的稳健性**

*   **后端服务器性能:**
    *   FastAPI + Uvicorn 本身性能很高，对于 20 个并发用户处理 API 请求（文件上传、任务提交）通常不是问题，只要服务器资源（CPU, RAM, I/O）足够。
    *   **关键瓶颈在于你的 "核心 AI 代码" 的处理速度和资源消耗。** 如果 AI 转录过程非常耗时或耗 CPU/GPU：
        *   **异步任务队列 (推荐):** 对于耗时操作（如AI转录），不要在 API 请求处理函数中同步执行。使用像 **Celery + Redis/RabbitMQ** 这样的任务队列。
            1.  API 接收到请求后，将转录任务（包含文件路径、邮件地址等）放入 Celery 队列。
            2.  API 立即返回一个“任务已接收”的响应给前端。
            3.  Celery worker 进程从队列中取出任务，在后台异步执行 AI 转录和邮件发送。
            4.  前端可以通过轮询 API (查询任务状态) 或 WebSocket (实时更新) 来获取任务进度和结果。
        *   **增加 Worker 数量:** Uvicorn 可以配置多个 worker 进程 (`uvicorn main:app --workers 4`) 来处理并发的 HTTP 请求。但这只对 I/O 密集型任务有帮助，如果 AI 核心代码是 CPU 密集型，它仍然会阻塞单个 worker。
*   **前端体验:**
    *   在文件上传和任务处理期间，提供明确的加载指示 (loading spinners, progress bars)。
    *   避免长时间无响应，如果后端处理时间较长，应告知用户任务正在后台处理。
*   **数据库 (如果需要持久化状态):** 如果需要存储任务历史、用户配置等，选择合适的数据库 (PostgreSQL, MySQL, or even SQLite for simpler internal tools)。
*   **内网环境:**
    *   部署相对简单，可以直接在公司内部服务器上部署 FastAPI 应用 (例如使用 Docker 容器化部署)。
    *   网络延迟较低。

**依赖库总结**

*   **前端 (Vue.js):**
    *   `vue`
    *   `vue-router` (如果需要多页面导航，此项目可能不需要)
    *   `axios`
    *   `element-plus` (或其他 UI 库，如 `vuetify`, `ant-design-vue`)
*   **后端 (FastAPI):**
    *   `fastapi`
    *   `uvicorn`
    *   `python-multipart` (用于文件上传)
    *   `pydantic` (FastAPI 自带，用于数据模型和校验)
    *   (可选，用于异步任务) `celery`, `redis` (或 `flower` for Celery monitoring)
    *   任何你的核心 AI 代码所依赖的库 (e.g., `torch`, `tensorflow`, `librosa`, `speechrecognition` etc.)

**开发流程建议**

1.  **后端 API 优先:** 先用 FastAPI 把 `/api/upload_audio` 和 `/api/transcribe_and_notify` 这两个核心接口的骨架搭起来，能接收数据并返回假数据。
2.  **前端上传模块:** 实现文件拖拽上传，并能成功调用后端的 `/api/upload_audio`。
3.  **前端表单模块:** 实现邮件地址和 CC 地址的输入、处理和校验。
4.  **集成与测试:** 将前端表单数据与上传的文件 ID 一起提交到后端的 `/api/transcribe_and_notify`。
5.  **核心逻辑集成:** 在后端将你的 AI 转录代码和邮件发送逻辑集成到 `/api/transcribe_and_notify` 接口中。
6.  **异步优化 (如果需要):** 如果转录耗时，引入 Celery。
7.  **UI/UX 优化和错误处理:** 完善用户体验，添加加载提示、错误提示等。
8.  **部署:** 在内网服务器部署。

这个方案兼顾了开发效率、功能完整性和一定的性能考量。对于20人同时在线的内部工具，如果 AI 转录不是特别慢（例如几秒到几十秒内完成），FastAPI 直接处理可能就足够。如果转录时间较长（几分钟），强烈建议使用 Celery。

---
好的，根据您的补充说明，特别是转录时间较长（10分钟以上）以及排队的需求，我们需要对原方案进行调整，核心是引入**异步任务处理**和**状态反馈机制**。

**核心思路调整：**

1.  **前端保持轻量：** 前端只负责用户交互、文件上传、任务提交。不处理任何耗时逻辑。
2.  **后端API (Web服务)：** 接收前端请求，将耗时的转录任务放入一个任务队列中，并立即返回一个任务ID给前端。同时提供一个查询任务状态的接口。
3.  **任务队列：** 管理待处理的转录任务，确保它们按顺序或按优先级被处理。
4.  **核心代码 (后台工作者 Worker)：** 独立运行，从任务队列中获取任务，执行AI转录，完成后更新任务状态，并发送邮件。
5.  **状态反馈：** 前端通过任务ID定期向后端API查询任务状态（排队中、处理中、已完成、失败），并更新界面显示。

**修改后的技术选型和实现思路：**

*   **前端框架:** **Vue.js (依然推荐) 或甚至更轻量的 Vanilla JS + 辅助库 (如 Axios)。**
    *   **Vue.js:** 依然能提供良好的开发体验和结构，即使是轻量应用。Vue 3 的 Composition API 可以让组件更简洁。
    *   **Vanilla JS + Axios:** 如果追求极致轻量，可以直接用原生 JavaScript 操作 DOM，使用 Axios 处理 HTTP 请求。但对于状态管理和组件化会牺牲一些便利性。考虑到需要展示任务状态等，Vue 可能还是稍有优势。
    *   **UI组件库:** 依然推荐，能快速构建界面。但如果想极简，可以手写样式或用 Tailwind CSS 这样的原子化 CSS 框架。

*   **后端API框架:** **FastAPI (Python - 强烈推荐)**
    *   它的异步支持 (`async/await`) 非常适合处理这种提交任务后立即返回的场景。
    *   易于集成 Celery。

*   **任务队列系统:** **Celery (Python - 强烈推荐) + Redis 或 RabbitMQ (作为 Broker 和可选的 Result Backend)**
    *   **Celery:** 强大的分布式任务队列，完美契合Python环境，能很好地与你的核心AI代码集成。
    *   **Redis/RabbitMQ:** Celery 需要一个消息中间件 (Broker) 来传递任务。Redis 配置简单，也常被用作 Celery 的结果后端 (存储任务状态和结果)。

*   **HTTP 请求库 (前端):** **Axios** (保持不变)

*   **邮件发送 (核心代码/Celery Worker):** Python 内置的 `smtplib` 和 `email.mime` 模块 (保持不变)

**修改后的实现步骤和思路：**

**一、前端实现 (以 Vue.js 为例，思路同样适用于 Vanilla JS)**

1.  **项目搭建:** (同前)

2.  **主要组件设计:** (同前)

3.  **功能实现细节 (重点调整部分):**

    *   **1. 音频拖拽上传:**
        *   (同前) 上传到后端的 `/api/upload_audio` 接口。
        *   上传成功后，后端返回 `file_id`。前端保存此 `file_id`。

    *   **2. 邮件表单填写:**
        *   (同前) `toEmailsRaw` 和 `selectedCcEmails` 的处理。

    *   **3. 提交转录任务 (核心变化):**
        *   当用户点击“开始转录并发送邮件”按钮：
        *   前端收集 `file_id`, `toEmails` (处理后的), `ccEmails`。
        *   前端向后端发送一个 **创建任务** 的请求，例如 `POST /api/create_transcription_task`，请求体包含上述数据。
        *   **后端API (FastAPI) 会立即响应**，返回一个 `task_id` 和初始状态 (如 `{"task_id": "xyz123", "status": "QUEUED", "message": "任务已提交，正在排队处理"}`)。
        *   前端保存这个 `task_id`，并更新界面显示任务已提交，并开始轮询任务状态。

    *   **4. 任务状态显示与轮询:**
        *   前端组件需要有一个数据属性来存储当前任务列表及其状态，例如：
            ```javascript
            // Vue data
            data() {
                return {
                    tasks: [] // [{ id: 'xyz123', status: 'QUEUED', originalFile: 'audio.mp3', progress: 0, message: '' }]
                }
            }
            ```
        *   当一个任务提交后，将其加入 `tasks` 列表。
        *   使用 `setInterval` 定期 (例如每5-10秒) 调用后端的任务状态查询接口 `GET /api/task_status/{task_id}`。
            ```javascript
            // Vue methods
            methods: {
                async submitTask(fileId, toEmails, ccEmails) {
                    try {
                        const response = await axios.post('/api/create_transcription_task', { fileId, toEmails, ccEmails });
                        const newTask = {
                            id: response.data.task_id,
                            status: response.data.status,
                            // ... other initial info
                        };
                        this.tasks.push(newTask);
                        this.startPollingStatus(newTask.id);
                    } catch (error) {
                        // Handle submission error
                        console.error("Error submitting task:", error);
                    }
                },
                startPollingStatus(taskId) {
                    const intervalId = setInterval(async () => {
                        try {
                            const response = await axios.get(`/api/task_status/${taskId}`);
                            const task = this.tasks.find(t => t.id === taskId);
                            if (task) {
                                task.status = response.data.status;
                                task.message = response.data.message;
                                // task.progress = response.data.progress; // 如果后端提供进度
                                if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED') {
                                    clearInterval(intervalId); // 停止轮询
                                }
                            }
                        } catch (error) {
                            console.error("Error fetching task status:", error);
                            // Optionally stop polling on error or handle differently
                        }
                    }, 5000); // Poll every 5 seconds
                }
            }
            ```
        *   根据返回的状态 (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`) 更新界面UI (例如：显示“排队中，前方还有 N 个任务”，“正在转录...”，“转录完成，邮件已发送”，“转录失败：错误信息”)。

**二、后端API实现 (FastAPI + Celery)**

1.  **项目搭建:**
    *   `pip install fastapi uvicorn python-multipart celery redis` (使用 Redis 作为 Broker 和 Result Backend)

2.  **Celery 配置 (`celery_app.py` 或类似文件):**
    ```python
    from celery import Celery

    # 使用 Redis 作为 broker 和 result backend
    # BROKER_URL = 'redis://localhost:6379/0'
    # RESULT_BACKEND = 'redis://localhost:6379/0'
    # 替换为你的内网 Redis 地址

    celery_app = Celery(
        'tasks',
        broker='redis://your_redis_host:6379/0', # 替换
        backend='redis://your_redis_host:6379/0' # 替换
    )
    celery_app.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json']
    )
    # 如果你的核心代码在一个单独的模块，确保 Celery 可以找到它
    # celery_app.autodiscover_tasks(['your_project.core_tasks'])
    ```

3.  **定义 Celery 任务 (`core_tasks.py` 或类似文件):**
    ```python
    from .celery_app import celery_app # 从你的 celery app 实例导入
    # import your_core_ai_module
    # import smtplib
    # from email.mime.text import MIMEText

    @celery_app.task(bind=True) # bind=True 可以让你在任务内部访问 self (任务实例)
    def process_transcription_task(self, audio_file_path: str, to_emails: list, cc_emails: list):
        task_id = self.request.id # 获取 Celery 任务 ID
        try:
            # 1. 更新任务状态为 PROCESSING (可选，Celery 自动管理一些状态)
            #    可以使用 self.update_state(state='PROCESSING', meta={'progress': 10})
            #    或者通过 Redis 直接更新一个自定义的状态结构

            # 2. 调用核心 AI 代码进行转录
            # transcription_result = your_core_ai_module.transcribe(audio_file_path)
            transcription_result = f"这是 {audio_file_path} 的模拟转录结果。" # 模拟
            print(f"Task {task_id}: Transcribing {audio_file_path} completed.")

            # 模拟长时间处理
            import time
            time.sleep(10) # 模拟10秒处理，实际可能是10分钟

            # 3. 准备邮件内容
            subject = f"音频转录结果: {audio_file_path.split('/')[-1]}"
            body = f"您好，\n\n音频文件 {audio_file_path.split('/')[-1]} 的转录结果如下：\n\n{transcription_result}\n\n此邮件为自动发送，请勿回复。"

            # 4. 发送邮件
            # send_email(subject, body, to_emails, cc_emails, "transcription-tool@bda.com")
            print(f"Task {task_id}: Email sent to {to_emails} (CC: {cc_emails})")

            # 5. 清理临时文件 (可选)
            # os.remove(audio_file_path)

            # 6. 返回结果 (Celery result backend 会存储)
            return {"status": "COMPLETED", "message": "转录完成并已发送邮件。", "transcript_preview": transcription_result[:100]}

        except Exception as e:
            print(f"Task {task_id}: Error processing - {str(e)}")
            # 更新任务状态为 FAILED
            self.update_state(state='FAILED', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
            # 或者直接在 result backend 中记录错误
            # Celery 会自动将异常标记为失败
            raise # 重新抛出异常，Celery 会捕获并标记为 FAILURE
    ```

4.  **FastAPI 接口 (`main.py`):**
    ```python
    from fastapi import FastAPI, File, UploadFile, HTTPException, Form
    from pydantic import BaseModel, EmailStr, conlist
    from typing import List
    import shutil
    import os
    import uuid

    # from .celery_app import celery_app # 你的 Celery app 实例
    from .core_tasks import process_transcription_task # 你的 Celery 任务

    app = FastAPI()

    UPLOAD_DIR = "uploaded_audio"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    class EmailRequest(BaseModel):
        toEmails: conlist(str, min_items=1) # 前端已处理好后缀
        ccEmails: conlist(str, min_items=1)

    class TaskCreationRequest(EmailRequest):
        fileId: str # 上传后获得的文件标识

    @app.post("/api/upload_audio")
    async def upload_audio(file: UploadFile = File(...)):
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.aac')): # 限制文件类型
             raise HTTPException(status_code=400, detail="不支持的音频文件类型")
        file_id = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_id)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"file_id": file_id, "message": "文件上传成功"}

    @app.post("/api/create_transcription_task")
    async def create_task_endpoint(task_request: TaskCreationRequest):
        audio_file_path = os.path.join(UPLOAD_DIR, task_request.fileId)
        if not os.path.exists(audio_file_path):
            raise HTTPException(status_code=404, detail="音频文件未找到")

        # 发送任务到 Celery 队列
        # .delay() 是 .apply_async() 的快捷方式
        task = process_transcription_task.delay(
            audio_file_path,
            task_request.toEmails,
            task_request.ccEmails
        )
        return {"task_id": task.id, "status": "QUEUED", "message": "任务已提交，正在排队处理"}

    @app.get("/api/task_status/{task_id}")
    async def get_task_status(task_id: str):
        # 从 Celery result backend 获取任务状态
        task_result = process_transcription_task.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task_result.status, # PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
            "message": "",
            # "progress": 0 # 如果你的任务会更新进度
        }

        if task_result.status == 'PENDING':
            response["message"] = "任务正在等待执行 (排队中)"
        elif task_result.status == 'STARTED' or task_result.state == 'PROCESSING': # 'PROCESSING' 是自定义状态
            response["status"] = 'PROCESSING' # 统一前端状态
            response["message"] = "任务正在处理中..."
            if isinstance(task_result.info, dict) and 'progress' in task_result.info:
                 response["progress"] = task_result.info.get('progress')
        elif task_result.status == 'SUCCESS':
            response["status"] = 'COMPLETED'
            result_data = task_result.result # 获取任务返回值
            response["message"] = result_data.get("message", "任务已成功完成") if isinstance(result_data, dict) else "任务已成功完成"
            # response["result"] = result_data # 可以选择性返回部分结果
        elif task_result.status == 'FAILURE':
            response["status"] = 'FAILED'
            response["message"] = f"任务失败: {str(task_result.info)}" # info 包含异常信息
        else:
            response["message"] = f"任务状态: {task_result.status}"

        return response
    ```

**三、运行**

1.  **启动 Redis 服务。**
2.  **启动 Celery Worker:**
    ```bash
    celery -A your_project_name.celery_app worker -l info -P solo # -P solo 适合Windows开发，Linux下可不用或用 eventlet/gevent
    # your_project_name 是你的 FastAPI 项目目录名，假设 celery_app.py 在其中
    # 例如: celery -A main.celery_app worker -l info (如果 celery_app 在 main.py 同级)
    ```
3.  **启动 FastAPI 应用:**
    ```bash
    uvicorn main:app --reload
    ```
4.  **访问前端页面。**

**关于“前端给核心代码输送排队信息，核心代码给前端反馈是否已经完成”：**

*   **前端输送排队信息：** 前端提交任务时，Celery会自动将其放入队列。如果想知道具体排队位置，实现起来会复杂一些，通常的做法是返回“排队中”即可。如果确实需要，可以查询队列长度（Broker特定API），但这增加了复杂性。
*   **核心代码反馈完成：**
    *   Celery Worker 在任务完成或失败时，会将其状态和结果（或错误信息）存储到 Result Backend (这里是 Redis)。
    *   FastAPI 的 `/api/task_status/{task_id}` 接口从 Result Backend 读取这个状态，并返回给前端。
    *   前端通过轮询此接口获得更新。

**稳健性 (20人同时在线):**

*   **FastAPI + Uvicorn:** 处理 API 请求并发能力强。
*   **Celery Workers:** 你可以启动多个 Celery worker 进程来并行处理队列中的任务 (`celery -A ... worker -c 4` 启动4个worker)。这样即使单个转录任务很慢，多个任务也可以同时被不同 worker 处理（如果你的核心AI代码和服务器资源允许并行）。
*   **Redis/RabbitMQ:** 作为消息中间件，性能很高，能处理大量任务消息。
*   **瓶颈:**
    *   **AI核心代码的效率和资源消耗：** 如果AI转录本身非常占用CPU/GPU/内存，那么你能同时处理的任务数量将受限于此。
    *   **服务器资源：** CPU、内存、磁盘I/O。
    *   **邮件服务器限制：** 短时间内大量发送邮件可能会被邮件服务器限制。

这个架构将耗时的AI处理与Web请求完全分离，使得前端响应迅速，用户体验更好，并且系统更具伸缩性。前端保持了轻量，主要工作由后端API调度和Celery Worker执行。

-----
好的，下面是这个AI录音转录工具的架构图、代码模块/功能概览、以及数据结构建议。

**一、系统架构图**

```mermaid
graph TD
    subgraph "用户浏览器 (Client)"
        A[前端UI - Vue.js/Vanilla JS]
        A -- HTTP/S --> B
    end

    subgraph "Web 服务器 (Internal Server)"
        B[FastAPI - API网关]
        B -- 任务信息 (JSON) --> C[Celery - 任务队列]
        B -- 文件 --> D[文件存储 (临时/持久)]
        B -- 查询状态 --> E[Redis - Celery Result Backend & Broker]
    end

    subgraph "后台处理 (Internal Server / Worker Nodes)"
        F[Celery Workers (Python)]
        C -- 获取任务 --> F
        F -- 读取文件 --> D
        F -- 调用 --> G[核心AI转录代码 (Python)]
        G -- 转录结果 --> F
        F -- 发送邮件 --> H[邮件服务器 (SMTP)]
        F -- 更新状态/结果 --> E
    end

    A -.-> |1. 用户上传音频, 填写表单| B
    B -.-> |2. 保存音频, 返回File ID| D
    B -.-> |3. (用户点击提交) 创建转录任务, 放入队列, 返回Task ID| C
    A -.-> |4. 定期轮询任务状态 (携带Task ID)| B
    B -.-> |5. 查询Celery任务状态| E
    E -.-> |6. 返回任务状态| B
    B -.-> |7. 返回任务状态给前端| A
    F -.-> |8. (Worker) 执行AI转录| G
    F -.-> |9. (Worker) 发送邮件| H
    F -.-> |10. (Worker) 更新任务最终状态到Redis| E

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bdf,stroke:#333,stroke-width:2px
    style C fill:#ffc,stroke:#333,stroke-width:2px
    style D fill:#ccf,stroke:#333,stroke-width:2px
    style E fill:#fcc,stroke:#333,stroke-width:2px
    style F fill:#9cf,stroke:#333,stroke-width:2px
    style G fill:#cfc,stroke:#333,stroke-width:2px
    style H fill:#ddd,stroke:#333,stroke-width:2px
```

**二、代码模块和功能概览**

1.  **前端 (Client-Side - e.g., Vue.js project)**
    *   **`main.js` / `app.js`**: 应用入口，初始化Vue/Axios等。
    *   **Components:**
        *   **`AudioUploader.vue`**:
            *   功能: 文件拖拽/选择，文件类型/大小校验 (可选)，调用上传API。
            *   状态: 上传进度，上传成功/失败，返回的 `file_id`。
        *   **`EmailForm.vue`**:
            *   功能: "To" 邮箱输入和后缀自动补全/校验，"CC" 邮箱从白名单下拉选择 (多选)，必填校验。
            *   状态: `toEmailsRaw`, `processedToEmails`, `ccWhitelist`, `selectedCcEmails`。
        *   **`TaskList.vue` (或集成到主页面)**:
            *   功能: 展示已提交任务的列表，显示任务ID、状态、进度 (如果提供)、消息。
            *   状态: `tasks` 数组 (包含每个任务的 `id`, `status`, `message` 等)。
        *   **`App.vue` (或主页面组件)**:
            *   功能: 组合上述组件，处理整体提交逻辑 (调用创建任务API)，启动任务状态轮询。
    *   **Services / Utils:**
        *   **`api.js` (或类似)**: 封装 Axios 请求，如 `uploadAudio(file)`, `createTranscriptionTask(data)`, `getTaskStatus(taskId)`。

2.  **后端API (Server-Side - FastAPI project)**
    *   **`main.py` (FastAPI 应用入口)**:
        *   **Endpoints:**
            *   `POST /api/upload_audio`:
                *   功能: 接收音频文件，保存到 `UPLOAD_DIR`，生成唯一 `file_id`，返回 `file_id`。
                *   依赖: `python-multipart`, `os`, `shutil`, `uuid`.
            *   `POST /api/create_transcription_task`:
                *   功能: 接收 `file_id`, `toEmails`, `ccEmails`。校验文件存在性。将转录任务 (包含文件路径和邮件信息) 发送到 Celery 队列。返回 `task_id` 和初始状态。
                *   依赖: Pydantic (用于请求体模型), Celery client。
            *   `GET /api/task_status/{task_id}`:
                *   功能: 根据 `task_id` 查询 Celery 任务的状态和结果 (从 Redis Result Backend)。返回任务的当前状态、消息等。
                *   依赖: Celery client (AsyncResult)。
    *   **`celery_app.py`**:
        *   功能: 初始化和配置 Celery 应用实例 (Broker URL, Result Backend URL)。
    *   **`core_tasks.py` (或 `tasks.py`)**:
        *   功能: 定义 Celery 任务。
        *   **`process_transcription_task(audio_file_path, to_emails, cc_emails)`**:
            *   被 `@celery_app.task` 装饰。
            *   获取音频文件。
            *   调用**核心AI转录代码**。
            *   处理转录结果。
            *   构建邮件内容。
            *   调用邮件发送函数。
            *   (可选) 清理临时文件。
            *   (可选) 更新更细致的任务进度 (通过 `self.update_state`)。
            *   返回结果或抛出异常。
            *   依赖: 你的核心AI库，`smtplib`, `email.mime`。
    *   **`your_core_ai_module.py` (你的核心AI代码模块)**:
        *   功能: 包含实际执行语音转文字的函数，例如 `transcribe(audio_path) -> str`。
        *   依赖: 你的AI模型库 (e.g., `whisper`, `speech_recognition`, `vosk` 等)。
    *   **`utils/email_sender.py` (可选，封装邮件发送逻辑)**:
        *   功能: `send_email(subject, body, to_addrs, cc_addrs, from_addr)` 函数。
        *   依赖: `smtplib`, `email.mime`。

3.  **配置与存储**
    *   **`config.py` (或环境变量)**:
        *   存储: Redis URL, SMTP服务器设置, 上传目录路径, AI模型路径 (如果需要) 等。
    *   **文件存储 (`UPLOAD_DIR`)**:
        *   物理位置: 服务器上的一个目录。
        *   内容: 用户上传的原始音频文件。
        *   管理: 需要考虑定期清理策略，避免磁盘占满。
    *   **Redis**:
        *   作为 Celery Broker: 存储待处理的任务消息。
        *   作为 Celery Result Backend: 存储每个任务的执行状态 (`PENDING`, `STARTED`, `SUCCESS`, `FAILURE`) 和执行结果 (如果成功) 或错误信息 (如果失败)。

**三、数据结构建议**

1.  **文件存储:**
    *   文件名: 建议使用 `uuid + original_filename_suffix` 来保证唯一性并保留原始文件类型，例如 `c5a3e8d0-8b1f-4f7e-9d1c-7b9a0e2d1f4a_meeting_audio.wav`。

2.  **前端 `tasks` 数组中每个任务对象:**
    ```javascript
    {
        id: "celery_task_id_string", // 从后端获取的 Celery Task ID
        originalFileName: "user_uploaded_audio.mp3", // (可选) 用于显示
        fileId: "backend_file_id_string", // 上传后后端返回的文件ID
        toEmails: ["user1@bda.com", "user2@bda.com"], // (可选) 用于显示
        ccEmails: ["manager@bda.com"], // (可选) 用于显示
        status: "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED", // 任务当前状态
        message: "任务正在排队...", // 后端返回的友好提示信息
        submittedAt: "YYYY-MM-DDTHH:mm:ssZ", // (可选) 提交时间戳
        completedAt: "YYYY-MM-DDTHH:mm:ssZ", // (可选) 完成时间戳
        resultPreview: "转录结果的前100个字符...", // (可选) 如果任务成功且有结果预览
        errorDetails: "转录引擎超时" // (可选) 如果任务失败
    }
    ```

3.  **FastAPI 请求体模型 (Pydantic):**
    *   `POST /api/create_transcription_task` 请求体:
        ```python
        class TaskCreationRequest(BaseModel):
            fileId: str
            toEmails: conlist(EmailStr, min_items=1) # 自动校验邮箱格式
            ccEmails: conlist(EmailStr, min_items=1) # 自动校验邮箱格式
        ```
        *这里的 `toEmails` 和 `ccEmails` 已经由前端处理好了后缀。*

4.  **FastAPI 响应体模型 (Pydantic - 可选，但推荐用于文档和一致性):**
    *   `POST /api/upload_audio` 响应:
        ```python
        class UploadResponse(BaseModel):
            file_id: str
            message: str
        ```
    *   `POST /api/create_transcription_task` 响应:
        ```python
        class TaskCreationResponse(BaseModel):
            task_id: str
            status: str # e.g., "QUEUED"
            message: str
        ```
    *   `GET /api/task_status/{task_id}` 响应:
        ```python
        class TaskStatusResponse(BaseModel):
            task_id: str
            status: str # PENDING, PROCESSING, COMPLETED, FAILED
            message: str
            result_preview: Optional[str] = None # 如果完成且有结果
            error_details: Optional[str] = None # 如果失败
        ```

5.  **Celery 任务参数 (传递给 `process_transcription_task`):**
    *   `audio_file_path: str` (服务器上音频文件的绝对路径)
    *   `to_emails: List[str]`
    *   `cc_emails: List[str]`

6.  **Celery 任务结果 (存储在 Redis Result Backend，`process_transcription_task` 的返回值):**
    *   如果成功:
        ```json
        {
            "status_override": "COMPLETED", // 自定义状态，可不写，Celery默认是SUCCESS
            "message": "转录完成并已发送邮件。",
            "transcript_preview": "转录文本的前N个字符..."
            // 任何你想返回给前端查看的信息
        }
        ```
    *   如果失败: Celery 会自动记录异常信息。FastAPI 的状态查询接口会读取这些信息。

7.  **邮件内容:**
    *   标准的邮件文本或 HTML。包含转录结果、原始文件名等信息。

**数据库 (如有):**

在这个设计中，我们主要依赖 **Redis** 作为 Celery 的 Broker 和 Result Backend，它存储了任务队列和任务状态/结果。对于这个工具的核心功能，不一定需要传统的关系型数据库 (如 PostgreSQL, MySQL)。

**如果未来需要扩展，可能会考虑数据库的场景：**

*   **用户账户和权限管理:** 如果需要用户登录、区分不同用户的任务等。
*   **持久化任务历史:** 如果希望长期保存所有任务的详细记录 (不仅仅是 Celery Result Backend 中可能过期的记录)，并进行查询分析。
*   **白名单管理:** 如果 CC 邮箱白名单需要动态管理而不是硬编码或配置文件。
*   **用量统计和审计:** 记录谁在什么时候提交了什么任务。

如果需要这些，可以引入一个轻量级的数据库 (如 SQLite，如果部署简单优先) 或更强大的数据库 (PostgreSQL, MySQL)。届时，`Task` 可能会成为一个数据库表，包含 `task_id` (Celery task ID), `user_id` (if any), `file_name`, `status`, `submitted_at`, `completed_at`, `result_summary` 等字段。但对于当前描述的需求，Redis + 文件系统已经足够。

这个结构清晰地分离了用户交互、API服务、任务调度和后台处理，使得系统易于维护和扩展。

-----
在内网环境下限制网页访问，有多种方法可以实现，从简单配置到更复杂的网络策略都有。以下是一些常见且有效的方法，你可以根据你的具体环境和需求选择：

**1. 部署在内网服务器，不暴露到公网**

*   **核心思路:** 这是最直接也是最安全的方法。将你的 Web 应用 (前端静态文件 + 后端 FastAPI 应用) 部署在一台只拥有内网 IP 地址的服务器上。
*   **实现方法:**
    *   **服务器选择:** 选择一台公司内部网络中的服务器。这台服务器不应该有公网 IP 地址，或者其公网 IP 地址的相应端口（如 80, 443, 或你应用使用的端口）没有在公司防火墙/路由器上做端口映射 (Port Forwarding) 到公网。
    *   **DNS 配置 (可选但推荐):** 在公司内部的 DNS 服务器上，为你的工具分配一个易记的内网域名 (例如 `transcribe-tool.bda.local` 或 `ai-tool.internal.bda.com`)，并将其解析到部署服务器的内网 IP 地址。这样员工就可以通过域名访问，而不是记住 IP。
    *   **应用监听地址:**
        *   **FastAPI (Uvicorn):** 启动 Uvicorn 时，可以指定监听的 IP 地址。
            *   监听特定内网 IP: `uvicorn main:app --host 192.168.1.100 --port 8000` (假设 `192.168.1.100` 是服务器的内网 IP)
            *   监听所有可用网络接口 (包括内网): `uvicorn main:app --host 0.0.0.0 --port 8000`。这种情况下，访问控制主要依赖于服务器本身不暴露到公网。
*   **优点:**
    *   实现简单，安全性高（物理隔离）。
    *   不需要额外的认证配置（如果信任所有内网用户）。
*   **缺点:**
    *   如果服务器意外配置了公网访问或防火墙规则变更，可能会有风险。

**2. 防火墙规则 (网络层面)**

*   **核心思路:** 在公司网络边界的防火墙或部署应用服务器本身的防火墙上配置规则，只允许来自特定内网 IP 地址段的访问。
*   **实现方法:**
    *   **公司边界防火墙:** IT 部门可以在公司的主要防火墙上设置规则，阻止所有来自公网对该应用服务器特定端口的访问请求。
    *   **服务器防火墙 (iptables, firewalld, ufw - Linux; Windows Firewall - Windows):**
        *   配置规则允许来自你公司内网 IP 段 (例如 `192.168.0.0/16` 或 `10.0.0.0/8`) 的流量访问应用的端口 (如 8000)。
        *   拒绝所有其他 IP 地址的访问。
        *   示例 (iptables):
            ```bash
            # 假设内网网段是 192.168.1.0/24，应用端口是 8000
            sudo iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
            sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
            ```
*   **优点:**
    *   提供了网络层面的强访问控制。
*   **缺点:**
    *   需要网络管理员权限或服务器管理员权限进行配置。
    *   如果防火墙规则配置错误，可能导致合法用户无法访问或意外开放访问。

**3. Web 服务器配置 (应用层面 - 例如 Nginx/Apache 反向代理)**

*   **核心思路:** 如果你在 FastAPI 应用前使用 Nginx 或 Apache 作为反向代理和静态文件服务器，可以在这些 Web 服务器的配置中限制访问。
*   **实现方法 (Nginx 示例):**
    ```nginx
    server {
        listen 80;
        server_name transcribe-tool.bda.local; // 你的内网域名

        # 允许的内网 IP 段
        allow 192.168.1.0/24;  // 示例内网段1
        allow 10.10.0.0/16;    // 示例内网段2
        # 拒绝所有其他 IP
        deny all;

        location / {
            proxy_pass http://localhost:8000; // FastAPI 应用地址
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static { # 如果前端静态文件由 Nginx 服务
            alias /path/to/your/frontend/dist;
            try_files $uri $uri/ /index.html;
        }
    }
    ```
*   **优点:**
    *   配置相对灵活，可以在 Web 服务器层面集中管理。
*   **缺点:**
    *   依赖于反向代理的正确配置。如果直接访问后端 FastAPI 应用的端口（且后端未做IP限制），则此限制无效。

**4. 应用内 IP 白名单 (FastAPI 中间件)**

*   **核心思路:** 在 FastAPI 应用中编写一个中间件，检查每个传入请求的来源 IP 地址，如果不在允许的内网 IP 地址列表或网段内，则拒绝请求。
*   **实现方法 (FastAPI 中间件示例):**
    ```python
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    from ipaddress import ip_network, ip_address

    app = FastAPI()

    # 允许的内网 IP 网段列表
    ALLOWED_IP_NETWORKS = [
        ip_network("192.168.1.0/24", strict=False),
        ip_network("10.0.0.0/8", strict=False),
        ip_network("127.0.0.1"), # 允许本地访问
    ]

    @app.middleware("http")
    async def ip_filter_middleware(request: Request, call_next):
        client_host = request.client.host
        client_ip = ip_address(client_host) # 将字符串转换为ip_address对象

        is_allowed = False
        for network in ALLOWED_IP_NETWORKS:
            if client_ip in network:
                is_allowed = True
                break

        if not is_allowed:
            # 可以记录非法访问尝试
            print(f"Forbidden_access from IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied: Your IP address is not allowed."}
            )

        response = await call_next(request)
        return response

    # ... 你的其他 API 路由 ...
    @app.get("/")
    async def read_root():
        return {"message": "Welcome to the Transcription Tool!"}
    ```
*   **优点:**
    *   直接在应用代码中控制，不依赖外部组件。
    *   可以灵活地动态更新允许的 IP 列表 (例如从配置文件读取)。
*   **缺点:**
    *   如果应用部署在反向代理后面，`request.client.host` 可能获取到的是反向代理的 IP。需要确保反向代理正确设置了 `X-Forwarded-For` 或 `X-Real-IP` 头部，并在中间件中读取这些头部来获取真实客户端 IP。
        ```python
        # 在中间件中获取真实 IP (如果使用了反向代理)
        # ...
        real_ip = request.headers.get("x-forwarded-for")
        if real_ip:
            client_host = real_ip.split(',')[0].strip() # 取第一个IP（最原始的客户端IP）
        else:
            client_host = request.client.host
        client_ip = ip_address(client_host)
        # ...
        ```

**5. VPN (虚拟专用网络)**

*   **核心思路:** 要求用户必须连接到公司的 VPN才能访问该工具。VPN 会为用户分配一个内网 IP 地址。
*   **实现方法:**
    *   你的工具部署在内网。
    *   公司已经有 VPN 设施。用户在外网时，需要先连接 VPN。
*   **优点:**
    *   非常安全，将访问控制点放在了 VPN 认证上。
    *   适用于需要远程访问内网资源的场景。
*   **缺点:**
    *   用户多一步操作 (连接VPN)。
    *   依赖公司 VPN 系统的稳定性和可用性。

**组合策略与建议**

通常情况下，推荐采用**多层防御 (Defense in Depth)** 的策略：

1.  **首选和基础：部署在内网服务器，不暴露公网 (方法1)。** 这是最根本的保障。确保服务器的网络配置是纯内网的。
2.  **加固：服务器防火墙规则 (方法2)。** 在服务器层面明确只允许公司内网 IP 段访问应用的端口，即使服务器意外获得了公网 IP，这层防火墙也能提供保护。
3.  **可选的便利性：内部 DNS (方法1的一部分)。**
4.  **如果使用反向代理：在反向代理层面也配置IP限制 (方法3)。** 这可以减轻后端应用的压力。
5.  **应用内 IP 白名单 (方法4)：** 可以作为额外的补充，特别是在无法完全控制服务器防火墙或希望在应用层面有更细致日志记录时。但要注意获取真实客户端IP的问题。

**对于你的场景 "只希望内网环境可以access"，最佳且最简单的组合通常是：**

*   **将应用部署在内网服务器上，该服务器没有公网IP或其端口未映射到公网。**
*   **(可选但推荐) 在该服务器上配置防火墙规则，只允许你公司内网IP段访问应用端口。**
*   **(可选但推荐) 使用内部DNS解析一个友好的域名到该服务器的内网IP。**

这样基本就能满足你的需求了。方法4 (应用内IP白名单) 是一种备选或补充，如果前两者难以完全实施，或者你需要更细粒度的应用日志。方法5 (VPN) 主要适用于员工需要在公司外部安全访问内网资源的情况。

-----
好的，将文件加密这一步整合进工作流确实会对流程产生一些影响，主要是在 Celery Worker 处理任务的环节。我们需要确保在发送邮件附件之前，文件已经被公司的加密系统处理过。

**核心思路调整：**

在 Celery Worker 的 `process_transcription_task` 中，在AI转录完成之后、发送邮件之前，增加一个步骤来触发公司的自动加密机制。

**对工作流的影响和修改：**

1.  **Celery Worker (`core_tasks.py`) 的 `process_transcription_task` 函数需要修改：**

    *   **AI转录后:** 得到转录结果文本。
    *   **创建/修改文件以触发加密:**
        *   **策略一：修改原始音频文件（不推荐，除非你的AI核心代码输出的就是修改后的音频）：** 如果加密系统是针对特定文件类型的，并且你的AI转录过程不改变原始音频文件，这个策略可能不适用。而且修改原始文件可能不是好做法。
        *   **策略二：创建新的文本文件包含转录结果，并对此文本文件进行“编辑”：** 这是更常见和推荐的做法。
            1.  将AI转录得到的文本内容写入一个新的文件 (例如 `transcription_result.txt`)。
            2.  对这个新创建的文本文件执行一个“编辑”操作。
        *   **策略三：如果转录结果本身就是一个文件（比如AI工具直接输出一个DOCX或PDF）：** 直接对这个输出文件进行“编辑”。
    *   **执行“编辑”操作:**
        *   **简单追加:** 在文件末尾追加一个特殊字符或一小段文本 (如你提到的 "`" 或 "Edited for encryption trigger.")。
        *   **程序化编辑:** 使用 Python 的文件操作 (`open`, `write`, `seek`, `read` 等) 来打开文件，进行微小的修改，然后保存并关闭。**关键是这个保存动作能被公司的自动化加密系统捕获到。**
    *   **等待加密完成 (关键点):**
        *   **同步等待 (如果加密很快且可靠):** 如果加密过程非常快 (秒级) 并且是同步的 (即保存后文件立即变为加密状态)，那么可以直接在代码中进行短暂的 `time.sleep()`，然后检查文件是否已加密 (例如，检查文件扩展名是否改变，或者是否有特定的加密标记文件生成)。**但这种方式不够鲁棒。**
        *   **异步监控/轮询 (更可靠):** 如果加密过程需要一些时间，或者其完成状态不直接体现在原文件上，你需要一种机制来监控加密是否完成。
            *   **监控文件变化:** 监控目标文件是否被修改（例如，文件大小变化、修改时间变化、或者被替换为加密版本的文件——通常加密后的文件名或扩展名会改变）。Python 的 `watchdog` 库可以用来监控文件系统事件。
            *   **检查加密标记:** 如果加密系统会在完成后生成一个标记文件 (如 `original_filename.enc.done`) 或改变文件属性，则轮询检查这个标记。
            *   **调用加密系统API (如果提供):** 如果公司的加密系统提供API查询加密状态，那是最好的方式。
        *   **超时机制:** 必须设置一个超时时间，以防加密过程卡住或失败，导致 Celery Worker 无限期等待。
    *   **获取加密后的文件路径:** 加密系统可能会改变文件名或将其移动到特定位置。你需要知道加密后文件的最终路径。
    *   **邮件附件使用加密后的文件:** 在构建邮件时，使用这个加密后的文件作为附件。
    *   **清理:** 原来的未加密文件（如果与加密文件不同）可能需要清理。

**修改后的 Celery Worker 任务伪代码示例 (`core_tasks.py`)：**

```python
from .celery_app import celery_app
# import your_core_ai_module
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.application import MIMEApplication # 用于附件
# from email.mime.multipart import MIMEMultipart
import os
import time
import shutil # 用于文件操作

# 假设这是你的邮件发送函数
def send_email_with_attachment(subject, body, to_addrs, cc_addrs, from_addr, attachment_path=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)
    if cc_addrs:
        msg['Cc'] = ', '.join(cc_addrs)

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=os.path.basename(attachment_path)
            )
        # After the file is closed
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(part)
    
    # ... (smtplib code to send email) ...
    print(f"Email sent with attachment: {attachment_path}")


@celery_app.task(bind=True, max_retries=3) # bind=True, 添加重试机制
def process_transcription_task(self, audio_file_path: str, to_emails: list, cc_emails: list):
    task_id = self.request.id
    base_filename = os.path.splitext(os.path.basename(audio_file_path))[0]
    
    # 临时工作目录，用于存放转录结果和待加密文件
    # 确保这个目录是加密系统会监控和处理的本地路径
    WORK_DIR = "/path/to/local_edit_and_encryption_area" # 【重要】替换为实际路径
    os.makedirs(WORK_DIR, exist_ok=True)
    
    unencrypted_transcript_path = os.path.join(WORK_DIR, f"{base_filename}_transcript.txt")
    # 假设加密后文件名会变成 .encrypted.txt 或类似，或者加密系统会移动它
    # 你需要根据实际情况确定如何找到加密后的文件
    expected_encrypted_filename = f"{base_filename}_transcript.encrypted.txt" # 示例
    encrypted_transcript_path = os.path.join(WORK_DIR, expected_encrypted_filename) # 示例

    try:
        self.update_state(state='PROCESSING', meta={'step': 'transcribing'})
        # 1. 调用核心 AI 代码进行转录
        # transcription_text = your_core_ai_module.transcribe(audio_file_path)
        transcription_text = f"This is the simulated transcription for {audio_file_path}."
        print(f"Task {task_id}: Transcription complete for {audio_file_path}")

        # 2. 将转录结果写入新文件
        with open(unencrypted_transcript_path, "w", encoding="utf-8") as f:
            f.write(transcription_text)
        print(f"Task {task_id}: Unencrypted transcript saved to {unencrypted_transcript_path}")

        # 3. 执行“编辑”操作以触发加密 (简单追加一个字符)
        self.update_state(state='PROCESSING', meta={'step': 'triggering_encryption'})
        with open(unencrypted_transcript_path, "a", encoding="utf-8") as f:
            f.write("`") # 追加一个字符
        print(f"Task {task_id}: Edited unencrypted transcript to trigger encryption.")
        # 此时，假设公司的自动化加密系统会检测到这个文件的变化并开始加密

        # 4. 等待加密完成
        #    【重要】这里的等待和检查机制需要根据你的加密系统特性来定制
        encryption_timeout_seconds = 300 # 例如，5分钟超时
        start_time = time.time()
        encryption_successful = False
        
        print(f"Task {task_id}: Waiting for encryption of {unencrypted_transcript_path}...")
        while time.time() - start_time < encryption_timeout_seconds:
            # 检查加密后的文件是否存在且未被修改 (假设加密完成后文件不再变动)
            # 或检查加密系统特定的标记
            if os.path.exists(encrypted_transcript_path): #【修改】检查加密后的文件
                 # 可选：更严格的检查，比如文件大小稳定一段时间
                print(f"Task {task_id}: Encrypted file found at {encrypted_transcript_path}")
                encryption_successful = True
                break
            time.sleep(5) # 每5秒检查一次

        if not encryption_successful:
            error_msg = f"Task {task_id}: Encryption timed out or failed for {unencrypted_transcript_path}."
            print(error_msg)
            # 可以选择重试任务，或者标记为失败
            # self.retry(exc=Exception(error_msg), countdown=60) # 60秒后重试
            raise Exception(error_msg) # 直接失败

        self.update_state(state='PROCESSING', meta={'step': 'sending_email'})
        # 5. 准备邮件内容
        subject = f"加密的音频转录结果: {os.path.basename(audio_file_path)}"
        body = (f"您好，\n\n音频文件 {os.path.basename(audio_file_path)} 的转录结果已加密，"
                f"并作为附件发送。\n\n{transcription_text[:200]}...\n\n此邮件为自动发送。") # 邮件正文可包含部分预览

        # 6. 发送邮件，附件为加密后的文件
        send_email_with_attachment(subject, body, to_emails, cc_emails, "transcription-tool@bda.com", encrypted_transcript_path)
        print(f"Task {task_id}: Email sent with encrypted attachment: {encrypted_transcript_path}")

        # 7. 清理临时文件 (可选)
        # os.remove(unencrypted_transcript_path) # 如果未加密和加密文件不同名
        # os.remove(encrypted_transcript_path) # 根据策略决定是否删除已发送的附件

        return {"status": "COMPLETED", "message": "转录完成，加密附件已发送邮件。"}

    except Exception as e:
        print(f"Task {task_id}: Error processing - {str(e)}")
        # self.update_state(state='FAILED', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        # 如果使用 bind=True 和 self.retry，Celery 会自动处理重试和最终失败状态
        # 对于不可重试的错误，直接 raise
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1)) if self.request.retries < 2 else e


```

**主要影响和考虑点：**

1.  **Celery Worker 的执行环境：**
    *   Worker 运行的机器/容器**必须**安装并配置好公司的自动化加密客户端/代理，使其能够监控到 Worker 创建和编辑的文件。
    *   Worker 写入文件的**本地路径**必须是加密系统监控的范围。

2.  **加密过程的可靠性和时间：**
    *   **等待机制至关重要：** 如何准确判断加密已完成？这是最容易出问题的地方。你需要和负责加密系统的团队沟通，了解其工作原理：
        *   加密后文件名会变吗？（例如 `file.txt` -> `file.txt.bdaenc`）
        *   加密是原地替换还是生成新文件？
        *   加密完成后是否有状态文件或日志可以查询？
        *   加密过程大致需要多长时间？波动大吗？
    *   **超时处理：** 如果加密失败或超时，任务应该如何处理？重试？标记为失败并通知管理员？
    *   **错误处理：** 如果加密过程中出现错误，Celery 任务需要能捕获并妥善处理。

3.  **文件路径管理：**
    *   需要清楚地知道未加密文件路径、触发编辑后的文件路径、以及最终加密文件的路径。
    *   如果加密系统会将文件移动到特定加密文件夹，逻辑会更复杂。

4.  **性能和资源：**
    *   文件读写操作会增加 I/O 负载。
    *   等待加密的过程会占用 Celery Worker 的处理时间，如果加密慢，会降低整体任务吞吐量。确保有足够的 Worker 和合理的并发设置。

5.  **安全性（尽管是内网）：**
    *   确保 Worker 操作的临时目录权限设置得当。
    *   转录后的未加密文本在加密完成前会短暂存在于磁盘上。

6.  **可配置性：**
    *   加密相关的路径、预期的加密后文件名模式、超时时间等，最好做成可配置的，而不是硬编码。

7.  **测试：**
    *   这个环节需要和加密系统紧密集成测试，确保文件确实被加密，并且后续流程能拿到正确的加密文件。

**对前端的影响：**

*   **基本无直接影响。** 前端仍然是提交任务，然后轮询状态。
*   **任务状态信息可以更丰富：** 后端可以在 `task_status` API 中返回更详细的步骤信息，如 `{"status": "PROCESSING", "message": "正在加密转录结果..."}`。
*   **用户等待时间可能变长：** 因为多了加密步骤，用户感知到的任务完成时间会增加。

**总结：**

引入这个加密步骤，核心的复杂性在于 Celery Worker 如何与公司的自动化加密系统进行可靠的交互（触发、等待、获取结果）。你需要仔细调研加密系统的工作方式，并设计鲁棒的等待和错误处理逻辑。这将使得 Celery 任务的逻辑比之前更长、更复杂。
