import json
import os
import time
from dotenv import load_dotenv
from graders.grade_all import grade_filter, grade_verilog, grade_stm32_usart

# Load environment variables from .env
load_dotenv()

def query_model(prompt, model_name, max_retries=3):
    """
    Unified API wrapper for Google Gemini, Groq Cloud, and OpenRouter models.
    """
    for attempt in range(max_retries):
        try:
            # --- 1. GOOGLE GEMINI ---
            if model_name.startswith("gemini"):
                from google import genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY is missing from your .env file.")
                
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text.strip()

            # --- 2. GROQ CLOUD ---
            elif model_name.startswith("groq/"):
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY is missing from your .env file.")
                
                # Extract exact model name (e.g., groq/openai/gpt-oss-120b -> openai/gpt-oss-120b)
                real_model = model_name.replace("groq/", "")
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model=real_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                return response.choices[0].message.content.strip()

            # --- 3. OPENROUTER ---
            elif model_name.startswith("openrouter"):
                from openai import OpenAI
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError("OPENROUTER_API_KEY is missing from your .env file.")
                
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                return response.choices[0].message.content.strip()

            else:
                raise ValueError(f"Unsupported model specified: {model_name}")

        except Exception as e:
            err_msg = str(e)
            if ("503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "rate_limit" in err_msg) and attempt < max_retries - 1:
                sleep_time = (2 ** attempt) * 4
                print(f"Warning: {model_name} busy (attempt {attempt+1}/{max_retries}). Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print(f"Error querying {model_name}: {e}")
                return ""

def run_benchmark():
    tasks = [
        {"file": "tasks/task_01_filter.json", "grader": grade_filter},
        {"file": "tasks/task_02_verilog.json", "grader": grade_verilog},
        {"file": "tasks/task_03_stm32_usart.json", "grader": grade_stm32_usart}
    ]
    
    # Valid model endpoints
    models = [
        "gemini-3.5-flash-lite",
        "groq/openai/gpt-oss-120b",
        "groq/qwen/qwen3.8-27b",
        "openrouter/free"
    ]
    
    trials_per_task = 3
    results = {}
    
    for model in models:
        print(f"\n==========================================")
        print(f"   Running Benchmark for Model: {model}")
        print(f"==========================================")
        
        total_score = 0.0
        total_trials = 0
        
        for task_info in tasks:
            with open(task_info['file'], 'r', encoding="utf-8") as f:
                task = json.load(f)
            
            task_id = task['task_id']
            grader = task_info['grader']
            
            print(f"-> Task: {task_id}")
            task_scores = []
            
            for trial in range(trials_per_task):
                response = query_model(task['prompt'], model_name=model)
                score = grader(response)
                task_scores.append(score)
                total_score += score
                total_trials += 1
                
                # Save execution transcript
                safe_folder = model.replace("/", "_").replace(":", "_")
                os.makedirs(f"transcripts/{safe_folder}", exist_ok=True)
                transcript_path = f"transcripts/{safe_folder}/{task_id}_trial_{trial+1}.txt"
                with open(transcript_path, "w", encoding="utf-8") as tf:
                    tf.write(f"MODEL: {model}\nTASK: {task_id}\nTRIAL: {trial+1}\nSCORE: {score}\n")
                    tf.write("="*40 + "\n")
                    tf.write(f"PROMPT:\n{task['prompt']}\n\n")
                    tf.write("="*40 + "\n")
                    tf.write(f"RESPONSE:\n{response}\n")
            
            print(f"   Scores: {task_scores}")
        
        pass_rate = (total_score / total_trials) * 100 if total_trials > 0 else 0.0
        results[model] = f"{pass_rate:.1f}%"
    
    print("\n" + "="*40)
    print("       FINAL EVALUATION SUMMARY")
    print("="*40)
    print(json.dumps(results, indent=2))
    
    # Save overall summary to results directory
    os.makedirs("results", exist_ok=True)
    with open("results/summary.json", "w", encoding="utf-8") as sf:
        json.dump(results, sf, indent=2)

if __name__ == "__main__":
    run_benchmark()