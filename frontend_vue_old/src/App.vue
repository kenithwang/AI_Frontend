<template>
  <!-- 
    File: AI_Frontend/frontend_vue/src/App.vue
    Purpose: Root Vue component. Sets up the main layout of the application.
             May include a router-view if Vue Router is used for navigation.
    Interactions:
      - Acts as the main container for other views/components.
      - If using Vue Router, <router-view /> will render the component for the current route.
      - Might import and use global components like a Navbar or Footer.
  -->
  <div id="app-container">
    <h1>AI Audio Memo Tool</h1>

    <!-- Audio Upload Section -->
    <div class="upload-section">
      <!-- TODO: Implement drag & drop functionality and click to upload for this area -->
      <div class="drop-area" @click="triggerFileInput" @dragover.prevent @drop="handleFileDrop">
        <span>+</span>
        <p>Drag & Drop your audio file here or click to select</p>
        <!-- Hidden file input, to be triggered programmatically -->
        <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none;" accept="audio/*">
      </div>
      <!-- Display selected file name -->
      <div v-if="fileName" class="file-name-display">Selected file: {{ fileName }}</div>
    </div>

    <!-- Email Configuration Section -->
    <div class="email-config-section">
      <div class="form-group">
        <label for="to-emails">To:</label>
        <!-- TODO: Add logic to handle 'To' email input, potentially with validation and parsing -->
        <textarea id="to-emails" v-model="toEmails" class="email-input" placeholder="Enter recipient usernames or email addresses, separated by commas"></textarea>
      </div>

      <div class="form-group">
        <label for="cc-emails">Cc:</label>
        <div class="cc-input-group">
          <!-- TODO: Add logic for 'Cc' email input. Consider implementing dropdown for suggestions or a multi-select component later. -->
          <textarea id="cc-emails" v-model="ccEmails" class="email-input" placeholder="Enter Cc usernames or email addresses, separated by commas"></textarea>
          <!-- Placeholder for a dropdown toggle, if we implement a custom dropdown later -->
          <!-- <button class="dropdown-toggle" @click="toggleCcDropdown">&#9660;</button> -->
        </div>
        <!-- TODO: If implementing a dropdown, its content would go here -->
        <!-- <div v-if="showCcDropdown" class="cc-dropdown-list"> -->
          <!-- Dropdown items -->
        <!-- </div> -->
      </div>
    </div>

    <!-- Submit Section -->
    <div class="submit-section">
      <!-- TODO: Add click handler for submit button to process audio and email information -->
      <button class="submit-button" @click="submitForm">Submit</button>
    </div>

  </div>
</template>

<script>
// import HomePage from './views/HomePage.vue'; // Uncomment if not using router-view

export default {
  name: 'App',
  components: {
    // HomePage // Uncomment if not using router-view
  },
  data() {
    return {
      toEmails: '',
      ccEmails: '',
      fileName: null, // To store and display the name of the uploaded file
      // showCcDropdown: false, // For potential CC dropdown functionality
    };
  },
  methods: {
    // Placeholder for triggering file input click
    triggerFileInput() {
      // This method will be called when the drop-area is clicked
      // It programmatically clicks the hidden file input element
      // console.log('Triggering file input...');
      // this.$refs.fileInput.click(); 
      // Commenting out direct DOM manipulation for now, will revisit when implementing full interactivity
    },
    // Placeholder for handling file selection via file input
    handleFileUpload(event) {
      // This method will be called when a file is selected through the file input
      // const file = event.target.files[0];
      // if (file) {
      //   this.fileName = file.name;
      //   console.log('File selected:', file.name);
      //   // TODO: Store the file object itself if needed for immediate processing or preview
      // }
      // Commenting out file handling logic for now
    },
    // Placeholder for handling file drop
    handleFileDrop(event) {
      // This method will be called when a file is dragged and dropped onto the drop-area
      // event.preventDefault(); // Prevent default browser behavior (opening the file)
      // const file = event.dataTransfer.files[0];
      // if (file && file.type.startsWith('audio/')) {
      //   this.fileName = file.name;
      //   console.log('File dropped:', file.name);
      //   // TODO: Store the file object
      // } else {
      //   console.log('Invalid file type dropped. Please drop an audio file.');
      //   // Optionally, provide user feedback about invalid file type
      // }
      // Commenting out file handling logic for now
    },
    // Placeholder for submit action
    submitForm() {
      // This method will be called when the submit button is clicked
      // console.log('Submitting form...');
      // console.log('To:', this.toEmails);
      // console.log('Cc:', this.ccEmails);
      // console.log('File Name:', this.fileName);
      // // TODO: Implement form submission logic:
      // // 1. Get the actual file data (if stored in data() or from a ref)
      // // 2. Validate inputs
      // // 3. Construct payload for the API
      // // 4. Make API call to backend
      // alert('Submit button clicked! (Functionality to be implemented)');
    },
    // toggleCcDropdown() {
      // For potential CC dropdown functionality
      // this.showCcDropdown = !this.showCcDropdown;
    // }
  }
  // mounted() {
  //   console.log("App.vue mounted");
  // }
}
</script>

<style>
/* Global styles for the application */
#app-container {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
  max-width: 700px; /* Adjusted width for better layout */
  margin-left: auto;
  margin-right: auto;
  padding: 25px;
  border: 1px solid #e0e0e0; /* Lighter border */
  border-radius: 10px; /* Softer corners */
  box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Softer shadow */
  background-color: #ffffff;
}

