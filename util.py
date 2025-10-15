import os
import json
import requests
import matplotlib.pyplot as plt
import numpy as np
from typing import List
from typing_extensions import Annotated
from fpdf import FPDF
def _call_google_search_api(query: str, num_results: int = 5) -> dict:
    """
    Perform a Google Custom Search and return structured results.
    Requires:
      - GOOGLE_API_KEY (from https://console.cloud.google.com/apis/credentials)
      - GOOGLE_CSE_ID (Custom Search Engine ID)
    """
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID in environment variables")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": min(num_results, 10),  # Google allows up to 10 results per request
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet"),
        })

    return {
        "query": query,
        "results": results,
    }


def _call_tavily_search_api(query: str, num_results: int = 5) -> dict:
    """
    Free web search using Tavily API.
    """
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    if not TAVILY_API_KEY:
        raise ValueError("Missing TAVILY_API_KEY in environment variables")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "num_results": num_results,
        "include_answer": True,
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()

    # Format response
    return {
        "query": query,
        "summary": data.get("answer"),
        "results": [
            {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
            for r in data.get("results", [])
        ],
    }


def create_plot(
    data: Annotated[dict, "Data to plot"],
    plot_type: Annotated[str, "Type of plot to create (bar, line, scatter, pie)"],
    title: Annotated[str, "Title of the plot"] = "Data Visualization",
    xlabel: Annotated[str, "Label for x-axis"] = "X-axis",
    ylabel: Annotated[str, "Label for y-axis"] = "Y-axis",
    filename: Annotated[str, "Filename to save the plot"] = "plot.png"
) -> str:
    """
    Create a plot based on the provided data and save it to a file.
    Returns the filename of the saved plot.
    """
    # Extract data
    x_data = data.get("x", [])
    y_data = data.get("y", [])
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Create plot based on type
    if plot_type == "bar":
        plt.bar(x_data, y_data)
    elif plot_type == "line":
        plt.plot(x_data, y_data)
    elif plot_type == "scatter":
        plt.scatter(x_data, y_data)
    elif plot_type == "pie":
        plt.pie(y_data, labels=x_data, autopct='%1.1f%%')
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")
    
    # Add labels and title
    if plot_type != "pie":  # Pie charts don't typically have axis labels
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
    plt.title(title)
    
    # Save plot
    plt.savefig(filename)
    plt.close()  # Close the figure to free memory
    
    return filename


def generate_pdf_report(
    analyst_response: Annotated[str, "The response from the analyst agent"],
    plot_filenames: Annotated[List[str], "List of filenames of plots to include in the report"] = [],
    report_filename: Annotated[str, "Filename for the generated PDF report"] = "report.pdf"
) -> str:
    """
    Generate a PDF report that includes the analyst's response and any generated plots.
    
    Args:
        analyst_response (str): The response text from the analyst agent
        plot_filenames (List[str]): List of filenames of plots to include in the report
        report_filename (str): Filename for the generated PDF report
        
    Returns:
        str: The filename of the generated PDF report
    """
    # Clean the text to remove or replace unsupported Unicode characters
    def clean_text(text):
        # Replace non-breaking hyphen with regular hyphen
        return text.replace("\u2011", "-")
    
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Use built-in fonts but clean the text to avoid Unicode issues
    # Add title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Research Analysis Report", ln=True, align="C")
    pdf.ln(10)
    
    # Add analyst response
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, clean_text(analyst_response))
    pdf.ln(10)
    
    # Add plots if any
    for plot_filename in plot_filenames:
        if os.path.exists(plot_filename):
            # Add a title for the plot
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"Plot: {plot_filename}", ln=True)
            pdf.ln(5)
            
            # Add the plot image
            pdf.set_font("Arial", "", 12)
            try:
                # Ensure the image fits on the page
                pdf.image(plot_filename, w=180)
                pdf.ln(10)
            except Exception as e:
                # If image cannot be added, add a note about it
                pdf.cell(0, 10, f"Could not include image: {str(e)}", ln=True)
                pdf.ln(10)
    
    # Save the PDF
    pdf.output(report_filename)
    return report_filename
