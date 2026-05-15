import os
import requests
import sys

def get_completion(prompt):
    api_key = os.getenv("LLM_API_KEY") 
    api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model_name = os.getenv("LLM_MODEL", "gpt-5.4-mini")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling LLM: {e}")
        sys.exit(1)

import subprocess

def get_git_diff():
    # 獲取當前分支與 main 主分支的差異
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD^", "HEAD", "--", ":!README_ZH.md"], 
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except Exception as e:
        print(f"Warning: Could not get git diff: {e}")
        return "No recent code changes detected."

def main():
    with open("README.md", "r", encoding="utf-8") as f:
        readme_en = f.read()
    
    diff_content = get_git_diff()
    
    try:
        with open("README_ZH.md", "r", encoding="utf-8") as f:
            readme_zh = f.read()
    except FileNotFoundError:
        readme_zh = ""

    prompt = f"""
    You are a technical documentation maintainer. Your task is to update the documentation based on recent code changes.
    
    --- RECENT CODE CHANGES (Git Diff) ---
    {diff_content}
    
    --- CURRENT README (English) ---
    {readme_en}
    
    --- CURRENT README (Traditional Chinese) ---
    {readme_zh}
    
    Task:
    1. Analyze the 'RECENT CODE CHANGES' to identify new features, bug fixes, or architectural changes.
    2. Update BOTH the English README and the Traditional Chinese README_ZH content.
    3. Ensure the tone is professional and the Chinese version uses Traditional Chinese (zh-TW).
    
    Format Requirements:
    - Output EXACTLY AND ONLY the full content of README.md first.
    - Then output the exact separator line: =====
    - Then output EXACTLY AND ONLY the full content of README_ZH.md.
    - DO NOT include ANY conversational text like "Here is the updated content" or markdown code blocks (```markdown) to wrap the entire output.
    - Start directly with the content of README.md.
    """
    
    print("Analyzing code changes and updating documentation via LLM...")
    llm_output = get_completion(prompt)
    
    if "=====" in llm_output:
        parts = llm_output.split("=====")
        new_en = parts[0].strip()
        new_zh = parts[1].strip()
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_en)
        with open("README_ZH.md", "w", encoding="utf-8") as f:
            f.write(new_zh)
        print("Successfully updated README.md and README_ZH.md")
    else:
        # Fallback if separator is missing
        with open("README_ZH.md", "w", encoding="utf-8") as f:
            f.write(llm_output)
        print("Updated README_ZH.md (Note: Separator missing, only one file updated)")

if __name__ == "__main__":
    main()
