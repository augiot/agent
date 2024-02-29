import os
import openai

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "http://10.20.216.187:8020/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "xxx")

# openai.api_type = "azure"
openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_API_KEY

MODEL_NAME = "/mnt/user2/workspace/model/Qwen-7B-Chat"

def api_func(prompt:str):
    # global MODEL_NAME
    
    # print(f"\nUse OpenAI model: {MODEL_NAME}\n")
    messages_item = [] + [{
            "role": "user",
            "content": prompt 
        }]

    # 2.模型推理
    response = openai.ChatCompletion.create(
        engine="/mnt/user2/workspace/model/Qwen-7B-Chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        stream=False,
        stop = ["<|im_end|>","<|endoftext|>"]
    )
  
    text = response['choices'][0]['message']['content'].strip()
    prompt_token = response['usage']['prompt_tokens']
    response_token = response['usage']['completion_tokens']
    return text, prompt_token, response_token

def api_func_2(prompt):
    # 2.模型推理
    response = openai.ChatCompletion.create(
        model = MODEL_NAME,
        messages = [{"role": "user", "content": prompt}],
        stream=False,
        temperature = 0.1,
        stop = ["<|im_end|>","<|endoftext|>"]
    )
    text = response['choices'][0]['message']['content'].strip()
    prompt_token = response['usage']['prompt_tokens']
    response_token = response['usage']['completion_tokens']
    return text, prompt_token, response_token

if __name__=="__main__":
    prompt = "你好！"
    print(api_func_2(prompt))