# MMSummary

Use Langchain for meeting summary and abstract.

## Environment
Install requirements
```
pip install langchain streamlit
```

create .env file in the directory
```
OPENAI_API_KEY=<Your_API_KEY>
```

## prompt file

map_template and reduce_template is the prompt file for the LLM.

## Run
```
streamlit run ./web.py
```