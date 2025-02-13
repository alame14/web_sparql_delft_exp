import os
import glob
import tempfile
import shutil

from microdata_offer_linker import MicrodataOfferLinker
from offer_feature_linker import OfferFeatureLinker
from data_counter import DataCounter
from global_values_collector import GlobalValuesCollector
from query_stats_calculator import QueryStatsCalculator
from times_analyzer import TimesAnalyzer

if __name__ == '__main__':
    
    # Data File Definition
    base_folder = 'working_files'
    stats_folder = os.path.join(base_folder, 'stats')
    os.makedirs(stats_folder, exist_ok=True)

    data_ref = 'complex'  # simple, complex
    data_folder = os.path.join(base_folder, f'results_{data_ref}')

    # Defining output files for statistics (stored in stats_folder)
    query_count_file = os.path.join(stats_folder, f"{data_ref}_data_counts.json")
    values_file = os.path.join(stats_folder, f"{data_ref}_data_values.json")
    query_stats_file = os.path.join(stats_folder, f"{data_ref}_query_stats.json")
    time_stats_file = os.path.join(stats_folder, f"{data_ref}_time_stats.json")

    # Creating a temporary folder for new JSON files
    temp_dir = tempfile.mkdtemp()

    try:
        # Copy contents from data_folder to temp_dir
        temp_data_folder = os.path.join(temp_dir, f'results_{data_ref}')
        shutil.copytree(data_folder, temp_data_folder, dirs_exist_ok=True)
        
        # Linking and renaming JSON files (in temp_dir)
        json_files = glob.glob(os.path.join(temp_data_folder, "*.json"))
        for json_file in json_files:
            linker = MicrodataOfferLinker()
            linker.process(json_file, json_file)
        for json_file in json_files:
            linker = OfferFeatureLinker()
            linker.process(json_file, json_file)

        # Data Count and collect
        counter = DataCounter()
        query_count = counter.process(temp_data_folder, query_count_file)
        collector = GlobalValuesCollector()
        collector.process(temp_data_folder, values_file)

        # Query Statistics
        calculator = QueryStatsCalculator()
        calculator.compute_stats(query_count_file, values_file, query_stats_file)

        # Time Statistics
        analyzer = TimesAnalyzer()
        analyzer.process_folder(temp_data_folder, time_stats_file)

        print(f"Temporary JSON files have been processed in: {temp_dir}")
        print(f"Statistics files are stored in: {stats_folder}")

    finally:
        # Removing the temporary folder and new JSON files
        shutil.rmtree(temp_dir)
