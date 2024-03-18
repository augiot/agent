import os
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.llms import OpenAI

API_KEY = "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"
os.environ["OPENAI_API_KEY"] = API_KEY
 
# First, let's load the language model we're going to use to control the agent.
llm = OpenAI(temperature=0)
 
# Next, let's load some tools to use. Note that the `llm-math` tool uses an LLM, so we need to pass that in.
tools = load_tools(["pal-math"], llm=llm)
 
# Finally, let's initialize an agent with the tools, the language model, and the type of agent we want to use.
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
 
# Now let's test it out!
# agent.run("What was the high temperature in SF yesterday in Fahrenheit? What is that number raised to the .023 power?")
agent.run("3的0.23次方是多少")