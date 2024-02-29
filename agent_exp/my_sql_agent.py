import os
import json
from langchain_community.tools.tavily_search import TavilySearchResults
# import broadscope_bailian
import datetime

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
    
# travily搜索引擎
os.environ['TAVILY_API_KEY']='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'    # travily搜索引擎api key
tavily=TavilySearchResults(max_results=3)
tavily.description='这是一个类似谷歌和百度的搜索引擎，搜索知识、天气、股票、电影、小说、百科等都是支持的哦，如果你不确定就应该搜索一下，谢谢！s'

# 工具列表
tools=[tavily, ]
tools=[]

tool_names='or'.join([tool.name for tool in tools])  # 拼接工具名
tool_descs=[] # 拼接工具详情
for t in tools:
    args_desc=[]
    for name,info in t.args.items():
        args_desc.append({'name':name,'description':info['description'] if 'description' in info else '','type':info['type']})
    args_desc=json.dumps(args_desc,ensure_ascii=False)
    tool_descs.append('%s: %s,args: %s'%(t.name,t.description,args_desc))
tool_descs='\n'.join(tool_descs)

prompt_tpl='''Today is {today}. Please Answer the following questions as best you can. You have access to the following tools:

{tool_descs}

These are chat history before:
{chat_history}

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

Question: {query}
{agent_scratchpad}
'''

def agent_execute(query,chat_history=[]):
    global tools,tool_names,tool_descs,prompt_tpl,llm,tokenizer
    
    agent_scratchpad='' # agent执行过程
    while True:
        # 1）触发llm思考下一步action
        history='\n'.join(['Question:%s\nAnswer:%s'%(his[0],his[1]) for his in chat_history])
        today=datetime.datetime.now().strftime('%Y-%m-%d')
        prompt=prompt_tpl.format(today=today,chat_history=history,tool_descs=tool_descs,tool_names=tool_names,query=query,agent_scratchpad=agent_scratchpad)
        print('\033[32m---等待LLM返回... ...\n%s\n\033[0m'%prompt,flush=True)
        response=llm(prompt,user_stop_words=['Observation:'])
        print('\033[34m---LLM返回---\n%s\n---\033[34m'%response,flush=True)
        
        # 2）解析thought+action+action input+observation or thought+final answer
        thought_i=response.rfind('Thought:')
        final_answer_i=response.rfind('\nFinal Answer:')
        action_i=response.rfind('\nAction:')
        action_input_i=response.rfind('\nAction Input:')
        observation_i=response.rfind('\nObservation:')
        
        # 3）返回final answer，执行完成
        if final_answer_i!=-1 and thought_i<final_answer_i:
            final_answer=response[final_answer_i+len('\nFinal Answer:'):].strip()
            chat_history.append((query,final_answer))
            return True,final_answer,chat_history
        
        # 4）解析action
        if not (thought_i<action_i<action_input_i):
            return False,'LLM回复格式异常',chat_history
        if observation_i==-1:
            observation_i=len(response)
            response=response+'Observation: '
        thought=response[thought_i+len('Thought:'):action_i].strip()
        action=response[action_i+len('\nAction:'):action_input_i].strip()
        action_input=response[action_input_i+len('\nAction Input:'):observation_i].strip()
        
        # 5）匹配tool
        the_tool=None
        for t in tools:
            if t.name==action:
                the_tool=t
                break
        if the_tool is None:
            observation='the tool not exist'
            agent_scratchpad=agent_scratchpad+response+observation+'\n'
            continue 
        
        # 6）执行tool
        try:
            action_input=json.loads(action_input)
            # tool_ret=the_tool.invoke(input=json.dumps(action_input))
            tool_ret=the_tool.invoke(input=action_input)
        except Exception as e:
            observation='the tool has error:{}'.format(e)
        else:
            observation=str(tool_ret)
        agent_scratchpad=agent_scratchpad+response+observation+'\n'

def agent_execute_with_retry(query,chat_history=[],retry_times=2):
    for i in range(retry_times):
        success,result,chat_history=agent_execute(query,chat_history=chat_history)
        if success:
            return success,result,chat_history
    return success,result,chat_history

my_history=[]
from call_sql_api import post_request
while True:
    query=input('query:')
    # 请求api工具，然后进行结果获取，进而得到答案，再进行修复
    url = 'http://10.251.172.138:7777/question2sql'
    data = {
    "user":"H2017871",
    "question":query,
    "semantic_message":"",
    "scene_code":"cnc_wmsc"
    }
    headers = {'Content-Type': 'application/json'}
    result = post_request(url, data, headers)
    result = json.loads(result) # 转为字典数据格式
    # query = f"问题：{query}\nsql：{result['answer']}\n请帮我检查sql是否正确，是否与问题匹配，如果不匹配，请进行修正"
    query = f"问题：{query}\nsql：...\n请帮我生成sql\n参考sql为:\n{result['answer']}"
    success,result,my_history=agent_execute_with_retry(query,chat_history=my_history)
    my_history=my_history[-10:]