import asyncio
from typing import List
from typing_extensions import Annotated
import json
from config import *
from autogen import AssistantAgent, ConversableAgent, UserProxyAgent
from util import _call_tavily_search_api

# Termination message function
def is_termination_msg(x):
    content = x.get("content", "")
    return content and content.rstrip().endswith("TERMINATE")

orchestrator_agent = ConversableAgent(
    name="Orchestrator",
    system_message=ORCHESTRATOR_SYSTEM_MSG,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg,
    code_execution_config=False,
    llm_config=CEREBRAS_CONFIG[0],
    description="An orchestrator agent that manages " \
    "a team of expert agents to accomplish a user's goal.",
)

search_agent = AssistantAgent(
    name="SearchAgent",
    system_message=SEARCH_PROMPT,
    llm_config=CEREBRAS_CONFIG[1],
    description="A web search agent that finds relevant information on the internet.",
    is_termination_msg=is_termination_msg,
)

analyst_agent = AssistantAgent(
    name="AnalystAgent",
    system_message=ANALYST_PROMPT,
    llm_config=CEREBRAS_CONFIG[2],
    description="An expert analyst agent that specializes in analyzing and synthesizing information from results of a web search.",
    is_termination_msg=is_termination_msg,
)



@orchestrator_agent.register_for_execution()
@search_agent.register_for_llm(description="Perform a web search")
def web_search(
    query: Annotated[str, "Search query string"],
    num_results: Annotated[int, "Number of results to return"] = 5,
) -> str:
    """
    Function that performs web search directly.
    Return a JSON-serializable string.
    """
    data = _call_tavily_search_api(query=query, num_results=num_results)
    return json.dumps(data)



async def main():
    
    tasks = [
    """Research recent articles on battery recycling advances and summarize key points from the top 5 results.""",
    """Based on the search results, analyze the current trends and challenges in battery recycling.""",
    ]
    
    res = await orchestrator_agent.a_initiate_chats(  
            [
                {
                    "chat_id": 1,
                    "recipient": search_agent,
                    "message": tasks[0],
                    "silent": False,
                    "summary_method": "last_msg",
                },
                {
                    "chat_id": 2,
                    "prerequisites": [1],
                    "recipient": analyst_agent,
                    "message": tasks[1],
                    "silent": False,
                    "summary_method": "last_msg",
                },
            ]
        )


if __name__ == "__main__":
    asyncio.run(main())
