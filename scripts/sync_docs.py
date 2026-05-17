import json
import os
import requests
import sys

def get_completion(prompt):
    # 這個函式負責把 prompt 送到外部 LLM API，讓模型幫忙判斷 README 是否需要更新。
    # 透過環境變數控制 API key、endpoint 與 model，方便在不同環境切換。
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
    # LLM 回應有時會夾帶多餘文字，因此先嘗試直接解析；失敗後再手動截取最外層 JSON。
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
    # 取得最近一次提交差異，作為 README 更新的依據。
    # 注意：這裡排除 README_ZH.md，避免文件改動又反過來影響 prompt 內容。
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
    # 讀取現有 README 內容，讓 LLM 在原文件基礎上做增修，而不是從零重寫。
    with open("README.md", "r", encoding="utf-8") as f:
        readme_en = f.read()
    
    # 把程式碼變更摘要傳給 LLM，讓它判斷是否需要同步更新文件。
    diff_content = get_git_diff()
    
    try:
        with open("README_ZH.md", "r", encoding="utf-8") as f:
            readme_zh = f.read()
    except FileNotFoundError:
        # 如果中文文件還不存在，就用空字串表示，讓 LLM 自行補齊內容。
        readme_zh = ""

    # 這段 prompt 的核心目標：讓 LLM 根據 diff 判斷文件是否要改，
    # 若要改，則一次輸出兩份完整 README，避免只回傳片段導致內容不一致。
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
        # 把模型輸出轉回 JSON，後續才能依欄位決定是否真的要寫檔。
        result = extract_json_payload(llm_output)
    except Exception as e:
        print(f"Error parsing LLM JSON output: {e}")
        sys.exit(1)

    # `update_required` 表示模型是否認為文件需要同步更新。
    update_required = bool(result.get("update_required"))
    new_en = (result.get("readme_md") or "").strip()
    new_zh = (result.get("readme_zh_md") or "").strip()

    if not update_required:
        # 如果沒有需要更新，就維持現狀，不寫回任何檔案。
        print("No documentation update required.")
        return

    if not new_en or not new_zh:
        # 理論上只要需要更新，就應該同時給出兩份完整 README。
        print("Update required but README content missing in JSON output.")
        sys.exit(1)

    # 寫回兩份文件，確保英文版與中文版同步。
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_en)
    with open("README_ZH.md", "w", encoding="utf-8") as f:
        f.write(new_zh)
    print("Successfully updated README.md and README_ZH.md")

if __name__ == "__main__":
    main()
