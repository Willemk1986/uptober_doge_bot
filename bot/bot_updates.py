import subprocess
import sys
import os
import logging
import json
import shutil
import tempfile
import pytest
from datetime import datetime
from pathlib import Path

# LangChain for AI self-improvement (free local LLM)
from langchain.llms import HuggingFacePipeline
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPDATE_RECORD = os.path.join(os.path.dirname(__file__), 'update_record.txt')
STATE_BACKUP = 'state_backup.json'
PID_FILE = 'bot.pid'

def log_update(message):
    with open(UPDATE_RECORD, 'a') as f:
        f.write(f"{datetime.now()}: {message}\n")
    logger.info(message)

# =============================================
# AI SELF-IMPROVEMENT ENGINE
# =============================================
def ai_self_improve(ghost_dir):
    """Scan all .py files, use CodeLlama to suggest improvements, apply if safe."""
    try:
        os.chdir(ghost_dir)
        # Free local LLM (CodeLlama 7B - first run downloads ~4GB)
        llm = HuggingFacePipeline(
            pipeline=pipeline(
                'text-generation',
                model='codellama/CodeLlama-7b-Instruct-hf',
                max_length=1024,
                temperature=0.3
            )
        )
        prompt = PromptTemplate(
            input_variables=['code', 'file'],
            template="""
Analyze this Python code for:
- Security vulnerabilities
- Performance improvements
- User experience (Telegram bot)
- Best practices (2025)

File: {file}
Code:

Suggest improved version. Output ONLY the full improved code.
"""
        )
        chain = LLMChain(llm=llm, prompt=prompt)

        for py_file in Path('.').rglob('*.py'):
            if '.git' in str(py_file) or 'venv' in str(py_file):
                continue
            with open(py_file, 'r', encoding='utf-8') as f:
                original = f.read()
            
            try:
                improved = chain.run(code=original, file=py_file)
                # Only apply if improvement detected and syntax valid
                if len(improved.strip()) > 50 and '```' not in improved:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(improved.strip())
                    log_update два(f"AI improved: {py_file}")
            except Exception as e:
                log_update(f"AI skip {py_file}: {e}")
        return True
    except Exception as e:
        log_update(f"AI engine failed: {e}")
        return False

# =============================================
# CORE UPDATE LOGIC
# =============================================
def backup_current():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copytree('.', backup_dir, ignore=shutil.ignore_patterns('venv', '.git', 'backup_*', 'staging_*', '.env'))
    log_update(f"Backup created: {backup_dir}")
    return backup_dir

def scan_github_changes():
    try:
        diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD', 'origin/main'], capture_output=True, text=True)
        changed = [f for f in diff.stdout.strip().split('\n') if f and not f.startswith('.env')]
        log_update(f"GitHub changes: {changed}")
        return changed
    except Exception as e:
        log_update(f"Scan failed: {e}")
        return []

def pull_updates():
    try:
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True, check=True)
        log_update(f"Git pull: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        log_update(f"Pull failed: {e.stderr}")
        return False

def update_deps():
    try:
        subprocess.run(['pip', 'install', '--upgrade', '-r', 'requirements.txt', '--user'], check=True)
        log_update("Dependencies updated")
        return True
    except Exception as e:
        log_update(f"Dep update failed: {e}")
        return False

def run_tests(ghost_dir):
    try:
        os.chdir(ghost_dir)
        # AI self-improvement
        ai_self_improve(ghost_dir)
        # Run pytest
        result = subprocess.run(['pytest', '-q'], capture_output=True, text=True)
        if result.returncode == 0:
            log_update("All tests passed")
            return True
        else:
            log_update(f"Tests failed: {result.stdout}")
            return False
    except Exception as e:
        log_update(f"Test run error: {e}")
        return False

def pause_bot():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 15)  # SIGTERM
            log_update("Bot paused")
        except:
            log_update("Bot already stopped")

def resume_bot():
    subprocess.Popen([sys.executable, 'bot/bot.py'], cwd=os.path.dirname(__file__))
    log_update("Bot resumed")

def apply_update(ghost_dir, backup_dir):
    try:
        pause_bot()
        shutil.rmtree('.', ignore_errors=True)
        shutil.copytree(ghost_dir, '.', ignore=shutil.ignore_patterns('backup_*', 'staging_*', '.env'))
        log_update("Update applied")
        resume_bot()
        return True
    except Exception as e:
        log_update(f"Apply failed: {e}")
        shutil.rmtree('.', ignore_errors=True)
        shutil.copytree(backup_dir, '.', ignore=shutil.ignore_patterns('backup_*', 'staging_*', '.env'))
        log_update("Rolled back")
        resume_bot()
        return False

def main():
    log_update("=== UPDATER STARTED ===")
    backup_dir = backup_current()
    ghost_dir = tempfile.mkdtemp(prefix="ghost_")
    
    try:
        shutil.copytree('.', ghost_dir, ignore=shutil.ignore_patterns('venv', '.git', 'backup_*', 'staging_*', '.env'))
        os.chdir(ghost_dir)
        
        changes = scan_github_changes()
        code_updated = pull_updates() if changes else False
        deps_updated = update_deps()
        
        if code_updated or deps_updated:
            if run_tests(ghost_dir):
                apply_update(ghost_dir, backup_dir)
                log_update("UPDATE SUCCESS")
            else:
                log_update("UPDATE FAILED - TESTS")
        else:
            log_update("No updates")
            
    except Exception as e:
        log_update(f"CRITICAL ERROR: {e}")
    finally:
        shutil.rmtree(ghost_dir, ignore_errors=True)
        log_update("=== UPDATER FINISHED ===\n")

if __name__ == '__main__':
    main()