h1 {
  color: #333;
  margin-bottom: 35px;
  font-size: 2em; /* Larger title */
}

.upload-section {
  margin-bottom: 30px; /* Increased spacing */
}

.drop-area {
  border: 2px dashed #4CAF50; /* Green dashed border */
  border-radius: 8px;
  padding: 40px 20px; /* Increased padding for a larger drop zone */
  cursor: pointer;
  background-color: #f9f9f9;
  transition: background-color 0.3s ease, border-color 0.3s ease;
  display: flex; /* For centering content */
  flex-direction: column; /* Stack items vertically */
  align-items: center; /* Center horizontally */
  justify-content: center; /* Center vertically */
  min-height: 150px; /* Minimum height */
}

.drop-area:hover {
  background-color: #e9f5e9; /* Lighter green on hover */
  border-color: #388E3C; /* Darker green border on hover */
}

.drop-area span {
  font-size: 48px; /* Plus sign */
  color: #4CAF50;
  display: block;
  margin-bottom: 10px;
}

.drop-area p {
  margin: 0;
  color: #555;
  font-size: 1em;
}

.file-name-display {
  margin-top: 10px;
  font-style: italic;
  color: #333;
}

.email-config-section {
  margin-bottom: 30px; /* Increased spacing */
  text-align: left;
}

.form-group {
  margin-bottom: 20px; /* Increased spacing */
}

.form-group label {
  display: block;
  margin-bottom: 8px; /* Increased spacing */
  font-weight: bold;
  color: #333;
  font-size: 1.05em;
}

.email-input {
  width: calc(100% - 22px); /* Account for padding and border */
  padding: 12px; /* Increased padding */
  border: 1px solid #4CAF50; /* Green border */
  border-radius: 6px; /* Softer corners */
  font-size: 16px;
  min-height: 60px;
  resize: vertical;
  background-color: #fff; /* Explicit white background */
  color: #333;
}

.email-input:focus {
  outline: none;
  border-color: #388E3C; /* Darker green on focus */
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2); /* Subtle focus ring */
}


.cc-input-group {
  display: flex;
  align-items: center;
}

.cc-input-group .email-input {
  flex-grow: 1;
}

/* Placeholder for CC dropdown toggle button styling */
/*
.dropdown-toggle {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 12px;
  margin-left: 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.dropdown-toggle:hover {
  background-color: #45a049;
}
*/

.submit-section {
  margin-top: 35px; /* Increased spacing */
  text-align: center; /* Center the button */
}

.submit-button {
  background-color: #4CAF50; /* Green background */
  color: white;
  padding: 14px 30px; /* Larger button */
  border: none;
  border-radius: 6px; /* Softer corners */
  cursor: pointer;
  font-size: 18px;
  font-weight: bold;
  transition: background-color 0.3s ease, transform 0.1s ease;
}

.submit-button:hover {
  background-color: #45a049; /* Darker green on hover */
  transform: translateY(-1px); /* Slight lift on hover */
}

.submit-button:active {
  transform: translateY(0px); /* Button press effect */
}
</style> 