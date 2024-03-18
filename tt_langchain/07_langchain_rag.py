import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


# 准备llm key
import os
API_KEY = "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"
os.environ["OPENAI_API_KEY"] = API_KEY

# 1. 数据准备阶段
# 1.1.文本加载
# Only keep post title, headers, and content from the full HTML.
bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs={"parse_only": bs4_strainer},
)
docs = loader.load()

# 1.2.文本切分
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)

# 1.3.向量存储
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

vectorstore = Chroma.from_documents(documents=all_splits, embedding=OpenAIEmbeddings())

# 2. 应用阶段
# 2.1.检索（Retrieval）
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

# 2.2.增强（Augmented）
from langchain import hub
prompt = hub.pull("rlm/rag-prompt")

# 2.3.生产 (Generation)
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

rag_chain = (
    {"context": retriever,  "question": RunnablePassthrough()} 
    | prompt 
    | llm
    | StrOutputParser() 
)
rag_chain.invoke("What is Task Decomposition?")

