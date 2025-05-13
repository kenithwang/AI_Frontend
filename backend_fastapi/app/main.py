from dotenv import load_dotenv # Added for .env support
import os # Ensure os is imported early if not already

# Load environment variables from .env file
# This should be one of the first things to run
# It will search for a .env file in the current directory or parent directories.
# Given your structure and where uvicorn is likely run (from backend_fastapi/), 
# it should find backend_fastapi/.env
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException, Depends, BackgroundTasks # Added BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel # Ensure BaseModel is imported
import logging
import uuid
import shutil
from typing import Optional, Dict, List
from datetime import datetime
from .db import SessionLocal, Task # Assuming db.py defines SessionLocal and Task model correctly
from sqlalchemy.orm import Session
import json
import smtplib # For email
from email.mime.text import MIMEText # For email
from email.mime.multipart import MIMEMultipart # For email
from email.header import Header # For email
from email.utils import formataddr # For email
from email.mime.application import MIMEApplication # For attaching files


# Assuming db.py defines SessionLocal and Task model correctly
# from .db import SessionLocal, Task # Already imported

# --- Import refactored audio2memo functions --- 
# (Adjust paths if your structure differs slightly, e.g., no 'app' prefix if main.py is inside 'app')
try:
    from .audio2memo import process_audio
    from .audio2memo import audio2text
    from .audio2memo import text_to_wordforword
    from .audio2memo import wordforword_to_memo
    from .audio2memo import combine_to_docx
    # funcs module might not be needed directly if others import it
except ImportError as e:
    logging.error(f"Failed to import audio2memo modules: {e}. Ensure they exist and paths are correct.")
    # Depending on setup, you might want to exit or raise an error here
    process_audio = audio2text = text_to_wordforword = wordforword_to_memo = combine_to_docx = None

app = FastAPI()

