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
    Create a plot based on the provided data and save it to a file in the plots folder.
    Returns the filename of the saved plot.
    """
    import os
    
    # Create plots directory if it doesn't exist
    plots_dir = "plots"
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    
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
    
    # Save plot in plots folder
    filepath = os.path.join(plots_dir, filename)
    plt.savefig(filepath)
    plt.close()  # Close the figure to free memory
    
    return filepath


def generate_pdf_report(
    analyst_response: Annotated[str, "The response from the analyst agent"],
    plot_filenames: Annotated[List[str], "List of filenames of plots to include in the report"] = [],
    report_filename: Annotated[str, "Filename for the generated PDF report"] = "report.pdf",
    report_title: Annotated[str, "Title for the PDF report"] = "Analysis Report"
) -> str:
    """
    Generate a professional PDF report that includes the analyst's response and any generated plots.
    
    Args:
        analyst_response (str): The response text from the analyst agent
        plot_filenames (List[str]): List of filenames of plots to include in the report
        report_filename (str): Filename for the generated PDF report
        report_title (str): Title for the PDF report
        
    Returns:
        str: The filename of the generated PDF report
    """
    
    # Clean text to handle Unicode characters properly
    def clean_text(text):
        if not text:
            return ""
        # Replace non-breaking hyphen with regular hyphen
        return text.replace("\u2011", "-")
    
    class PDF(FPDF):
        def __init__(self, title):
            super().__init__()
            self.report_title = title
            
        def header(self):
            # Set font for header
            self.set_font('Times', 'B', 16)
            # Add title
            self.cell(0, 10, self.report_title, border=0, ln=1, align='C')
            # Add line break
            self.ln(8)
            
        def footer(self):
            # Position at 1.5 cm from bottom
            self.set_y(-15)
            # Set font for footer
            self.set_font('Times', 'I', 8)
            # Add page number
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', border=0, ln=0, align='C')
            
        def add_report_date(self):
            # Add report date
            from datetime import datetime
            self.set_font('Times', 'I', 10)
            self.cell(0, 10, f"Report generated on: {datetime.now().strftime('%B %d, %Y')}", border=0, ln=1, align='R')
            self.ln(5)
            
        def add_section_title(self, title):
            # Set font for section title
            self.set_font('Times', 'B', 14)
            # Add section title with underline
            self.cell(0, 10, title, border=0, ln=1, align='L')
            # Add line
            self.set_draw_color(0, 0, 0)  # Black line
            self.line(self.get_x(), self.get_y(), self.w - self.r_margin, self.get_y())
            # Add line break
            self.ln(8)
            
        def add_body_text(self, text):
            # Set font for body text
            self.set_font('Times', '', 12)
            # Clean text to handle Unicode characters
            cleaned_text = clean_text(text)
            # Add body text
            self.multi_cell(0, 8, cleaned_text)
            # Add line break
            self.ln(8)
            
        def add_plot_title(self, title):
            # Set font for plot title
            self.set_font('Times', 'B', 12)
            # Add plot title
            self.cell(0, 10, title, border=0, ln=1, align='C')
            # Add line break
            self.ln(5)

    # Create PDF instance with UTF-8 support
    pdf = PDF(report_title)
    pdf.set_auto_page_break(auto=True, margin=25)
    
    # Set alias for total page numbers
    pdf.alias_nb_pages()
    
    # Add first page
    pdf.add_page()
    
    # Add report date
    pdf.add_report_date()
    
    # Add executive summary section
    pdf.add_section_title("Executive Summary")
    pdf.add_body_text(analyst_response)
    
    # Add data visualization section if plots exist
    if plot_filenames:
        pdf.add_page()  # Start plots on a new page
        pdf.add_section_title("Data Visualizations")
        
        for i, plot_filename in enumerate(plot_filenames, 1):
            
            # Add a title for the plot
            # Extract just the filename without extension for the title
            plot_name = os.path.basename(plot_filename).replace('.png', '').replace('_', ' ').title()
            pdf.add_plot_title(f"Figure {i}: {plot_name}")
            
            # Check if file exists and add the plot image
            try:
                if os.path.exists(plot_filename):
                    # Ensure the image fits on the page with proper margins
                    pdf.image(plot_filename, w=160, h=90, type='PNG')
                else:
                    # If image file doesn't exist, add a note about it
                    pdf.set_font('Times', 'I', 10)
                    pdf.cell(0, 10, f"Could not include image: File '{plot_filename}' not found", border=0, ln=1, align='L')
            except Exception as e:
                # If image cannot be added for any other reason, add a note about it
                pdf.set_font('Times', 'I', 10)
                pdf.cell(0, 10, f"Could not include image: {str(e)}", border=0, ln=1, align='L')
            
            pdf.ln(15)
    
    # Save the PDF
    pdf.output(report_filename)
    return report_filename
