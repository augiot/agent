# requests请求访问api接口
import requests
import json

url = 'https://api.example.com/data'
data = {'key': 'value'}
headers = {'Content-Type': 'application/json'}

def post_request(url, data, headers):
    response = requests.post(url, data=json.dumps(data), headers=headers)
    # 打印响应内容
    # print(response.text)
    return  response.text


if __name__ == '__main__':
    url = 'http://10.251.172.138:7777/question2sql'
    data = {
    "user":"H2017871",
    "question":"能否告知進一周觀瀾廠區GL-C06-5F 237M機種的CNC6工站的oee數據",
    "semantic_message":"",
    "scene_code":"cnc_wmsc"
    }

    headers = {'Content-Type': 'application/json'}
    result = post_request(url, data, headers)
    result = json.loads(result) # 转为字典数据格式
    print(result)

