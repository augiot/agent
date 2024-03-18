
import os
# from langchain.llms import OpenAI
# from langchain_community.llms import OpenAI
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


API_KEY = "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"
os.environ["OPENAI_API_KEY"] = API_KEY

# prompt模板
prompt = PromptTemplate(
    input_variables=["product","name"],
    template="What is a good name for a company that makes {product}，{name}?",
)
print(prompt)
print(prompt.format(product="colorful socks",name="111"))
# print(prompt.format(product="colorful socks"))
raise EOFError

# llm
# Simple LLM call Using LangChain model_name="gpt-3.5-turbo"
# llm = OpenAI(temperature=0.9)
# question = "Which language is used to create chatgpt ?"
# print(question, llm(question))

# chain
llm = OpenAI(temperature=0.9)
prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}，{name}?",
)
chain = LLMChain(llm=llm, prompt=prompt)
# chain.run("colorful socks")
print(chain.run(product='COLOR', name='FOOTBALL'))