# 日志配置
logging.basicConfig(filename='transcribe.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Load AUDIO_TARGET_DIR from environment variable
# It will be checked for validity within the transcribe endpoint.
AUDIO_TARGET_DIR = os.environ.get("AUDIO_TARGET_DIR")
if not AUDIO_TARGET_DIR:
    logging.warning("AUDIO_TARGET_DIR environment variable is not set. The application will fail if a task is submitted unless this is configured correctly.")
    # No default value is set here; the transcribe function must handle the missing configuration.

# --- Load Mail Configuration from Environment --- 
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_SMTP_SERVER = os.environ.get("MAIL_SMTP_SERVER")
MAIL_SMTP_PORT = os.environ.get("MAIL_SMTP_PORT", "587") # Default to 587 if not set
MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME", "Audio2Memo Notification")

# --- Define paths for prompts and template --- 
# Assuming main.py is in the 'app' directory, and audio2memo is a subdirectory
# Adjust these paths based on your actual project structure and where you place these files
BASE_AUDIO2MEMO_DIR = os.path.dirname(__file__) # Gets the directory of main.py
AUDIO2MEMO_MODULE_DIR = os.path.join(BASE_AUDIO2MEMO_DIR, "audio2memo")
PROMPT_TEXT_TO_WORDFORWORD_PATH = os.path.join(AUDIO2MEMO_MODULE_DIR, "prompts", "text_to_wordforword_prompt.txt")
PROMPT_WORDFORWORD_TO_MEMO_PATH = os.path.join(AUDIO2MEMO_MODULE_DIR, "prompts", "wordforword_to_memo_prompt.txt")

# --- Check if necessary files exist (optional but recommended) ---

# Add checks for prompt files if critical

# --- Helper Pydantic Models (Optional but good practice) ---
class TranscribeResponse(BaseModel):
    status: str
    task_id: str # Changed 'project' to 'project_id' for clarity, then to task_id
    message: Optional[str] = None

class TaskStatusResponse(BaseModel):
    # Define fields based on your Task model, excluding SQLAlchemy internal fields
    task_id: str
    status: str
    submit_time: datetime
    last_update_time: datetime
    file_name: Optional[str] = None         # Original uploaded file name
    model: Optional[str] = None             # Model used for processing
    error: Optional[str] = None             # Error message if status is 'failed' or 'timed_out'
    result_files: Optional[Dict[str, str]] = None # Dictionary of output files if 'completed'
    processing_time: Optional[float] = None # Duration in seconds
    to_email: Optional[str] = None          # For user reference
    email_status: Optional[str] = None      # Status of the notification email
    # Consider adding other relevant fields like:
    # output_type: Optional[str] = None
    # file_size: Optional[int] = None

# New Pydantic model for the list of tasks
class TaskListResponse(BaseModel):
    tasks: List[TaskStatusResponse]
    # total_active: int # Optional: count of tasks returned

# --- Email Sending Function --- 
def send_email_notification(
    task_id: str,
    project_name: str,
    to_email: str,
    cc_emails: Optional[str],
    status: str, # "completed" or "failed"
    result_files: Optional[Dict[str, str]], # Contains docx_path for completed tasks
    error_message: Optional[str],
    attachment_path: Optional[str] = None # New parameter for the attachment
) -> tuple[bool, str]:
    if not all([MAIL_USERNAME, MAIL_PASSWORD, MAIL_SMTP_SERVER, MAIL_SMTP_PORT]):
        logging.error(f"Task {task_id}: Mail server configuration incomplete. Cannot send email.")
        return False, "Mail server configuration incomplete."

    subject = ""
    body_html = "" # Using HTML for richer emails

    if status == "completed":
        subject = f"任务完成通知: {project_name} (ID: {task_id}) 已处理完毕"
        body_html = f"""
        <html>
            <body>
                <p>您好,</p>
                <p>您的音频转写任务 <b>{project_name}</b> (任务ID: {task_id}) 已成功处理完毕。</p>
                <p>处理结果已作为附件发送，请查收。</p> 
                <p>感谢使用我们的服务。</p>
            </body>
        </html>"""
        # Removed the section listing file paths
    elif status == "failed":
        subject = f"任务失败通知: {project_name} (ID: {task_id}) 处理失败"
        body_html = f"""\
        <html>
            <body>
                <p>您好,</p>
                <p>非常抱歉，您的音频转写任务 <b>{project_name}</b> (任务ID: {task_id}) 处理失败。</p>
        """
        if error_message:
            body_html += f"<p>错误详情: <pre>{error_message}</pre></p>"
        body_html += "<p>请检查您的文件或联系支持人员。 </p></body></html>"
    else:
        logging.warning(f"Task {task_id}: Attempted to send email for unknown status '{status}'.")
        return False, f"Unknown task status for email: {status}"

    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((str(Header(MAIL_SENDER_NAME, 'utf-8')), MAIL_USERNAME))
    msg['To'] = to_email
    if cc_emails:
        msg['Cc'] = cc_emails
    msg['Subject'] = Header(subject, 'utf-8')

    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    # Add attachment if provided (for completed tasks)
    if status == "completed" and attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as fil_to_attach:
                part = MIMEApplication(
                    fil_to_attach.read(),
                    Name=os.path.basename(attachment_path)
                )
            # After the file is closed
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
            logging.info(f"Task {task_id}: Attached file {attachment_path} to email.")
        except Exception as e:
            logging.error(f"Task {task_id}: Failed to attach file {attachment_path} to email: {e}", exc_info=True)
            # Email will be sent without attachment in this case

    recipients = [to_email]
    if cc_emails:
        recipients.extend([email.strip() for email in cc_emails.split(',') if email.strip()])

    try:
        logging.info(f"Task {task_id}: Connecting to SMTP server {MAIL_SMTP_SERVER}:{MAIL_SMTP_PORT}")
        server = smtplib.SMTP(MAIL_SMTP_SERVER, int(MAIL_SMTP_PORT))
        server.ehlo() # Extended Hello
        server.starttls() # Enable STARTTLS
        server.ehlo() # Re-send ehlo after STARTTLS
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        logging.info(f"Task {task_id}: Sending email to {recipients}")
        server.sendmail(MAIL_USERNAME, recipients, msg.as_string())
        server.quit()
        logging.info(f"Task {task_id}: Email sent successfully to {recipients}.")
        return True, "Email sent successfully."
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"Task {task_id}: SMTP Authentication Error: {e}. Check username/password.")
        return False, f"SMTP Authentication Error: {e}"
    except Exception as e:
        logging.error(f"Task {task_id}: Failed to send email: {e}", exc_info=True)
        return False, f"Failed to send email: {e}"

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Background Task Processing Function ---
def process_transcription_task( # Renamed and made into a background task
    project_id: str,
    local_file_path: str, # Path to the saved uploaded file
    original_filename: str,
    model_name_param: str, # Renamed to avoid conflict with 'model' Form param if any confusion
    to_email: str,
    cc_emails: Optional[str],
    # Directory paths needed by the pipeline
    task_base_dir: str, # Base directory for this task
    audio_segments_dir: str,
    transcripts_dir: str,
    wordforword_dir: str,
    memo_draft_dir: str,
    output_docx_dir: str
    # Prompt and template paths are global, so accessible directly
):
    db: Session = SessionLocal() # Create a new session for the background task
    task = None
    # Determine project_name for output files (use original filename base)
    project_name_base = os.path.splitext(original_filename)[0]
    # Basic sanitization for project name
    project_name_sanitized = "".join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in project_name_base)

    try:
        task = db.query(Task).filter(Task.task_id == project_id).first()
        if not task:
            logging.error(f"Background Task {project_id}: Task not found in DB. Aborting processing.")
            return # Or raise an exception to be caught by a higher level background task runner if any

        # Update task status to indicate start of processing (more granular)
        task.status = "processing_audio_split" 
        task.last_update_time = datetime.now()
        db.commit()
        db.refresh(task)
        logging.info(f"Task {project_id}: Status set to processing_audio_split.")

        # Step 1: Split audio
        logging.info(f"Task {project_id}: Splitting audio...")
        segment_paths = process_audio.split_audio(
            input_file_path=local_file_path,
            output_dir_path=audio_segments_dir
        )
        if not segment_paths:
            raise ValueError("Audio splitting failed.")
        logging.info(f"Task {project_id}: Audio split completed.")
        task.status = "transcribing"
        task.last_update_time = datetime.now()
        db.commit()
        db.refresh(task)

        # Step 2: Transcribe
        logging.info(f"Task {project_id}: Transcribing audio segments...")
        transcription_summary = audio2text.process_directory_of_audio_files(
            input_audio_segments_dir=audio_segments_dir,
            output_transcripts_dir=transcripts_dir,
            model_name=model_name_param # Use the model specified in the request
        )
        if not transcription_summary or (transcription_summary.get("failed_count", 0) > 0 and transcription_summary.get("successful_count",0) == 0):
            raise ValueError(f"Audio transcription failed. Summary: {transcription_summary}")
        logging.info(f"Task {project_id}: Transcription completed. Summary: {transcription_summary}")
        task.status = "generating_wordforword"
        task.last_update_time = datetime.now()
        db.commit()
        db.refresh(task)

        # Step 3: Text to Word-for-word
        logging.info(f"Task {project_id}: Generating word-for-word...")
        output_wordforword_filepath = os.path.join(wordforword_dir, f"{project_name_sanitized}_wordforword.txt")
        wordforword_success = text_to_wordforword.generate_wordforword(
            input_transcript_dir_path=transcripts_dir,
            output_wordforword_file_path=output_wordforword_filepath,
            prompt_template_path=PROMPT_TEXT_TO_WORDFORWORD_PATH
        )
        if not wordforword_success:
            raise ValueError("Failed to generate word-for-word text.")
        logging.info(f"Task {project_id}: Word-for-word generated.")
        task.status = "generating_memo_draft"
        task.last_update_time = datetime.now()
        db.commit()
        db.refresh(task)
        
        # Step 4: Wordforword to Memo Draft (or Transcripts to Memo Draft)
        logging.info(f"Task {project_id}: Generating memo draft...")
        output_memo_draft_filepath = os.path.join(memo_draft_dir, f"{project_name_sanitized}_memo_draft.txt")
        memo_success = wordforword_to_memo.generate_memo_from_transcripts( # Name implies it uses transcripts
            input_transcript_dir_path=transcripts_dir, # Confirm this input based on function def
            output_memo_file_path=output_memo_draft_filepath,
            prompt_template_path=PROMPT_WORDFORWORD_TO_MEMO_PATH
        )
        if not memo_success:
            raise ValueError("Failed to generate memo draft.")
        logging.info(f"Task {project_id}: Memo draft generated.")
        task.status = "generating_document"
        task.last_update_time = datetime.now()
        db.commit()
        db.refresh(task)

        # Step 5: Combine to DOCX
        logging.info(f"Task {project_id}: Combining outputs to DOCX...")
        final_output_paths = combine_to_docx.combine_to_docx_and_markdown(
            project_name=project_name_sanitized,
            summary_md_path=output_memo_draft_filepath, # This is the memo draft
            wordforword_md_path=output_wordforword_filepath, # This is the word-for-word .txt
            output_dir_docx=output_docx_dir
        )
        if not final_output_paths or not final_output_paths.get("docx_path"):
            raise ValueError("Failed to combine outputs into DOCX.")
        logging.info(f"Task {project_id}: Final DOCX output generated: {final_output_paths}")

        # --- Update Task in DB as Completed --- 
        task.status = "completed"
        task.result_files = final_output_paths 
        task.last_update_time = datetime.now()
        processing_duration = task.last_update_time - task.submit_time
        task.processing_time = processing_duration.total_seconds()
        db.commit()
        db.refresh(task)
        logging.info(f"Task {project_id}: Completed successfully.")
        
        # --- Trigger email notification on Success --- 
        attachment_to_send = final_output_paths.get("docx_path") if final_output_paths else None
        email_sent_status, email_message = send_email_notification(
            task_id=project_id,
            project_name=project_name_sanitized,
            to_email=task.to_email,
            cc_emails=task.cc_emails, # Send to CC on success
            status="completed",
            result_files=task.result_files, 
            error_message=None,
            attachment_path=attachment_to_send # Pass the docx_path for attachment
        )
        task.email_sent = datetime.now()
        task.email_status = email_message if not email_sent_status else "Sent"
        db.commit()

    except Exception as process_error: 
        logging.error(f"Task {project_id}: Background processing failed - {str(process_error)}", exc_info=True)
        if task: 
            task.status = "failed"
            task.error = str(process_error)[:2000] 
            task.last_update_time = datetime.now()
            if task.submit_time: # Ensure submit_time is not None for duration calculation
                 processing_duration = task.last_update_time - task.submit_time
                 task.processing_time = processing_duration.total_seconds()
            db.commit()

            # --- Trigger email notification on Failure --- 
            email_sent_status, email_message = send_email_notification(
                task_id=project_id,
                project_name=project_name_sanitized, # project_name_sanitized should be defined
                to_email=task.to_email,
                cc_emails=None, # Do NOT send to CC on failure
                status="failed",
                result_files=None,
                error_message=task.error,
                attachment_path=None # No attachment on failure
            )
            task.email_sent = datetime.now() # Record email attempt time
            task.email_status = email_message if not email_sent_status else "Sent (failure notice)"
            db.commit()
    finally:
        db.close() # Ensure DB session is closed for the background task


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: Request,
    background_tasks: BackgroundTasks, # Inject BackgroundTasks
    file: UploadFile = File(...),
    to_email: str = Form(...),
    cc_emails: Optional[str] = Form(""),
    model: str = Form("gpt-4o-transcribe"), # This is the transcription model name
    output_type: str = Form("all"), # This param seems unused in the core pipeline now
    db: Session = Depends(get_db) 
):
    if not process_audio: 
        logging.error("audio2memo modules not loaded, cannot process request.")
        raise HTTPException(status_code=500, detail="Server configuration error: audio processing module failed to load.")
        
    # For now, we use the original filename (without extension) as project_name
    # You might want a more sophisticated way to name projects or let users specify it.
    project_name_from_file = os.path.splitext(file.filename)[0]

    # --- Create Task Directory Structure ---
    # Use a unique ID for the task directory to avoid collisions
    # This project_id is the task_id
    project_id = str(uuid.uuid4()) # This will be our task_id

    # Base directory for all files related to this task
    # AUDIO_TARGET_DIR must be configured and be a valid path
    if not AUDIO_TARGET_DIR or not os.path.isdir(AUDIO_TARGET_DIR):
        logging.error(f"Task {project_id}: AUDIO_TARGET_DIR ('{AUDIO_TARGET_DIR}') is not configured or not a directory.")
        raise HTTPException(status_code=500, detail=f"Server configuration error: AUDIO_TARGET_DIR is invalid.")

    task_base_dir = os.path.join(AUDIO_TARGET_DIR, project_id)
    audio_segments_dir = os.path.join(task_base_dir, "audio_segments")
    transcripts_dir = os.path.join(task_base_dir, "transcripts")
    wordforword_dir = os.path.join(task_base_dir, "wordforword")
    memo_draft_dir = os.path.join(task_base_dir, "memo_draft")
    output_docx_dir = os.path.join(task_base_dir, "output_docx")
    
    try:
        os.makedirs(task_base_dir, exist_ok=True)
        os.makedirs(audio_segments_dir, exist_ok=True)
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(wordforword_dir, exist_ok=True)
        os.makedirs(memo_draft_dir, exist_ok=True)
        os.makedirs(output_docx_dir, exist_ok=True)
        logging.info(f"Task {project_id}: Created directory structure at {task_base_dir}")
    except OSError as e:
        logging.error(f"Task {project_id}: Failed to create directory structure: {e}", exc_info=True)
        # It's crucial to handle this, as the rest of the process depends on these directories
        raise HTTPException(status_code=500, detail=f"Failed to create task directories: {e}")


    local_file_path = os.path.join(task_base_dir, file.filename) # Save original file in task_base_dir

    try:
        with open(local_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"Task {project_id}: File '{file.filename}' saved to '{local_file_path}'")
    except Exception as e:
        logging.error(f"Task {project_id}: Error saving uploaded file: {e}", exc_info=True)
        # Clean up task directory if file saving fails
        shutil.rmtree(task_base_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {e}")
    finally:
        file.file.close() # Ensure file is closed

    # --- Database Interaction: Create Task Record ---
    new_task = None # Initialize to ensure it's defined for the finally block
    try:
        # Basic input validation for email (can be more complex)
        if not to_email: # Ensure to_email is provided
            raise HTTPException(status_code=400, detail="To Email is required.")

        new_task = Task(
            task_id=project_id, # Use the generated UUID as task_id
            project_name=project_name_from_file, # Use filename as project name
            status="submitted", 
            submit_time=datetime.now(),
            last_update_time=datetime.now(),
            file_name=file.filename,
            model=model, # Save the model name used
            # output_type=output_type, # Save output_type if relevant
            to_email=to_email,
            cc_emails=cc_emails if cc_emails else None,
            # result_files initially null
            # error initially null
            # processing_time initially null
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        logging.info(f"Task {new_task.task_id}: Record created in DB with status 'submitted'.")
    except HTTPException: # Re-raise HTTPExceptions
        if os.path.exists(task_base_dir): # Clean up if DB operation fails after file save
             shutil.rmtree(task_base_dir, ignore_errors=True)
        raise
    except Exception as e: # Catch other SQLAlchemy or DB errors
        logging.error(f"Task {project_id}: Database error creating task: {e}", exc_info=True)
        db.rollback()
        if os.path.exists(task_base_dir): # Clean up if DB operation fails after file save
             shutil.rmtree(task_base_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    # --- Add Transcription to Background Tasks ---
    try:
        background_tasks.add_task(
            process_transcription_task,
            project_id=new_task.task_id, # Pass the task_id
            local_file_path=local_file_path,
            original_filename=file.filename,
            model_name_param=model, # Pass the model name for transcription
            to_email=to_email,
            cc_emails=cc_emails,
            # Directory paths
            task_base_dir=task_base_dir,
            audio_segments_dir=audio_segments_dir,
            transcripts_dir=transcripts_dir,
            wordforword_dir=wordforword_dir,
            memo_draft_dir=memo_draft_dir,
            output_docx_dir=output_docx_dir
        )
        logging.info(f"Task {new_task.task_id}: Added to background tasks for processing.")
    except Exception as e: # Catch errors during add_task
        logging.error(f"Task {new_task.task_id}: Failed to add task to background queue: {e}", exc_info=True)
        # Update task status to 'failed' as it won't be processed
        new_task.status = "failed"
        new_task.error = f"Failed to enqueue for processing: {e}"
        new_task.last_update_time = datetime.now()
        db.commit()
        # No need to rmtree here as the file is saved, but it won't be processed. 
        # Consider if cleanup is desired if enqueueing fails.
        raise HTTPException(status_code=500, detail=f"Failed to enqueue task for processing: {e}")
    
    return TranscribeResponse(status="success", task_id=new_task.task_id, message="Task submitted successfully")


@app.get("/api/task_status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    processed_result_files = None
    if task.result_files:
        if isinstance(task.result_files, str): # If stored as JSON string
            try:
                processed_result_files = json.loads(task.result_files)
            except json.JSONDecodeError:
                logging.error(f"Task {task_id}: Failed to decode result_files JSON: {task.result_files}")
                processed_result_files = {"error": "Failed to parse result files"}
        elif isinstance(task.result_files, dict): # If already a dict (e.g. from SQLAlchemy JSON type)
            processed_result_files = task.result_files
        else: # Handle unexpected type
            logging.warning(f"Task {task_id}: result_files is of unexpected type: {type(task.result_files)}")
            processed_result_files = {"info": "Result files in non-standard format"}

    task_data = {
        "task_id": task.task_id,
        "status": task.status,
        "submit_time": task.submit_time,
        "last_update_time": task.last_update_time,
        "file_name": task.file_name,
        "model": task.model,
        "error": task.error,
        "result_files": processed_result_files, # Use the processed dictionary
        "processing_time": task.processing_time,
        "to_email": task.to_email,
        "email_status": task.email_status,
        # Populate other fields from task object as needed by TaskStatusResponse
        # For example, if you added output_type to TaskStatusResponse:
        # "output_type": task.output_type,
        # "file_size": task.file_size,
    }
    return TaskStatusResponse(**task_data) # Validate against the model

@app.get("/api/tasks", response_model=TaskListResponse)
def list_active_tasks(db: Session = Depends(get_db)):
    """
    Retrieves a list of all tasks currently in 'submitted' or 'processing' state,
    ordered by their submission time (oldest first).
    It will now also include tasks with more granular processing statuses.
    """
    active_tasks_query = db.query(Task).filter(
        Task.status.in_([
            "submitted", 
            "processing_audio_split", 
            "transcribing", 
            "generating_wordforword", 
            "generating_memo_draft",
            "generating_document"
            # "processing" could be a general fallback if needed, but specific states are better
        ])
    ).order_by(Task.submit_time.asc())
    
    active_tasks = active_tasks_query.all()

    response_tasks = []
    for task in active_tasks:
        processed_result_files = None
        if task.result_files:
            if isinstance(task.result_files, str): # If stored as JSON string
                try:
                    processed_result_files = json.loads(task.result_files)
                except json.JSONDecodeError:
                    logging.error(f"Task {task.task_id}: Failed to decode result_files JSON: {task.result_files}")
                    processed_result_files = {"error": "Failed to parse result files"}
            elif isinstance(task.result_files, dict): # If already a dict
                processed_result_files = task.result_files
            else: 
                logging.warning(f"Task {task.task_id}: result_files is of unexpected type: {type(task.result_files)}")
                processed_result_files = {"info": "Result files in non-standard format"}

        task_data = TaskStatusResponse(
            task_id=task.task_id,
            status=task.status,
            submit_time=task.submit_time,
            last_update_time=task.last_update_time,
            file_name=task.file_name,
            model=task.model,
            error=task.error,
            result_files=processed_result_files,
            processing_time=task.processing_time,
            to_email=task.to_email,
            email_status=task.email_status
            # Ensure all fields required by TaskStatusResponse are populated
        )
        response_tasks.append(task_data)
    
    return TaskListResponse(tasks=response_tasks) 