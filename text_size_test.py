import pypdf
import ollama
from tokenCounter import count_tokens
import re
from modelinfo import get_context_length
import argparse

def extract(filepath, num_tokens, prompt):
    """
    Extract part of a pdf text based on the number of tokens being tested
    """
    
    reader = pypdf.PdfReader(filepath)
    pages = reader.pages

    prompt_length = count_tokens(text=prompt)
    extracted_text = ""
    for page in pages:
        curr_text = page.extract_text()
        sentences = re.split(r'(?<=[.!?])\s+', curr_text)
        for sentence in sentences:
            sentence_len = count_tokens(text=sentence)
            if (prompt_length + count_tokens(text=extracted_text)) + sentence_len <= num_tokens:
                extracted_text += sentence
            else:
                return extracted_text.strip()
    
    return extracted_text.strip()

def get_summary(text:str, prompt:str, model:str) -> str:
    """
    Prompt the model based on the provided chunk of a text.
    """

    model_response = ollama.chat(
        model=model,
        messages=[
            {'role':'user', 'content':f'{prompt}\n{text}'}
        ],
        stream=False,
        options={'temperature':0, 'num_ctx': get_context_length(model)}
    )
    
    return model_response.get('message', {}).get('content', "Error: no response from the model.")

def record_test(text, prompt, model, response):
    """
    Records test in a txt file with text, prompt, model, and model's response
    """

    test_dir = "tests/text_size_test/"

    model_prefix = {
        "llama3.1:8b": "llama",
        "llama3.1:8b-instruct-fp16": "llama",
        "qwen2.5:14b": "qwen",
        "qwen2.5:14b-instruct-fp16": "qwen",
        "mistral-nemo:12b": "mistral",
        "mistral-nemo:12b-instruct-2407-fp16": "mistral",
        "gemma3:27b":"gemma",
        "phi4":"phi4",
        "deepseek-r1:14b":"deepseek",
        "deepseek-r1:14b-qwen-distill-fp16":"deepseek",
    }.get(model)

    test_dir += model_prefix
    is_instruct = "instruct" in model
    model_type = "instruct" if is_instruct else "base"
    result_file = f"{test_dir}_{model_type}_modelresponse.txt"

    with open(result_file, "w", encoding="utf-8") as file:
        file.write(f"""Model: {model}
Prompt: {prompt}
Text size (tokens): {count_tokens(text)}
Text: \n{text}\n\n
Model Response: {response}
""")

# Parsing args and recording tests
if __name__ == "__main__":
    prompt = """Conduct a holistic, precision-driven text comprehension analysis. Your goal is to maintain 100% information integrity while preserving exact contextual nuances.

Deliver:

1. An exhaustive factual summary capturing all key events and details without distortion or omission.
2. A thematic analysis exploring core ideas and recurring motifs.
3.A deep symbolic/metaphorical interpretation supported by textual evidence.
4. Extraction of five pivotal narrative components with justification.

Map out with full detail:

1. All character interactions and relationships.
2. The complete plot progression with no missing elements.
3. Narrative techniques, including structural choices, perspective, and literary devices.
4. A linguistic breakdown covering syntax, diction, tone, narrative voice, and literary techniques.
"""

    parser = argparse.ArgumentParser(description="User input")
    parser.add_argument("num_tokens", type=int, help="Number of tokens to process at a time")
    parser.add_argument("filepath", type=str, help="Filepath to pdf")
    args = parser.parse_args()

    response: ollama.ListResponse = ollama.list()
    for model in response.models:
        model_name = model.model

        if model_name == "nomic-embed-text:latest":
            continue
        
        extracted_text = extract(args.filepath, args.num_tokens)

        summary = get_summary(extracted_text, prompt, model_name)

        record_test(extracted_text, prompt, model_name, summary)