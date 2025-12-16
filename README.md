# HIREME
# Job Market Analysis for Data and Software Roles Using Web Scraping and APIs

# Overview
This project analyzes trends in the technology job market by collecting and examining job postings related to data science, machine learning, and software engineering roles. The project uses web scraping and public APIs to gather job listings, which are then cleaned, processed, analyzed, and visualized to identify patterns in job roles, required skills, geographic distribution, and salary trends. The objective of the project is to gain insights into hiring demand and regional distribution of technology focused jobs.

# Data Sources
The data for this project was collected using a combination of public APIs and web scraping techniques. The following sources were used:

RemoteOK      
Job data was collected using the RemoteOK public API. The API provides structured JSON data for remote job postings, including job titles, company names, locations, job descriptions, and salary information.

Remotive          
Job data was collected using the Remotive public API. This API provides structured access to remote job postings across multiple categories, including software development and data related roles.

These sources were selected due to their accessibility, structured data format, and reproducibility.

# Data Samples
Approximately 100 raw job postings were collected from all sources combined. After removing duplicate entries and incomplete records during the data cleaning process, approximately 260 job postings were retained for final analysis.

# Project Structure
The project is organized into modular components to ensure clarity and reproducibility.

# job_pipeline.py
Contains the core logic for data collection, cleaning, feature extraction, and preprocessing. All scraping and processing functions are implemented in this file.

# Nishkarsh_Mittal_Final_Project.ipynb
Jupyter notebook used primarily for visualization and presentation. The notebook imports functions from the pipeline file and focuses on analysis and visual interpretation of the results.

# jobs_raw.csv
Raw dataset containing combined job postings collected from all sources.

# jobs_processed.csv
Cleaned and processed dataset used for analysis and visualization.

# requirements.txt
List of Python dependencies required to run the project.

final_report.pdf
Final project report describing the methodology, analysis, results, and conclusions.

## Setup Instructions

# Prerequisites
Python version 3.9 or higher is required. An active internet connection is needed to access the public job APIs.

# Installing Dependencies
Install the required Python packages by running:

pip install -r requirements.txt

# Running the Project

## Data Collection and Processing
The core data collection and processing logic is implemented in job_pipeline.py. Data is collected and cleaned by calling the pipeline functions from the notebook.

Example usage:

from job_pipeline import collect_posts, clean_posts

raw_df = collect_posts()
processed_df = clean_posts(raw_df)

This step fetches job postings from all configured sources and prepares the dataset for analysis.

# Saving the Data
The collected and processed datasets can be saved as CSV files using:

raw_df.to_csv("jobs_raw.csv", index=False)
processed_df.to_csv("jobs_processed.csv", index=False)

# Analysis and Visualization
All analysis and visualizations are performed in the Jupyter notebook. The notebook includes visualizations such as:

Distribution of job postings by geographic region
Frequency of job roles
Demand for technical skills
Salary distributions by role and region

These visualizations are generated from the cleaned dataset and are fully reproducible.

# Reproducibility
All steps of data collection, cleaning, analysis, and visualization are reproducible by running the provided Python pipeline and notebook. Core logic is separated from visualization code to ensure modularity and adherence to good software engineering practices.

# Challenges and Limitations
The original project proposal included additional job platforms such as WeWorkRemotely and Himalayas. These platforms employ client side rendering and anti scraping mechanisms that prevented reliable data extraction using standard HTTP requests. To address these challenges and maintain reproducibility, the final implementation relies on job platforms that provide stable and publicly accessible APIs.

# Future Work
Future extensions of this project could include integrating additional job platforms with official APIs, applying natural language processing techniques for deeper analysis of job descriptions, performing time series analysis to study hiring trends over longer periods, and developing an interactive dashboard for real time exploration of job market data.

Author
Nishkarsh Mittal
University of Southern California
Email: nishkars@usc.edu
