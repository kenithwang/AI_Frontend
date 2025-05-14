<template>
  <div id="app-root">
    <!-- Decorative Background Elements -->
    <div class="decor-shape decor-shape-1"></div>
    <div class="decor-shape decor-shape-2"></div>
    <div class="decor-shape decor-shape-3"></div>

    <header class="app-header">
      <h1>BDA Transcribe Tool</h1>
    </header>

    <main class="main-container">
      <!-- Left Panel: Task Queue -->
      <aside class="task-queue-panel">
        <div class="task-info-area">
          <!-- Content from original task-info-area -->
          <!-- <h2>Active Tasks</h2> (Title hidden by CSS as per image) -->
          <div v-if="isLoadingTasks">Loading tasks...</div>
          <table v-else-if="formattedTasks.length > 0" class="task-table">
            <thead>
              <tr>
                <th>Submitted</th>
                <th>Task ID</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in formattedTasks" :key="task.task_id">
                <td>{{ task.submit_time }}</td>
                <td>{{ task.task_id }}</td>
                <td>{{ task.status }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else>No active tasks in the queue.</p>

          <div v-if="currentFeedback.message" :class="['feedback-message', currentFeedback.type]">
            <strong>Feedback:</strong> {{ currentFeedback.message }}
          </div>
        </div>
      </aside>

      <!-- Right Panel: Form -->
      <section class="form-panel">
        <!-- Audio Upload Section -->
        <div class="form-section upload-section-new">
          <h2 class="section-title">Click to upload your audio</h2>
          <div class="upload-content">
            <div class="drop-area-icon" @click="triggerFileInput" @dragover.prevent @drop="handleFileDrop">
              <span>+</span>
              <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none;" accept=".mp3,.wav,.flac,.ogg,.aac,.m4a,.ipod,.wma">
            </div>
            <div class="audio-types-info">
              <p><u>Enabled audio types</u></p>
              <p>.mp3, .wav, .flac, .ogg, .aac, .m4a (.ipod), .wma</p>
            </div>
          </div>
          <div v-if="fileName" class="file-name-display">Selected file: {{ fileName }}</div>
        </div>

        <!-- Email Configuration Section -->
        <div class="form-section email-config-new">
          <h2 class="section-title">Email address to receive the note</h2>
          
          <div class="email-field-group">
            <label for="to-emails" class="email-label">To</label>
            <div class="input-with-helper">
              <input type="text" id="to-emails" v-model="toEmails" class="email-input-new" placeholder="username">
              <p class="helper-text">Please just input your username, e.g., <strong>ken.wang</strong>.<br>System will append the rest (@bda.com) automatically</p>
            </div>
          </div>

          <div class="email-field-group">
            <label for="cc-emails" class="email-label">Cc</label>
            <div class="input-with-helper">
              <div class="cc-input-container">
                <input type="text" id="cc-emails" ref="ccEmailsInput" v-model="ccEmails" class="email-input-new" placeholder="Select manager/director" @focus="showCcDropdown = true" @blur="handleCcBlur">
                <button type="button" class="cc-dropdown-arrow" @click="toggleCcDropdown" aria-label="Toggle CC suggestions">▼</button>
                <div v-if="showCcDropdown && ccSuggestions.length > 0" class="cc-dropdown-list-new">
                  <div v-for="suggestion in filteredCcSuggestions" :key="suggestion" class="cc-dropdown-item-new" @mousedown="selectCcSuggestion(suggestion)">
                    {{ suggestion }}
                  </div>
                </div>
              </div>
              <p class="helper-text">Please select the manager's/director's email address here. Multiple choices are enabled.</p>
            </div>
          </div>
        </div>

        <!-- Submit Section -->
        <div class="form-section submit-section-new">
          <div class="email-field-group">
            <div class="email-label email-label-placeholder">&nbsp;</div>
            <div class="input-with-helper">
              <div class="submit-button-container">
                <button class="submit-button-new" @click="submitForm">Submit</button>
              </div>
              <div class="helper-text helper-text-placeholder">&nbsp;</div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="app-footer">
      <span class="copyright">© BDA 2025</span>
      <div class="bda-logo">bda</div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      toEmails: '',
      ccEmails: '',
      fileName: null,
      uploadedFile: null,
      tasks: [], 
      isLoadingTasks: false,
      currentFeedback: { message: null, type: null }, 
      pollingInterval: null,
      feedbackTimeout: null,
      showCcDropdown: false,
      ccSuggestions: [
        'bing.yin@bda.com',
        'hualiang.guo@bda.com',
        'jinglei.chen@bda.com',
        'ken.wang@bda.com',
        'lantian.li@bda.com',
        'lei.shi@bda.com',
        'leo.cao@bda.com',
        'lingqi.liu@bda.com',
        'liou.liu@bda.com',
        'matthew.deng@bda.com',
        'meiqin.fang@bda.com',
        'wilbur.zou@bda.com',
        'yan.wang@bda.com'
      ], 
    };
  },
  computed: {
    filteredCcSuggestions() {
      if (!this.ccEmails) {
        return this.ccSuggestions;
      }
      const currentTyped = this.ccEmails.split(';').pop().trim().toLowerCase();
      if (!currentTyped) {
          return this.ccSuggestions;
      }
      return this.ccSuggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(currentTyped)
      );
    },
    formattedTasks() {
      const statusMap = {
        submitted: '已提交',
        processing_audio_split: '切分音频',
        transcribing: '转录中',
        generating_wordforword: '生成逐字稿',
        generating_memo_draft: '纪要初稿',
        generating_document: '终版纪要',
        completed: '任务完成',
        failed: '任务失败',
        // You might want to keep a general 'processing' if the backend ever sends it
        // or remove it if all states are now more granular.
        // processing: '处理中' // Example if you still need a generic processing state
      };
      return this.tasks.map(task => ({
        ...task,
        submit_time: this.formatDateToGMT8(task.submit_time),
        status: statusMap[task.status.toLowerCase()] || task.status // Use toLowerCase() for robustness
      }));
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.fileName = file.name;
        this.uploadedFile = file;
      }
    },
    handleFileDrop(event) {
      event.preventDefault();
      const file = event.dataTransfer.files[0];
      const allowedTypes = ['.mp3','.wav','.flac','.ogg','.aac','.m4a','.ipod','.wma'];
      const fileExtension = "." + file.name.split('.').pop().toLowerCase();

      if (file && allowedTypes.includes(fileExtension)) {
        this.fileName = file.name;
        this.uploadedFile = file;
      } else {
        this.currentFeedback = { message: `Invalid file type dropped. Please drop an audio file of type: ${allowedTypes.join(', ')}.`, type: 'error' };
        this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5000);
        this.fileName = null;
        this.uploadedFile = null;
      }
    },
    validateEmails(emailsString) {
      if (!emailsString) return [];
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const emails = emailsString.split(';').map(e => e.trim()).filter(e => e);
      const invalidEmails = [];
      for (const email of emails) {
        if (!emailRegex.test(email) || !email.endsWith('@bda.com')) {
          invalidEmails.push(email);
        }
      }
      return [...new Set(invalidEmails)]; // 返回不重复的无效邮箱列表
    },
    submitForm() {
      if (!this.uploadedFile) {
        this.currentFeedback = { message: 'Please select an audio file first.', type: 'error' };
        this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5000);
        return;
      }

      // Process "To" emails: allow usernames, append @bda.com if necessary
      const toUsernamesOrEmails = this.toEmails.split(';').map(u => u.trim()).filter(u => u);
      if (toUsernamesOrEmails.length === 0) {
        this.currentFeedback = { message: 'Please enter at least one recipient in the "To" field.', type: 'error' };
        this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5000);
        return;
      }
      const processedToEmails = toUsernamesOrEmails.map(entry => {
        return entry.includes('@') ? entry : `${entry}@bda.com`;
      }).join(';');
      
      const invalidToEmails = this.validateEmails(processedToEmails);
      if (invalidToEmails.length > 0) {
        this.currentFeedback = { message: `收件人邮箱无效: ${invalidToEmails.join(', ')}。请确保用户名有效或邮箱地址正确，且所有邮箱必须以 @bda.com 结尾。`, type: 'error' };
        this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5000);
        return;
      }

      // Process "Cc" emails: expect full emails from dropdown or manual entry
      const ccEmailsArray = this.ccEmails.split(';').map(e => e.trim()).filter(e => e);
       if (ccEmailsArray.length === 0) { // Check if Cc field is empty
        this.currentFeedback = { message: 'The "Cc" field cannot be empty. Please select a manager/director.', type: 'error' };
        this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5000);
        return;
      }
      const invalidCcEmails = this.validateEmails(this.ccEmails);
      if (invalidCcEmails.length > 0) {
        this.currentFeedback = { message: `抄送邮箱无效: ${invalidCcEmails.join(', ')}。所有邮箱必须以 @bda.com 结尾。`, type: 'error' };
        this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5000);
        return;
      }
      
      const formData = new FormData();
      formData.append('file', this.uploadedFile);
      formData.append('to_email', processedToEmails); 
      formData.append('cc_emails', this.ccEmails);
      
      console.log('Form Data Prepared:');
      for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value instanceof File ? value.name : value}`);
      }
      
      this.currentFeedback = { message: 'Submitting task...', type: 'info' };

      fetch('/api/transcribe', {
        method: 'POST', 
        body: formData 
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(err => { throw new Error(err.detail || `HTTP error! status: ${response.status}`) });
          }
          return response.json();
        })
        .then(data => {
          console.log('API Response:', data);
          if (data.task_id) {
            this.handleNewTaskFeedback(data.task_id, `Task submitted successfully (ID: ${data.task_id}). Waiting for processing...`);
          } else {
            this.handleNewTaskFeedback(null, data.message || 'Submission successful, but no task ID returned.');
          }
          this.fetchTasks();
          this.fileName = null;
          this.uploadedFile = null;
          this.toEmails = '';
          this.ccEmails = '';
        })
        .catch(error => {
          console.error('API Error:', error);
          this.currentFeedback = { message: `Submission Error: ${error.message}`, type: 'error' };
          this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 5 * 60 * 1000);
        });
    },

    async fetchTasks() {
        this.isLoadingTasks = true;
        console.log('Fetching tasks from /api/tasks...');
        try {
            const response = await fetch('/api/tasks');
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            const responseData = await response.json(); // responseData is TaskListResponse { tasks: [] }
            
            if (responseData && Array.isArray(responseData.tasks)) {
                // Backend already filters for active tasks and sorts them by submission time.
                // We just take the list from responseData.tasks.
                this.tasks = responseData.tasks.slice(0, 20); // Keep the slice for limiting display if needed
                console.log('Tasks updated from API (/api/tasks):', this.tasks);
            } else {
                console.warn('/api/tasks did not return the expected structure:', responseData);
                this.tasks = []; // Default to empty or handle as an error
            }
        } catch (error) {
            console.error('Failed to fetch tasks:', error);
            this.currentFeedback = { message: `Error fetching tasks: ${error.message}`, type: 'error' };
            if (!this.feedbackTimeout) {
                 this.feedbackTimeout = setTimeout(() => this.clearCurrentFeedback(), 10000);
            }
        } finally {
            this.isLoadingTasks = false;
        }
    },
    handleNewTaskFeedback(taskId, initialMessage) { 
        console.log(`Feedback process for task ${taskId}`);
        this.clearCurrentFeedback(); 
        this.currentFeedback = {
            message: initialMessage || (taskId ? `Task (${taskId}) submitted. Monitoring status.` : 'Task submission processed.'),
            type: 'info'
        };
    },
    clearCurrentFeedback() {
        if (this.feedbackTimeout) {
            clearTimeout(this.feedbackTimeout);
            this.feedbackTimeout = null;
        }
        this.currentFeedback = { message: null, type: null };
    },
    formatDateToGMT8(isoString) {
      if (!isoString) return 'Invalid Date';
      try {
        const date = new Date(isoString);
        // Create a new Date object representing GMT+8 time
        // getTimezoneOffset() returns the difference in minutes between UTC and local time.
        // We want UTC time + 8 hours * 60 minutes
        const offsetMinutes = date.getTimezoneOffset();
        const gmt8Timestamp = date.getTime() + (offsetMinutes * 60 * 1000) + (8 * 60 * 60 * 1000);
        const gmt8Date = new Date(gmt8Timestamp);

        const year = gmt8Date.getFullYear();
        const month = String(gmt8Date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
        const day = String(gmt8Date.getDate()).padStart(2, '0');
        const hours = String(gmt8Date.getHours()).padStart(2, '0');
        const minutes = String(gmt8Date.getMinutes()).padStart(2, '0');
        const seconds = String(gmt8Date.getSeconds()).padStart(2, '0');

        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
      } catch (e) {
        console.error("Error formatting date:", e);
        return 'Invalid Date'; // Return fallback string on error
      }
    },
    toggleCcDropdown() {
      this.showCcDropdown = !this.showCcDropdown;
       if (this.showCcDropdown) {
        this.$nextTick(() => {
          if (this.$refs.ccEmailsInput) { // Check if ref is available
            this.$refs.ccEmailsInput.focus();
          }
        });
      }
    },
    selectCcSuggestion(suggestion) {
      const emailParts = this.ccEmails.split(';').map(s => s.trim()).filter(s => s.length > 0);
      
      // Check if the suggestion is already in the list
      if (emailParts.includes(suggestion)) {
          this.showCcDropdown = false; // Just close dropdown if already selected
          return;
      }

      let currentLastPart = this.ccEmails.split(';').pop().trim();
      if (currentLastPart && this.ccSuggestions.some(s => s.toLowerCase().startsWith(currentLastPart.toLowerCase()))) {
          // If user was typing and it matches start of a suggestion, replace that typed part
          emailParts.pop(); // Remove the partially typed part
          emailParts.push(suggestion);
      } else {
          emailParts.push(suggestion);
      }
      
      this.ccEmails = emailParts.join('; ');
      if (this.ccEmails.length > 0 && !this.ccEmails.endsWith('; ')) {
          this.ccEmails += '; '; 
      }
      
      this.showCcDropdown = false;
      this.$nextTick(() => { 
          if(this.$refs.ccEmailsInput) this.$refs.ccEmailsInput.focus(); 
      });
    },
    handleCcBlur() {
      setTimeout(() => {
        this.showCcDropdown = false;
      }, 150);
    }
  },
  mounted() {
    this.fetchTasks(); 
    this.pollingInterval = setInterval(this.fetchTasks, 5000); 
  },
  unmounted() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    this.clearCurrentFeedback();
  }
}
</script>

<style>
/* Global styles for the application */
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #F0F3F4; 
  color: #333333;
  overflow-x: hidden;
}

#app-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 30px 40px; 
  box-sizing: border-box;
  position: relative; 
}

/* Decorative Background Shapes */
.decor-shape {
  position: absolute;
  z-index: 0; /* Behind content */
  opacity: 0.9;
  pointer-events: none; /* Make them non-interactive */
}

/* MODIFIED: Decorative shapes smaller and repositioned */
.decor-shape-1 { /* Teal like */
  width: 24vw; /* MODIFIED from 30vw */
  min-width: 200px; /* MODIFIED from 250px */
  max-width: 330px; /* MODIFIED from 450px */
  height: 24vw; /* MODIFIED from 30vw */
  min-height: 200px; /* MODIFIED from 250px */
  max-height: 330px; /* MODIFIED from 450px */
  background-color: #3FA9A4;
  top: -60px; /* MODIFIED from -50px */
  right: 15px; /* MODIFIED from 30px */
  transform: rotate(45deg) skew(-20deg, -10deg);
  clip-path: polygon(0% 0%, 100% 20%, 80% 100%, 20% 80%);
}
.decor-shape-2 { /* Green like */
  width: 22vw; /* MODIFIED from 28vw */
  min-width: 180px; /* MODIFIED from 200px */
  max-width: 300px; /* MODIFIED from 400px */
  height: 22vw; /* MODIFIED from 28vw */
  min-height: 180px; /* MODIFIED from 200px */
  max-height: 300px; /* MODIFIED from 400px */
  background-color: #82A454;
  top: 30px;  /* MODIFIED from 100px */
  right: 60px; /* MODIFIED from -20px (more to the left) */
  transform: rotate(25deg) skew(15deg, 5deg);
  clip-path: polygon(20% 0%, 80% 10%, 100% 70%, 0% 100%);
}
.decor-shape-3 { /* Yellow like */
  width: 25vw; /* MODIFIED from 33vw */
  min-width: 230px; /* MODIFIED from 280px */
  max-width: 370px; /* MODIFIED from 500px */
  height: 25vw; /* MODIFIED from 33vw */
  min-height: 230px; /* MODIFIED from 280px */
  max-height: 370px; /* MODIFIED from 500px */
  background-color: #FBC13A;
  top: 60px;  /* MODIFIED from 30px */
  right: 110px; /* MODIFIED from 120px */
  transform: rotate(-30deg) skew(5deg, 15deg);
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
}


.app-header h1 {
  font-size: 28px;
  color: #333333;
  margin: 0 0 10px 0;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 5px solid #82A454; 
  display: inline-block; 
  position: relative; /* For z-index if needed */
  z-index: 1;
}

.main-container {
  display: flex;
  flex-grow: 1;
  gap: 40px; /* MODIFIED from 30px - to shift right panel rightwards */
  margin-top: 20px;
  position: relative; /* For z-index if needed */
  z-index: 1;
}

.task-queue-panel {
  flex: 0 0 30%; /* MODIFIED from 28% - to shift right panel rightwards */
  background-color: #FFFFFF;
  border: 1px solid #82A454; 
  border-radius: 0; 
  padding: 20px;
  box-sizing: border-box;
  min-height: 500px; 
  max-height: 70vh; /* Limit height and allow scroll */
  overflow-y: auto; 
}

.task-queue-panel .task-info-area {
  margin-top: 0;
  padding: 0;
  border: none;
  background-color: transparent;
}
.task-queue-panel .task-info-area h2 { /* Original "Active Tasks" title */
  display: none; 
}
.task-queue-panel .task-table {
  font-size: 0.9em;
  width: 100%;
  border-collapse: collapse;
}
.task-queue-panel .task-table th,
.task-queue-panel .task-table td {
  border: 1px solid #e0e0e0;
  padding: 6px 8px;
  text-align: left;
  word-break: break-word;
}
.task-queue-panel .task-table th {
  background-color: #f8f8f8;
  font-weight: 600;
}


.form-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 35px; /* Increased space between form sections */
}

.form-section {
  /* Common styling for form sections if any */
}

.section-title {
  font-size: 18px; 
  font-weight: 600;
  margin-bottom: 15px;
  color: #333333;
}

.upload-section-new .upload-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.drop-area-icon {
  width: 60px;
  height: 60px;
  border: 2px solid #82A454;
  border-radius: 4px; /* Slightly rounded as in image */
  display: flex;
  justify-content: center;
  align-items: center;
  color: #82A454;
  font-size: 36px;
  font-weight: 300; /* Lighter plus sign */
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0; /* Prevent shrinking */
}
.drop-area-icon:hover {
  background-color: #e9f5e9;
}

.audio-types-info p {
  margin: 0 0 5px 0;
  font-size: 0.9em;
  color: #555555;
  line-height: 1.4;
}
.audio-types-info u { /* Only for "Enabled audio types" */
  font-weight: bold;
  text-decoration: underline;
  color: #333;
}
.audio-types-info p:not(:first-child) u { /* Remove accidental underlines */
    text-decoration: none;
    font-weight: normal;
}

.file-name-display {
  margin-top: 10px;
  font-style: italic;
  color: #333;
  font-size: 0.9em;
}

.email-config-new .email-field-group {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 20px;
}

.email-label {
  width: 35px; 
  font-weight: bold;
  padding-top: 8px; 
  font-size: 1.1em;
  color: #333333;
  flex-shrink: 0;
}

.input-with-helper {
  flex-grow: 1;
  display: flex;
  gap: 15px; 
  align-items: flex-start;
  /* flex-wrap: wrap; Allow helper text to wrap if not enough space */
}

.email-input-new {
  /* flex-grow: 1; Will be handled by cc-input-container or itself */
  width: 100%; /* Take full width of its container */
  box-sizing: border-box; /* Include padding and border in width */
  padding: 10px;
  border: 1px solid #82A454;
  border-radius: 0; 
  font-size: 1em;
  background-color: #FFFFFF;
  /* min-width: 200px; */ /* Let flexbox decide */
}
.input-with-helper > .email-input-new { /* Direct child input */
    flex-basis: 250px; /* Give it a base size */
    flex-grow: 1;
    max-width: 400px; /* Prevent it from becoming too wide */
}

.email-input-new:focus {
  outline: none;
  border-color: #5e7c3b; 
  box-shadow: 0 0 0 2px rgba(130, 164, 84, 0.2);
}

.helper-text {
  font-size: 0.8em;
  color: #505050;
  margin: 0;
  line-height: 1.4;
  flex-basis: 200px; /* Give it a base size */
  flex-grow: 1;
  /* max-width: 250px; */ /* Adjust as needed */
  padding-top: 2px; 
}
.helper-text strong {
  color: #000000; 
}

.cc-input-container {
  position: relative;
  display: flex;
  flex-grow: 1; 
  flex-basis: 250px; /* Give it a base size */
  max-width: 400px; /* Prevent it from becoming too wide */
}
.cc-input-container .email-input-new {
  padding-right: 30px; 
}

.cc-dropdown-arrow {
  position: absolute;
  right: 1px; 
  top: 1px; 
  bottom: 1px; 
  width: 28px;
  border: none;
  background-color: transparent; 
  color: #82A454; 
  cursor: pointer;
  font-size: 14px; 
  display: flex;
  align-items: center;
  justify-content: center;
}
.cc-dropdown-arrow:hover {
  color: #5e7c3b;
}

.cc-dropdown-list-new {
  position: absolute;
  top: 100%; 
  left: 0;
  right: 0;
  background-color: white;
  border: 1px solid #82A454;
  border-top: none;
  z-index: 1000;
  max-height: 150px;
  overflow-y: auto;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.cc-dropdown-item-new {
  padding: 8px 10px;
  cursor: pointer;
  font-size: 0.9em;
}
.cc-dropdown-item-new:hover {
  background-color: #e9f5e9;
}

.submit-section-new .email-field-group {
  margin-bottom: 0;
}

.email-label-placeholder,
.helper-text-placeholder {
  visibility: hidden;
}

.submit-button-new {
  background-color: #82A454;
  color: white;
  padding: 10px 25px;
  border: none;
  border-radius: 0; 
  cursor: pointer;
  font-size: 1em;
  font-weight: bold;
  transition: background-color 0.2s;
}
.submit-button-new:hover {
  background-color: #5e7c3b; 
}

.submit-button-container {
  display: flex; /* ADDED: to enable justify-content */
  justify-content: flex-end; /* This will push the button to the right */
  flex-basis: 250px;
  flex-grow: 1;
  max-width: 400px; /* This should align with the input fields' max-width */
}

.app-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto; 
  padding-top: 20px;
  border-top: 1px solid #D5D8DC; 
  color: #555555;
  position: relative; /* For z-index if needed */
  z-index: 1;
}
.copyright {
  font-size: 0.9em;
}
.bda-logo {
  width: 60px;
  height: 60px;
  background-color: #386641; 
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 22px;
  font-weight: bold;
  border-radius: 0; 
}

.feedback-message {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px; 
  color: #fff;
  font-size: 0.9em;
}
.feedback-message.success { background-color: #4CAF50; }
.feedback-message.error { background-color: #f44336; }
.feedback-message.info { background-color: #2196F3; }

/* Media query for smaller screens if needed */
@media (max-width: 900px) {
  #app-root {
    padding: 20px;
  }
  .main-container {
    flex-direction: column;
    gap: 20px; /* Adjust gap for column layout */
  }
  .task-queue-panel {
    flex: 1 1 auto; /* Allow it to grow and shrink */
    min-height: 200px; /* Adjust for smaller view */
    max-height: 40vh;
    flex-basis: auto; /* Reset flex-basis for column layout */
  }
  .input-with-helper {
    flex-direction: column;
    align-items: stretch; /* Make input and helper full width */
  }
  .input-with-helper > .email-input-new,
  .input-with-helper .cc-input-container,
  .input-with-helper .submit-button-container { /* ADDED .submit-button-container here */
    max-width: none; /* Allow full width in column layout */
  }
  .helper-text {
    flex-basis: auto;
    margin-top: 5px;
  }
  /* Optional: Adjust decor shapes further or hide on small screens */
  .decor-shape-1 { top: -40px; right: 5px; width: 30vw; max-width: 200px; height: 30vw; max-height: 200px;}
  .decor-shape-2 { top: 10px; right: 30px; width: 28vw; max-width: 180px; height: 28vw; max-height: 180px;}
  .decor-shape-3 { top: 30px; right: 50px; width: 32vw; max-width: 220px; height: 32vw; max-height: 220px;}
}
@media (max-width: 600px) {
    .app-header h1 {
        font-size: 22px;
    }
    .section-title {
        font-size: 16px;
    }
    .decor-shape {
        display: none; /* Hide decor on very small screens */
    }
    .app-footer {
        flex-direction: column;
        gap: 10px;
    }
}

</style>