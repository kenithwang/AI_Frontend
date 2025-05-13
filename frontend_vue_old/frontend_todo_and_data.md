# AI Audio Memo Tool - Frontend TODOs and Data Structures

## 1. 概述

本文档旨在追踪 `AI_Frontend/frontend_vue/src/App.vue` 组件中尚未完成的功能点，明确各交互元素的实现细节，并定义与后端API交互时所需的数据结构。目前，页面的基本HTML结构和CSS样式已根据初步设计完成。

## 2. 待实现功能及数据说明

以下是需要逐步实现的主要交互功能模块：

### 2.1. 音频文件上传

*   **功能描述**: 用户可以通过拖拽文件到指定区域或点击该区域来选择并上传一个音频文件。上传成功后，应显示文件名。
*   **相关代码位置 (`App.vue`)**:
    *   模板中:
        *   `<div class="upload-section">` 内的 `<div class="drop-area" ...>`
        *   `<!-- TODO: Implement drag & drop functionality and click to upload for this area -->`
        *   `<input type="file" ref="fileInput" ...>` (隐藏的input)
        *   `<div v-if="fileName" class="file-name-display">` (用于显示文件名)
    *   `script` 部分:
        *   `data()`: `fileName: null` (已存在, 用于存储文件名)
        *   `methods`:
            *   `triggerFileInput()`: (已声明) 逻辑需要取消注释并完善，使其能触发 `this.$refs.fileInput.click()`。
                *   `// console.log('Triggering file input...');`
                *   `// this.$refs.fileInput.click();`
            *   `handleFileUpload(event)`: (已声明) 逻辑需要取消注释并完善。
                *   `// const file = event.target.files[0];`
                *   `// if (file) { ... }`
            *   `handleFileDrop(event)`: (已声明) 逻辑需要取消注释并完善。
                *   `// event.preventDefault();`
                *   `// const file = event.dataTransfer.files[0];`
                *   `// if (file && file.type.startsWith('audio/')) { ... }`
*   **实现细节/交互逻辑**:
    1.  **点击上传**:
        *   当用户点击 `div.drop-area` 时，应调用 `triggerFileInput()` 方法。
        *   `triggerFileInput()` 方法内部通过 `this.$refs.fileInput.click()` 以编程方式触发隐藏的 `<input type="file">` 元素的选择文件对话框。
    2.  **拖拽上传**:
        *   `div.drop-area` 需要监听 `@dragover.prevent` 以允许放置，监听 `@drop` 来处理文件放置事件。
        *   当文件被拖拽到 `div.drop-area` 并释放时，`handleFileDrop(event)` 方法被调用。
        *   阻止浏览器的默认行为（如打开文件）。
    3.  **文件处理 (通用逻辑，在 `handleFileUpload` 和 `handleFileDrop` 中)**:
        *   从事件对象中获取文件 (`event.target.files[0]` 或 `event.dataTransfer.files[0]`)。
        *   **验证**: 检查文件类型是否为音频 (e.g., `file.type.startsWith('audio/')`)。如果不是，可以考虑给出提示。
        *   **存储文件**: 将获取到的文件对象（`File` 对象）存储在 Vue 组件的 `data` 属性中（例如，新增一个 `uploadedFile: null`）。
        *   **更新显示**: 将文件名更新到 `this.fileName`，以便在界面上显示。
*   **相关数据 (`App.vue` state)**:
    *   `fileName: String | null` (已存在): 用于在UI上显示已选择/拖拽的文件名。
    *   `uploadedFile: File | null` (建议新增): 用于存储实际的 `File` 对象，该对象将在表单提交时使用。
*   **未来数据交互 (提交时)**:
    *   将 `uploadedFile` 对象作为请求体的一部分（通常使用 `FormData`）发送到后端。

### 2.2. "To" 邮件接收人输入

*   **功能描述**: 用户可以在文本区域输入一个或多个邮件接收人的用户名或邮箱地址。
*   **相关代码位置 (`App.vue`)**:
    *   模板中:
        *   `<div class="form-group">` 内的 `<textarea id="to-emails" v-model="toEmails" ...>`
        *   `<!-- TODO: Add logic to handle 'To' email input, potentially with validation and parsing -->`
    *   `script` 部分:
        *   `data()`: `toEmails: ''` (已存在，通过 `v-model` 双向绑定)
*   **实现细节/交互逻辑**:
    1.  用户直接在文本区域输入。
    2.  (未来/可选) 输入内容变化时，可以进行实时解析（如按逗号、分号或空格分隔多个地址）和基本格式校验。
*   **相关数据 (`App.vue` state)**:
    *   `toEmails: String` (已存在): 存储用户输入的原始字符串。
*   **未来数据交互 (提交时)**:
    *   将 `toEmails` 字符串发送到后端。后端可能需要进一步解析此字符串为接收人列表。
    *   **期望数据结构 (发送给后端时)**:
        *   `to_recipients: String` (e.g., "user1, user2@example.com") 或 `to_recipients: Array<String>` (e.g., `["user1", "user2@example.com"]`)，具体取决于后端API设计。

### 2.3. "Cc" 邮件抄送人输入/选择

