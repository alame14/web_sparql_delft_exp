# Web-SPARQL Hybrid Query Evaluation  

This repository contains the dataset, source code, scripts, and results of experiments conducted on hybrid querying with Web-SPARQL.

## Repository Contents  

- **Query dataset** covering a usage scenario about purchasing books.  
- **Source code** for the tools and scripts used in the evaluation.  
- **Experimental results** analyzing microdata availability and Web-SPARQL query performance.  

This work aims to explore the feasibility and efficiency of hybrid querying over disparate data sources.  

## Running the Query Evaluation  

To execute the queries, follow these steps:

### 1. Setup the Working Directory  
Ensure that the input files are in the correct directory before executing the scripts:
- Place all query files inside the `working_files/dataset/complex_queries` folder.
- Ensure the `working_files/results` directory exists to store output results.

### 2. Configure Execution Parameters  
Modify the `run_complex_evaluation.py` script to set execution parameters:
- `log_level`: Set to `logging.INFO` or `logging.DEBUG` depending on verbosity needed.
- `exec_mode`: Choose between `'cold'` (fresh start) or `'hot'` (reuse cached data).
- `web_service`: Select from available web services (`BFP_CWTS`, `BFP_SWSS`, `DDG_WSS`).
- `web_extractor`: Choose an extraction method (`BFP_CWTME`, `W3_ME`).

### 3. Execute the Query Evaluation Script  
Run the script using:
```sh
python run_complex_evaluation.py
```
This will process multiple queries from the dataset and store the results in `working_files/results/`.

### 4. Execute Simple Query Evaluation  
For evaluating simple queries, run the following script:
```sh
python run_simple_evaluation.py
```
This will process specific query files from `working_files/dataset/simple_queries/` and generate corresponding result files in `working_files/results/`.

## Analyzing the Results  

### 1. Setup the Analysis Environment  
Ensure that the result files are correctly placed:
- The output of the query execution should be in `working_files/results_complex/` for complex queries and `working_files/results_simple/` for simple queries.
- The `working_files/stats` directory should exist to store analysis results.

### 2. Run the Analysis Script  
Execute the analysis script:
```sh
python scripts/analyzer_main_script.py
```
This script will:
- Process and link JSON data using `MicrodataOfferLinker` and `OfferFeatureLinker`.
- Count and collect global data values.
- Compute query execution statistics.
- Analyze execution times for both simple and complex queries.

### 3. Review the Analysis Output  
The analysis results will be stored in the `working_files/stats/` directory:
- `complex_data_counts.json`: Query data count statistics for complex queries.
- `simple_data_counts.json`: Query data count statistics for simple queries.
- `complex_data_values.json`: Extracted global values for complex queries.
- `simple_data_values.json`: Extracted global values for simple queries.
- `complex_query_stats.json`: Query execution statistics for complex queries.
- `simple_query_stats.json`: Query execution statistics for simple queries.
- `complex_time_stats.json`: Execution time analysis for complex queries.
- `simple_time_stats.json`: Execution time analysis for simple queries.

These files can be used to further analyze the efficiency and performance of hybrid queries over Web-SPARQL.

