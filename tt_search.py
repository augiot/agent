# The integration lives in the langchain-community package. We also need to install the tavily-python package itself.
# pip install -U langchain-community tavily-python
# We also need to set our Tavily API key.
import getpass
import os

api_key =  "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" # getpass.getpass()
# print(api_key)
os.environ["TAVILY_API_KEY"] = api_key
os.environ['TAVILY_API_KEY']='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'    # travily搜索引擎api key


from langchain_community.tools.tavily_search import TavilySearchResults
search = TavilySearchResults(max_results=3)
search.description='这是一个类似谷歌和百度的搜索引擎，搜索知识、天气、股票、电影、小说、百科等都是支持的哦，如果你不确定就应该搜索一下，谢谢！s'


# anwser = search.run("北京今天天气预报")
# anwser = search.invoke("北京今天天气预报")
anwser = search.invoke(input={"query": "北京今天天气预报"})
print(anwser)