*   **功能描述**: 用户可以输入一个或多个抄送人的用户名或邮箱地址。未来可能支持从下拉列表中选择。
*   **相关代码位置 (`App.vue`)**:
    *   模板中:
        *   `<div class="form-group">` 内的 `<textarea id="cc-emails" v-model="ccEmails" ...>`
        *   `<!-- TODO: Add logic for 'Cc' email input. Consider implementing dropdown for suggestions or a multi-select component later. -->`
        *   (可选下拉相关) `<!-- <button class="dropdown-toggle" @click="toggleCcDropdown">&#9660;</button> -->` 和 `<!-- <div v-if="showCcDropdown" class="cc-dropdown-list"> -->`
    *   `script` 部分:
        *   `data()`: `ccEmails: ''` (已存在，通过 `v-model` 双向绑定)
        *   `data()`: `// showCcDropdown: false` (已注释，为未来下拉功能预留)
        *   `methods`: `// toggleCcDropdown()` (已注释，为未来下拉功能预留)
*   **实现细节/交互逻辑**:
    1.  用户直接在文本区域输入。
    2.  (未来/可选) 实现下拉选择功能：
        *   可能需要从API获取建议用户列表。
        *   点击下拉按钮 (`dropdown-toggle`) 或输入框获得焦点时显示下拉列表 (`cc-dropdown-list`)。
        *   从下拉列表中选择用户并添加到 `ccEmails` 中。
*   **相关数据 (`App.vue` state)**:
    *   `ccEmails: String` (已存在): 存储用户输入的原始字符串。
*   **未来数据交互 (提交时)**:
    *   将 `ccEmails` 字符串发送到后端。
    *   **期望数据结构 (发送给后端时)**:
        *   `cc_recipients: String` 或 `cc_recipients: Array<String>`，同 `to_recipients`。

### 2.4. 提交按钮

*   **功能描述**: 用户点击提交按钮，将上传的音频文件和填写的邮件接收人信息发送到后端进行处理。
*   **相关代码位置 (`App.vue`)**:
    *   模板中:
        *   `<div class="submit-section">` 内的 `<button class="submit-button" @click="submitForm">Submit</button>`
        *   `<!-- TODO: Add click handler for submit button to process audio and email information -->`
    *   `script` 部分:
        *   `methods`: `submitForm()` (已声明，大部分逻辑已注释)
            *   `// console.log('Submitting form...');`
            *   `// // TODO: Implement form submission logic:`
            *   `// // 1. Get the actual file data (if stored in data() or from a ref)` (对应 `this.uploadedFile`)
            *   `// // 2. Validate inputs` (e.g., 检查文件是否已上传，To/Cc邮箱是否符合基本格式)
            *   `// // 3. Construct payload for the API`
            *   `// // 4. Make API call to backend`
            *   `// alert('Submit button clicked! (Functionality to be implemented)');`
*   **实现细节/交互逻辑**:
    1.  当用户点击 "Submit" 按钮时，调用 `submitForm()` 方法。
    2.  **获取数据**: 从组件的 `data` 中获取 `this.uploadedFile`、`this.toEmails`、`this.ccEmails`。
    3.  **输入验证**:
        *   检查 `this.uploadedFile` 是否存在 (即用户是否已上传文件)。
        *   检查 `this.toEmails` 是否为空（或根据业务需求进行更复杂的验证）。
        *   `this.ccEmails` 可以是可选的。
        *   如果验证失败，向用户显示错误提示。
    4.  **构建API请求负载**:
        *   通常使用 `FormData` 对象来同时发送文件和文本数据。
        *   将 `this.uploadedFile` 添加到 `FormData`。
        *   将 `this.toEmails` 和 `this.ccEmails` 添加到 `FormData`。
    5.  **发起API调用**: 使用 `axios` 或 `fetch` 将 `FormData` 发送到后端API端点。
    6.  **处理响应**: 根据API的响应（成功/失败）向用户提供反馈（如成功消息、错误提示、清空表单等）。
*   **未来数据交互 (发送给后端)**:
    *   **请求类型**: `POST`
    *   **请求体**: `FormData` 对象
    *   **期望 `FormData` 结构**:
        ```
        formData.append('audio_file', this.uploadedFile);
        formData.append('to_recipients', this.toEmails); // 或者解析后的数组
        formData.append('cc_recipients', this.ccEmails); // 或者解析后的数组
        // 可能还有其他参数，如 processing_options 等
        ```
    *   **后端API端点 (示例)**: `/api/process-audio`
    *   **期望后端响应 (示例)**:
        *   成功: `{"status": "success", "message": "Processing started", "task_id": "xyz123"}`
        *   失败: `{"status": "error", "message": "Invalid input: No audio file provided"}`

## 3. 后续步骤

1.  逐步取消 `App.vue` 中相关方法的注释，并实现其核心逻辑。
2.  为文件上传功能添加 `uploadedFile` 到 `data()`。
3.  实现表单提交时的输入验证。
4.  在 `main.js` 或单独的API服务模块中配置 `axios` (如果尚未使用)，用于API调用。
5.  与后端开发人员确认API端点、确切的请求/响应数据结构。

本文档将随着开发的进展而更新。 