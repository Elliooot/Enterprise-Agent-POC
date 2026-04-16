import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

async def main():
    print("Starting and connecting to MCP server...")

    client = MultiServerMCPClient({
        "enterprise_server": {
            "command": "uv", 
            "args": ["run", "server.py"],
            "transport": "stdio"
        }
    })

    tools = await client.get_tools()
    print(f"Successfully loaded {len(tools)} tools")

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemma-4-26b-a4b-it", temperature=0)

    # Need to explicitly tell LLM which tools can be used in LangGraph
    llm_with_tools = llm.bind_tools(tools)

    # Start Constructing LangGraph State Machine

    # Node A: Node to think and make decision (Agent Node)
    async def call_model(state: MessagesState):
        """Read current chat status and let LLM decides the next move"""
        system_msg = SystemMessage(content="You are the company's dedicated HR and IT assistant. Utilize tools effectively to solve problems for employees. If you encounter errors, honestly inform the user.")

        messages = [system_msg] + state['messages']
        response = await llm_with_tools.ainvoke(messages)
        # Wrap LLM response into Dict, LangGraph will append it to conversation history
        return {"messages": [response]}
    
    # Node B: Node to execute tools (Tool Node)
    tool_node = ToolNode(tools)

    # Draw the StateGraph
    # MessagesState is the built-in state structure, specifically used for secure transmission of chat history
    workflow = StateGraph(MessagesState)

    # Add Nodes to Graph
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent") # Always start by thinking at the agent node

    # Conditional Edges
    workflow.add_conditional_edges("agent", tools_condition)

    # The results have to be brought back to agent node for LLM to summarize after executing tools
    workflow.add_edge("tools", "agent")

    app = workflow.compile(checkpointer=MemorySaver())

    config = {"configurable": {"thread_id": "session_001"}}

    while True:
        user_input = input(">>> ")
        print("\n Agent start thinking and executing tasks: \n" + "-"*50)

        human_msg = HumanMessage(content=user_input)

        # astream will print the results of every node execution in stream
        async for event in app.astream({"messages": [human_msg]}, config=config, stream_mode="values"):
            last_message = event["messages"][-1]

            if last_message.type == "ai":
                if last_message.tool_calls:
                    print(f"[AI decides to call tool]: {last_message.tool_calls[0]['name']}")
                elif last_message.content:
                    if isinstance(last_message.content, list):
                        for block in last_message.content:
                            if block.get("type") == "thinking":
                                print(f"[AI Internal Thinking Process]:\n{block.get('thinking')}\n")
                            elif block.get("type") == "text":
                                print(f"[AI Final Response]: {block.get('text')}")
                    else:
                        print(f"[AI Final Response]: {last_message.content}")
            elif last_message.type == "tool":
                print(f"[Tool Execution Result]: {last_message.name} -> Successfully getting info")
        
        print("\n" + "="*50 + "\n Mission End")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSession End.")