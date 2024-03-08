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
# while True:
#     query=input('query:')
#     success,result,my_history=agent_execute_with_retry(query,chat_history=my_history)
#     my_history=my_history[-10:]


query="""
\nconfig_json:\n{'column': ['产品类型', '阶段', '设备类型', '专案', '机种', '制程类型', '制程', '工站', '楼层', '厂区'], 'column_db': ['material_group', 'attribution', 'device_type', 'project', 'project', 'process_type', 'process', 'work_station', 'area_floor_id'], 'value': {'产品类型': ['Band', 'TM', 'MCH', 'BGM'], '阶段': ['量試', '量產'], '设备类型': ['主設備', '檢測設備', '自動化設備'], '专案': ['238B', '237M/238M', '252B', '223', 'DM243', '244B', 'DM233', 'DM234', '252M', '244M', '243B', '234B', '237M', '248B', '247B', '248M', 'DM237', '23X', 'DM238', '254M', '233M', '259M', '238M', '243M', '247M', '253M', '234M'], '机种': ['238B', '237M/238M', '252B', '223', 'DM243', '244B', 'DM233', 'DM234', '252M', '244M', '243B', '234B', '237M', '248B', '247B', '248M', 'DM237', '23X', 'DM238', '254M', '233M', '259M', '238M', '243M', '247M', '253M', '234M'], '制程类型': ['外觀檢測', '支架預處理', 'PVD', '組裝', '撕貼膜', '陽極', 'PU', '檢測', 'CNC', '尺寸檢', '組立', '清洗', '灌膠', '组装', '焊接', '功能檢'], '制程': ['重工', 'RT去毛刺CG', 'OQC AOI', 'SI', 'SP1焊接', 'UMP-TK', 'ALT氣防檢測', '鈍化', 'Small Parts Assy', 'CNCLC2', 'CNC7.1', 'CNC MC1', 'Chassis貼膜組立連線', 'UMP-T4', 'CNCS', 'IQC貼膜連線', 'CNC A1', 'UMP-T2檢測', 'CNCLC1', 'CNC3.1', 'TrimtoSP', 'PVD', 'CNC MC3', 'CNC U2', 'CNC CF3', 'CNC7.5', 'CNC4', 'CNC1.1', 'CNC2.4', '固定齒焊接', '中板預推', 'CG組立', 'SPK組立', 'SPtoBG', 'SP焊接', 'CNC BP2', '支架焊接', 'LiPo灌膠連線', 'SI檢測', 'CNC6.1', 'CNCLC3', 'CNC1', 'PU', 'CNC4.1', '天准', 'CNC4.3', 'CNC7', 'CNC3', 'CNC2.2', 'CNC6.05', 'CNC2', 'CNC CF1', 'IQC AOI', 'IQC', '貼PSA-Foam 6P', 'Mic2Assy', '撕來料膜', 'CNC1.2', 'CNC7.05', 'CNC2.3', 'OQC 功能段連線', 'PVD前清洗', 'OQC功能段連線', '防水功能連線', 'Trim小件', 'ShimtoBG', '組立後大連線', 'Receiver貼合', 'CNC CF2', 'Rcam Assy', '天準', 'OQC貼膜連線', 'Ano', 'RT去毛刺', 'LiPo後大連線', 'CNC BP1', 'CNC6', 'BG Assy', 'CNC MC2', 'SPK&amp;RCVR組立', '噴Plasma-Primer 2P', 'CNC5', 'CNC4.2', 'CNCW', 'CNC8', 'RT去毛刺BG', 'CNC U1', 'CNC2.5', 'AOI', 'FQC', 'CNC A2'], '工站': ['LIPO靜置', '成品下料', 'BracetoTrim', 'Assy', 'RcamBGLoading', 'CNC2-4', 'CNC2-U', 'CNCLC2', 'CNC7.1', 'SPKMesh貼合', 'CNC MC1', 'UMP-T4', 'CNC4-N', '撕外保膜', '2P噴塗', 'PSA撕膜', '貼易撕膜', 'CNC A1', '母模上料', 'UMP-T2檢測', '下蓋板', 'CNCLC1', 'Chassis上料', 'BGPlasma', 'CNC3.1', 'CG Snap鎖螺絲', 'CNC2-B', 'CNC4-P', 'CNCS-1', 'LSR拆夾', 'CNC7-P', '等離子清洗', 'NG-收發料A', '貼L-Coner泡棉', 'PU2/3夾', 'CNC MC3', 'BG貼保護膜', 'CNC U2', 'CNC CF3', 'CNC7.5', 'CNC4', '貼出貨膜', '物流连线', 'Trim焊接組立（ML)', '貼Senser Shim', '保壓', 'Ring焊接', 'CG組立', 'U型支架焊接&amp;接地支架焊接', 'NG-收發料C', '封膠', 'SPtoBG', '天準下料', '按壓排線', '下料機', 'RT複檢', 'CNC1.2下小C', '公模外觀檢', 'CNC2上大U', 'SPPost-Welding-Dims-Measure', '治具組裝', 'DVA測試模組', '去膠口', 'ALT-Rcam', 'BG-IQC-Cosmetic-Inspection', 'Curing', 'CNC4.3', 'LIPO上料', 'CNC1.1上U', 'Ano上下挂', 'TSP測試模組', 'IQC-AOI對接', 'CNC1.1中板', 'CNC6.05', 'CNC CF1', 'ALT-PreRcam', '公膜NG下料', '小件焊後檢', 'PVD爐', 'Trim焊接組立(VR)', '撕排線膜', '撕離型膜', '組立後上料', 'UAT1ShimAssy', 'OQC貼膜下料', '貼GND', 'CNC2中板', '貼ALS膜', '貼PSA', '上蓋板', '拔膠塞', 'CNC W-D', 'CNC2.3-D', 'SPK貼合', 'CNC4.1-P', '撕膜', '貼DIC-LR泡棉', 'Mic2貼膜', '灌膠固化檢測', 'SPK RCVR ALT', 'ShimtoBG', 'Mic2BracketAssy', 'DP檢測', 'CNC2-1', 'Chassis組立', 'NG-收發料B', 'CNC1.2下大U', 'Ring焊後檢', '天準上料', '二次固化', 'PU-Band氣防檢測', 'CNC2.2-E', '貼RailTape', 'CNC BP1', 'CNC6', '6P上料', 'DP上料', 'CNC1.1-3', 'CNC2上小U', 'CNC2下大U', 'CNC5', 'CNC4.2', 'AOI外观检测', 'CNC W-B', 'CNC W-C', 'CNC8', 'CNC2.5', 'CNC2.2-F', 'BG-FQC-Cosmetic-Inspection', '貼Sensor', 'SPPlasma', '重工', 'CNC1.2-4', 'RT去毛刺CG', 'CNC2-2', 'AOI對接', '貼標籤紙', '撕平面膜', 'CNC1.2上大U', 'UVPU檢測', 'FangstoIsland-Welding', '防水中轉', 'LIPO拆夾', 'HAFtoBGAssy', 'HAFtoSmallPartRecheck', '母模外觀檢', 'Trim焊接組立(ML&MW)', 'UMP-TK下料', 'CNC1-I', 'Ano下胶塞', 'HAFtoTrimPlate', 'UMP-TK上料', '防水測試', '夾具拆裝', 'CNC2-3', 'AOI内观检测', 'CNC1.1-2', 'CNC1.1下U', 'RcamAOI', '支架貼合', 'Ano下飞杆', 'CNC2.2-B', 'TrimtoSP', 'CNC2.2-D', '貼VGA', 'Carrier拆夾', '貼Chin-DIC泡棉', '貼HOOK', '自動下料', 'IQC貼膜下料', 'CNC1.2-3', 'PU1夾', 'CNC2.3-B', 'HAFtoBGRecheck', '撕金屬膜', '合模', 'ASFtoBGAssy', 'CNC2.4', 'CNC1.2上小U', 'IQC外觀檢測', '貼GND膜', 'Shim焊接', '中板預推', '貼tape膜', '終檢PDCA-TSP', 'CNC2.2-C', 'Mic2MeshAssy', 'CNC BP2', 'Ano拆裝夾', '2D複檢', '小件焊接', 'Chassis下料', 'CNC1.2中板', 'CNC6-P', 'CNC1.2-2', '貼R-Coner泡棉', 'Trim焊接組立（MW)', 'CNC6.1', 'SmallSPtoBG', 'HAFtoFang', 'CNC1.2下小U', '6P下料', 'CNC5-P', 'CNC1.2上小C', 'ALS-DIC保壓', 'CNCLC3', 'CNC2-5', '水基清洗', 'CNC4.1', '貼DIC膜', 'CNC2.3-C', 'SP1', 'CNCS-2', 'IQC撕膜上料', 'CNC7', 'Mic2BracketDispense', 'CNC3', 'IQC貼膜保壓', 'Chassis保壓', 'LIPO下料', 'CNC1.2-5', '防水上料', 'Trim焊接組立(AV)', '貼Chin-Forhead泡棉', 'Washer組裝', '清膠', 'Ano上下料', '插膠塞', 'CNC7.05', 'LiPo後下料', '治具殘膠檢測', 'CNC1.1-1', 'Ring來料檢測', 'Trim貼外保護膜', 'TrimAssembly', '母模NG下料', 'Trim焊接組立（WM)', 'Ano上飞杆', 'Assy-CGBGO-Measure', '支架上料', '貼Display Shim', 'SIM ALT', '清洗', 'CNC6-S', '一次固化', 'Receiver貼合', 'Chassis組立靜置', 'CNC2-I', 'CNC CF2', 'CuringRecheck', 'CNC1.2-1', 'LiPo後上料', 'SmallPartPlasma', '灌膠', 'LCH ALT', 'CNC2.2-A', 'PU-SIM氣防檢測', 'SPPost-Welding', 'OQC外觀檢測', 'FangstoIsland-Welding-Dims-Measure', 'IQC撕膜下料', 'IQC貼膜上料', '裝夾', 'OQC貼膜上料', 'De-PU', 'De-OLRail', 'CNC MC2', '貼製程膜', '治具拆解', 'ASFtoBGAssyRecheck', '點膠', '貼旋風膜&OR膜', '功能下料', 'CNC2下小U', 'RT去毛刺BG', 'CNC U1', '折排線', '尺寸檢測', 'CNC1-U', 'Washer壓頭拆解', '貼Jindo Foam', 'IPQC-Welding', 'CNC A2'], '楼层': ['GL-C11-2F-B', 'GL-C12-1F', 'GL-A02-3F', 'GL-B12-1F', 'GL-C09-3F', 'GL-B05-3F', 'GL-B13-3F', 'GL-A01-1F', 'GL-C06-5F', 'GL-C11-1F', 'GL-B12-4F', 'GL-C04-1F', 'GL-C06-2F', 'GL-B13-1F', 'GL-C06-1F-A', 'GL-C11-3F', 'GL-C08-3F', 'GL-B05-4F', 'GL-C08-2F', 'GL-C05-4F', 'GL-C07-4F', 'GL-B11-1F', 'GL-C12-2F', 'GL-A01-4F', 'GL-C07-5F', 'GL-B13-4F', 'GL-C11-2F-A', 'GL-C06-4F', 'GL-C05-3F', 'GL-C10-4F', 'GL-C09-2F'], '厂区': ['GL']}, '指标': {'OEE': ['OEE', 'oee', 'oee指标', 'oee情况', '设备综合效率'], '时间稼动率': ['时间稼动率', '设备稼动率', '设备利用率', '设备开动率', '设备运行率'], '性能稼动率': ['性能稼动率'], '生产达成率': ['rate', '生产达成率', '生产计划完成率', '生产计划达成率', '生产效率'], '良率': ['yield', '良率', '良率指标', '良率情况', '产品良率', '成品率', '良品率', '良品率指标'], 'ct': ['ct', 'CT情况', 'CT时间', 'CT时间利用率', 'CT时间利用率情况', '机器CT', '机台CT'], '机台开机数': ['机台开机数量', '机台开机数目', '机台开机数'], '机台总数': ['机台总数', '机台数'], '机台开机占比': ['机台开机占比', '机台开机状态', '设备开机状态', '设备开机占比'], 'ct超标设备比例': ['ct超标设备比例', 'ct超标设备状态', 'ct超标设备'], '加工时间占比': ['加工时间占比', '加工时间占比指标', '加工时间占比情况', '加工时间占比指标'], '待机时间占比': ['待机时间占比', '待机时间占比指标', '待机时间占比情况', '待机时间占比指标'], '报警时间占比': ['报警时间占比', '报警时间占比指标', '报警时间占比情况', '报警时间占比指标'], '离线时间占比': ['离线时间占比', '离线时间占比指标', '离线时间占比情况', '离线时间占比指标'], '通讯异常时间占比': ['通讯异常时间占比', '通讯异常时间占比指标', '通讯异常时间占比情况', '通讯异常时间占比指标'], '调机时间占比': ['调机时间占比', '调机时间占比指标', '调机时间占比情况', '调机时间占比指标'], '暖机时间占比': ['暖机时间占比', '暖机时间占比指标', '暖机时间占比情况', '暖机时间占比指标'], '机台时间占比': ['总体时间分布', '综合时间分布', '总体时间占比情况', '整体时长分布', '机台时间占比'], '穴位数': ['穴位数', '一出N系数']}, '厂区': {'LK': ['兰考', 'LK'], 'HB': ['鹤壁', 'HB'], 'ZZK': ['综保区', '航空港区', '港区', 'APZ', 'ZZK'], 'GL': ['观澜', 'GL'], 'JC': ['晋城', 'JC'], 'TY': ['太原', 'TY'], 'LH': ['龙华', 'LH'], 'ZZC': ['加工区', '经开区', 'EPZ', 'ZZC'], 'GZ': ['贛州', 'GZ'], 'JY': ['济源', 'JY']}}\nconfig_json中，column为数据库字段的中文名称，column_db为数据库实际字段名称，value为数据库对应的取值，指标为对应指标的取值别名，厂区为各厂区的别名。\nquestion：请问今天量产阶段MCH产品各厂区的机台时间占比\npre_sql:{'日期': ['2024-03-02'], '条件': ['阶段=量产', '产品=MCH'], '指标': ['机台时间占比'], '分组': ['厂区']}\nsql：...，请帮我直接生成sql\n
"""

success,result,_=agent_execute_with_retry(query,chat_history=my_history)
my_history=my_history[-10:]
