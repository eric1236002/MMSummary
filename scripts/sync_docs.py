import json
import os
import requests
import sys

def get_completion(prompt):
    api_key = os.getenv("LLM_API_KEY") 
    api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    
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

def extract_json_payload(text):
    """
    Try to parse JSON from LLM output. If extra text is present, extract
    the outermost JSON object.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM output.")

    return json.loads(text[start : end + 1])

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
    2. Decide whether the README files should be updated.
    3. If updates are needed, provide the full updated content for BOTH README files.

    Output Requirements:
    - Output ONLY a single JSON object.
    - The JSON must include these keys:
        - "update_required": boolean
        - "readme_md": string (full updated README.md content, empty if no update)
        - "readme_zh_md": string (full updated README_ZH.md content, empty if no update)
        - "reason": string (short rationale)
    - Do NOT wrap JSON in markdown fences and do NOT include any extra text.
    """
    
    print("Analyzing code changes and updating documentation via LLM...")
    llm_output = get_completion(prompt)
    
    try:
        result = extract_json_payload(llm_output)
    except Exception as e:
        print(f"Error parsing LLM JSON output: {e}")
        sys.exit(1)

    update_required = bool(result.get("update_required"))
    new_en = (result.get("readme_md") or "").strip()
    new_zh = (result.get("readme_zh_md") or "").strip()

    if not update_required:
        print("No documentation update required.")
        return

    if not new_en or not new_zh:
        print("Update required but README content missing in JSON output.")
        sys.exit(1)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_en)
    with open("README_ZH.md", "w", encoding="utf-8") as f:
        f.write(new_zh)
    print("Successfully updated README.md and README_ZH.md")

if __name__ == "__main__":
    main()
