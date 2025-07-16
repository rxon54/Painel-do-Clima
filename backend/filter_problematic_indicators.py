#!/usr/bin/env python3
"""
Filter Problematic Indicators Module

This module processes city-specific JSON files and creates new files containing only
the indicators that are identified as problematic based on their current state and
future trends.

Usage:
    python filter_problematic_indicators.py <state_abbr> <city_id> <input_data_dir>

Example:
    python filter_problematic_indicators.py PR 5329 data/LLM
"""

import os
import json
import argparse
import logging
from typing import Dict, Any, List


def setup_logging():
    """Configure logging for the filtering process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('filter_problematic_indicators.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def is_indicator_problematic(indicator_data: Dict[str, Any]) -> bool:
    """
    Determines if an indicator is problematic based on its current state and future trends.
    An indicator is problematic if its current state is not good, or if it is good but worsens in the future.
    
    Args:
        indicator_data: Dictionary containing indicator information including value, 
                       proporcao_direta, rangelabel, and future_trends
    
    Returns:
        bool: True if the indicator is problematic, False otherwise
    """
    proporcao_direta = int(indicator_data.get("proporcao_direta", "-1"))
    current_value = indicator_data.get("value")
    rangelabel = indicator_data.get("rangelabel")
    future_trends = indicator_data.get("future_trends", {})

    if current_value is None:
        return False  # Cannot assess without a current value

    # Define what constitutes a "good" rangelabel for each proporcao_direta
    # These are the states we want to FILTER OUT (i.e., not problematic in current state)
    GOOD_RANGELABELS_FOR_WORSE_IS_HIGHER = ["Baixo", "Muito baixo"]
    GOOD_RANGELABELS_FOR_BETTER_IS_HIGHER = ["Alto", "Muito alto"]

    # Check if the indicator is "good" in its current state based on rangelabel
    is_currently_good_by_label = False
    if proporcao_direta == 1:  # Higher value is worse, so "Baixo" or "Muito baixo" are good
        if rangelabel in GOOD_RANGELABELS_FOR_WORSE_IS_HIGHER:
            is_currently_good_by_label = True
    elif proporcao_direta == 0:  # Higher value is better, so "Alto" or "Muito alto" are good
        if rangelabel in GOOD_RANGELABELS_FOR_BETTER_IS_HIGHER:
            is_currently_good_by_label = True

    # If it is not currently good by label, it is problematic
    if not is_currently_good_by_label:
        return True

    # If it is currently good by label, check if it worsens in the future
    for year_str in sorted(future_trends.keys()):  # Iterate through years to check for worsening trends
        trend_data = future_trends[year_str]
        future_value = trend_data.get("value")
        
        if future_value is not None:
            if proporcao_direta == 1:  # Higher is worse
                if future_value > current_value:  # If future value is numerically higher (worse)
                    return True  # It is problematic due to worsening trend
            elif proporcao_direta == 0:  # Higher is better
                if future_value < current_value:  # If future value is numerically lower (worse)
                    return True  # It is problematic due to worsening trend

    return False  # It is currently good and does not worsen in the future


def filter_city_indicators(state_abbr: str, city_id: str, input_data_dir: str, logger: logging.Logger) -> None:
    """
    Process all JSON files for a specific city and create filtered versions containing
    only problematic indicators.
    
    Args:
        state_abbr: State abbreviation (e.g., 'PR')
        city_id: City identifier (e.g., '5329')
        input_data_dir: Base directory containing the input data (e.g., 'data/LLM')
        logger: Logger instance for output messages
    """
    city_data_path = os.path.join(input_data_dir, state_abbr, str(city_id))
    output_data_path = os.path.join(city_data_path, "problematic_indicators_only")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_data_path, exist_ok=True)
    
    if not os.path.exists(city_data_path):
        logger.error(f"Input directory does not exist: {city_data_path}")
        return
    
    logger.info(f"Processing city {city_id} in state {state_abbr}")
    logger.info(f"Input path: {city_data_path}")
    logger.info(f"Output path: {output_data_path}")
    
    total_indicators_processed = 0
    total_problematic_indicators = 0
    files_processed = 0
    
    # Process each JSON file in the city directory
    for filename in os.listdir(city_data_path):
        if filename.endswith(".json"):
            filepath = os.path.join(city_data_path, filename)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    sector_data = json.load(f)
                
                original_indicators = sector_data.get("indicators", [])
                total_indicators_processed += len(original_indicators)
                
                # Filter indicators to keep only problematic ones
                problematic_indicators = [
                    ind for ind in original_indicators 
                    if is_indicator_problematic(ind)
                ]
                
                total_problematic_indicators += len(problematic_indicators)
                
                # Create new sector data with only problematic indicators
                filtered_sector_data = sector_data.copy()
                filtered_sector_data["indicators"] = problematic_indicators
                
                # Add metadata about the filtering process
                filtered_sector_data["filter_metadata"] = {
                    "original_indicator_count": len(original_indicators),
                    "problematic_indicator_count": len(problematic_indicators),
                    "filter_applied": "problematic_indicators_only",
                    "filter_criteria": "Current state not good OR good but worsens in future"
                }
                
                # Save filtered data to output directory
                output_filepath = os.path.join(output_data_path, filename)
                with open(output_filepath, "w", encoding="utf-8") as f:
                    json.dump(filtered_sector_data, f, indent=2, ensure_ascii=False)
                
                files_processed += 1
                logger.info(f"Processed {filename}: {len(original_indicators)} -> {len(problematic_indicators)} indicators")
                
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
                continue
    
    # Summary statistics
    logger.info(f"Processing complete for city {city_id}")
    logger.info(f"Files processed: {files_processed}")
    logger.info(f"Total indicators processed: {total_indicators_processed}")
    logger.info(f"Total problematic indicators found: {total_problematic_indicators}")
    logger.info(f"Problematic indicator rate: {(total_problematic_indicators/total_indicators_processed)*100:.1f}%")


def filter_all_cities_in_state(state_abbr: str, input_data_dir: str, logger: logging.Logger) -> None:
    """
    Process all cities in a given state.
    
    Args:
        state_abbr: State abbreviation (e.g., 'PR')
        input_data_dir: Base directory containing the input data (e.g., 'data/LLM')
        logger: Logger instance for output messages
    """
    state_data_path = os.path.join(input_data_dir, state_abbr)
    
    if not os.path.exists(state_data_path):
        logger.error(f"State directory does not exist: {state_data_path}")
        return
    
    cities_processed = 0
    
    # Process each city directory in the state
    for city_id in os.listdir(state_data_path):
        city_path = os.path.join(state_data_path, city_id)
        
        # Skip if not a directory or if it's the problematic_indicators_only directory
        if not os.path.isdir(city_path) or city_id == "problematic_indicators_only":
            continue
            
        filter_city_indicators(state_abbr, city_id, input_data_dir, logger)
        cities_processed += 1
    
    logger.info(f"Processed {cities_processed} cities in state {state_abbr}")


def main():
    """Main function to handle command line arguments and execute filtering."""
    parser = argparse.ArgumentParser(
        description="Filter problematic indicators from city climate data"
    )
    parser.add_argument(
        "state_abbr",
        help="State abbreviation (e.g., PR, SC)"
    )
    parser.add_argument(
        "city_id",
        nargs="?",
        help="City ID to process (optional - if not provided, processes all cities in state)"
    )
    parser.add_argument(
        "input_data_dir",
        help="Input data directory (e.g., data/LLM)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    try:
        if args.city_id:
            # Process specific city
            filter_city_indicators(args.state_abbr, args.city_id, args.input_data_dir, logger)
        else:
            # Process all cities in the state
            filter_all_cities_in_state(args.state_abbr, args.input_data_dir, logger)
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
