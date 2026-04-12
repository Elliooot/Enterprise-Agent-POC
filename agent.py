import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

async def main():
    print("Starting and connecting to MCP server...")

    # Connect to server.py
    client = MultiServerMCPClient({
        "enterprise_server": {
            "command": "uv", 
            "args": ["run", "server.py"],
            "transport": "stdio"
        }
    })

    tools = await client.get_tools()
    print(f"Successfully loaded {len(tools)} tools: {[t.name for t in tools]}")

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the company's dedicated HR and IT assistant. Utilize tools effectively to solve problems for employees. If you encounter errors, honestly inform the user."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"), # Black box: Stores the agent's intermediate thinking and calling tools.
    ])

    # Assemble the Agent and Executor
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    while True:
        user_input = input("Enter Your Query: ")

        print("\n Agent start thinking and executing tasks: \n" + "-"*50)

        response = await agent_executor.ainvoke({
            "input": user_input,
            "chat_history": []
        })

        final_output = response["output"]
        if isinstance(final_output, list):
            texts = []
            for item in final_output:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
                elif isinstance(item, str):
                    texts.append(item)
            final_text = "".join(texts)
        else:
            final_text = str(final_output)

        print("\n" + "="*50 + "\n Response Message: \n" + final_text)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Session End.")