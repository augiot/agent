
"""
https://zhuanlan.zhihu.com/p/664477178

"""


import json
import openai
from openai import OpenAI
openai.api_base = "http://10.20.216.187:8020/v1"
openai.api_key = "empty"
model_name = "/mnt/user2/workspace/model/Qwen-7B-Chat"
temperature = 0

client = OpenAI(
    api_key=openai.api_key,
    base_url=openai.api_base
)

def llm(query,history=[],user_stop_words=[]):    # 调用api_server

    try:
        messages=[{'role':'system','content':'You are a helpful assistant.'}]
        for hist in history:
            messages.append({'role':'user','content':hist[0]})
            messages.append({'role':'assistant','content':hist[1]})
        messages.append({'role':'user','content':query})

        # 2.模型推理
        completion = client.chat.completions.create(
            model = model_name,
            messages = messages,
            stream=False,
            temperature = temperature,
            stop = ["<|im_end|>","<|endoftext|>"] + user_stop_words
        )
        content = completion.choices[0].message.content
        # print(resp)
        # content=resp.get("Data", {}).get("Choices", [])[0].get("Message", {}).get("Content")
        return content
    except Exception as e:
        return str(e)




TOOL_DESC = """{name_for_model}: Call this tool to interact with the {name_for_human} API. What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters} Format the arguments as a JSON object."""

REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

{tool_descs}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {query}"""

# from langchain.tools.python.tool import PythonAstREPLTool
from langchain_experimental.tools.python.tool import PythonAstREPLTool
from langchain.utilities import ArxivAPIWrapper
from langchain import SerpAPIWrapper
arxiv = ArxivAPIWrapper()
python = PythonAstREPLTool()
search = SerpAPIWrapper(serpapi_api_key ="0a5067b2803f7506122022a5c1c4bd7e7fe907ccada04d6607768a7891138c5d" )


def tool_wrapper_for_qwen(tool,):
    def tool_(query):
        query = json.loads(query)["query"]
        return tool.run(query)
    return tool_

# 以下是给千问看的工具描述：
TOOLS = [
    {
        'name_for_human':
            'arxiv',
        'name_for_model':
            'Arxiv',
        'description_for_model':
            'A wrapper around Arxiv.org Useful for when you need to answer questions about Physics, Mathematics, Computer Science, Quantitative Biology, Quantitative Finance, Statistics, Electrical Engineering, and Economics from scientific articles on arxiv.org.',
        'parameters': [{
            "name": "query",
            "type": "string",
            "description": "the document id of arxiv to search",
            'required': True
        }], 
        'tool_api': tool_wrapper_for_qwen(arxiv)
    },
    {
        'name_for_human':
            'python',
        'name_for_model':
            'python',
        'description_for_model':
            "A Python shell. Use this to execute python commands. When using this tool, sometimes output is abbreviated - Make sure it does not look abbreviated before using it in your answer. "
            "Don't add comments to your python code.",
        'parameters': [{
            "name": "query",
            "type": "string",
            "description": "a valid python command.",
            'required': True
        }],
        'tool_api': tool_wrapper_for_qwen(python)
    },
    {
        'name_for_human':
            'google search',
        'name_for_model':
            'Search',
        'description_for_model':
            'useful for when you need to answer questions about current events.',
        'parameters': [{
            "name": "query",
            "type": "string",
            "description": "search query of google",
            'required': True
        }], 
        'tool_api': tool_wrapper_for_qwen(search)
    }

]


# 构建prompt
def build_planning_prompt(TOOLS, query):
    tool_descs = []
    tool_names = []
    for info in TOOLS:
        tool_descs.append(
            TOOL_DESC.format(
                name_for_model=info['name_for_model'],
                name_for_human=info['name_for_human'],
                description_for_model=info['description_for_model'],
                parameters=json.dumps(
                    info['parameters'], ensure_ascii=False),
            )
        )
        tool_names.append(info['name_for_model'])
    tool_descs = '\\n\\n'.join(tool_descs)
    tool_names = ','.join(tool_names)

    prompt = REACT_PROMPT.format(tool_descs=tool_descs, tool_names=tool_names, query=query)
    return prompt

prompt_1 = build_planning_prompt(TOOLS[0:3], query="中国人口多少，google查询")
# print(prompt_1)


# llm推理
stop = ["Observation:", "Observation:\\n"]
response_1=llm(prompt_1,user_stop_words=['Observation:'])
print(response_1)


from typing import Dict, Tuple
def parse_latest_plugin_call(text: str) -> Tuple[str, str]:
    i = text.rfind('\\nAction:')
    j = text.rfind('\\nAction Input:')
    k = text.rfind('\\nObservation:')
    if 0 <= i < j:  # If the text has `Action` and `Action input`,
        if k < j:  # but does not contain `Observation`,
            # then it is likely that `Observation` is ommited by the LLM,
            # because the output text may have discarded the stop word.
            text = text.rstrip() + '\\nObservation:'  # Add it back.
            k = text.rfind('\\nObservation:')
    if 0 <= i < j < k:
        plugin_name = text[i + len('\\nAction:'):j].strip()
        plugin_args = text[j + len('\\nAction Input:'):k].strip()
        return plugin_name, plugin_args
    return '', ''

def use_api(tools, response):
    use_toolname, action_input = parse_latest_plugin_call(response)
    if use_toolname == "":
        return "no tool founds"

    used_tool_meta = list(filter(lambda x: x["name_for_model"] == use_toolname, tools))
    if len(used_tool_meta) == 0:
        return "no tool founds"
    
    api_output = used_tool_meta[0]["tool_api"](action_input)
    return api_output

api_output = use_api(TOOLS, prompt_1)
print(api_output)

