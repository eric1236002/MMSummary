import streamlit as st
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

def calculate_rouge_scores(original, summary):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    scores = scorer.score(original, summary)
    return scores

def calculate_bleu_score(original, summary):
    # 將文本分割為單詞列表
    reference = [original.split()]
    candidate = summary.split()
    # 計算 BLEU 分數
    smoothing = SmoothingFunction().method1
    score = sentence_bleu(reference, candidate, smoothing_function=smoothing)
    return score

def main():
    # st.title("MMSummary evaluation 📝")

    original = st.file_uploader("Input original file")
    summary = st.file_uploader("Input summary file")
    if original and summary:
        original = original.getvalue().decode("utf-8")
        summary = summary.getvalue().decode("utf-8")
    
    if st.button("Evaluate"):
        if original and summary:
            # 計算 ROUGE 和 BLEU 分數
            rouge_scores = calculate_rouge_scores(original, summary)
            bleu_score = calculate_bleu_score(original, summary)
            
            st.write("ROUGE Scores:")
            for key, score in rouge_scores.items():
                st.write(f"{key}: {score}")

            st.write(f"BLEU Score: {bleu_score}")
        else:
            st.write("Please input both original file and summary.")

if __name__ == "__main__":
    main()
