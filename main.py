import asyncio
from typing import List
from typing_extensions import Annotated
import json
from config import *
from autogen import AssistantAgent, ConversableAgent, UserProxyAgent
from util import _call_tavily_search_api, create_plot, generate_pdf_report

# Termination message function
def is_termination_msg(x):
    content = x.get("content", "")
    return content and content.rstrip().endswith("TERMINATE")

data_analyst_agent = AssistantAgent(
    name="DataAnalystAgent",
    system_message=DATA_ANALYST_PROMPT,
    llm_config=CEREBRAS_CONFIG[2],
    description="A data analytics expert agent that can analyze data and create visualizations.",
    is_termination_msg=is_termination_msg,
)
orchestrator_agent = UserProxyAgent(
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


@orchestrator_agent.register_for_execution()
@data_analyst_agent.register_for_llm(description="Create a plot from data")
def plot_data(
    data: Annotated[dict, "Data to plot with 'x' and 'y' keys"],
    plot_type: Annotated[str, "Type of plot (bar, line, scatter, pie)"],
    title: Annotated[str, "Title of the plot"] = "Data Visualization",
    xlabel: Annotated[str, "Label for x-axis"] = "X-axis",
    ylabel: Annotated[str, "Label for y-axis"] = "Y-axis",
    filename: Annotated[str, "Filename to save the plot"] = "plot.png"
) -> str:
    """
    Function that creates a plot from provided data and saves it to a file.
    Returns the filename of the saved plot.
    """
    return create_plot(data, plot_type, title, xlabel, ylabel, filename)


@orchestrator_agent.register_for_execution()
@data_analyst_agent.register_for_llm(description="Generate a PDF report with analysis results and plots")
def generate_pdf_report_tool(
    analyst_response: Annotated[str, "The response from the analyst agent"],
    plot_filenames: Annotated[List[str], "List of filenames of plots to include in the report"] = [],
    report_filename: Annotated[str, "Filename for the generated PDF report"] = "report.pdf",
    report_title: Annotated[str, "Title for the PDF report"] = "Analysis Report"
) -> str:
    """
    Function that generates a PDF report with the analyst's response and any generated plots.
    Returns the filename of the generated PDF report.
    """
    return generate_pdf_report(analyst_response, plot_filenames, report_filename, report_title)


async def main():

    tasks = [
"""Research recent articles on battery recycling advances and summarize key points from the top 5 results.""",
"""Based on the search results, analyze the current trends and challenges in battery recycling, market share of different battery types.""",

    ]
    
    # First, let's initiate the search and analysis
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
                {
                    "chat_id": 3,
                    "prerequisites": [2],
                    "recipient": data_analyst_agent,
                    "message": f"Based on the following analysis from the analyst agent, if needed, create visualization(s) and save them as png files. Then write a report using the following analysis and include any available plots when appropriate.",
                    "silent": False,
                    "summary_method": "last_msg",
                },
            ]
        )
    

if __name__ == "__main__":
    asyncio.run(main())
