# This file contains utilities for handling the older TXT format census data files.
# The TXT format was used from 2009 to October 2019.
# Usage
# records = list(parse_census_stream("data.txt"))
# df = pd.DataFrame(records)


from pathlib import Path
import pandas as pd
import logging

# w = 'overwrite' mode for each run
logging.basicConfig(filename="parser.log", 
                    filemode='w', 
                    level=logging.DEBUG)
logger = logging.getLogger()


def _parse_census_stream(file_path: Path | str):
    code_start=49
    name_start=10

    logger.debug(f"Starting to parse census TXT format file: {file_path}")
    # Define exact slice positions (based on your screenshot)
    # You need to confirm the exact start index of the "GA" on line 2
    SLICE_CODE = slice(0, 9)
    SLICE_NAME = slice(name_start, code_start) # Adjust end based on where numbers typically start
    SLICE_NAME_MULTI_LINE = slice(0, code_start) # For continuation lines
    SLICE_DATA = slice(code_start, None) # The rest of the line

    logger.debug(f"Parsing file: {file_path}")
    
    with open(file_path, 'r', encoding='latin1') as f:
        buffer_code = None
        buffer_name = None
        line_no = 0
        for line in f:
            line_no += 1

            logger.debug(f"Processing line {line_no}: {line.rstrip()}")

            if(line_no < 12): 
                continue # Skip header lines  # noqa: E701
            if not line.strip(): 
                continue # Skip empty  # noqa: E701
            # If the line starts with '*', we are done with the data.
            if line.strip().startswith('*'): 
                break
            # Check if the line STARTS with a Code (Digits) or Spaces
            # The first few chars of the continuation line appear to be spaces
            has_leading_code = line[0].isdigit()

            if has_leading_code:
                # SCENARIO: New Record Start
                
                # 1. If we have a buffered record waiting, it was a "Single Line" record. Yield it.
                if buffer_code: 
                    yield {
                        "code": buffer_code, 
                        "name": buffer_name, 
                        "raw_data": "" # Empty data means we need to handle "Single Line with Data" logic
                    }

                # 2. Check if this new line has data numbers at the end
                # Heuristic: Does the end of the line look like numbers?
                line_has_data = any(char.isdigit() for char in line[code_start:])
                
                if line_has_data:
                    # It's a complete Single Line Record
                    yield {
                        "code": line[SLICE_CODE].strip(),
                        "name": line[SLICE_NAME].strip(),
                        "raw_data": line[SLICE_DATA]
                    }
                    buffer_code = None # Reset
                else:
                    # It's a Header Line (Wrapped). Buffer it and wait for line 2.
                    buffer_code = line[SLICE_CODE].strip()
                    buffer_name = line[name_start:].strip() # <-- UNBOUNDED SLICE

            else:
                # SCENARIO: Continuation Line (Starts with spaces)
                logger.debug(f"Continuation line detected at line {line_no}.")
                if buffer_code:
                    # Merge with buffer
                    if(buffer_name is None):
                        raise ValueError(f"Buffer name is None when processing continuation line at line {line_no}")
                    full_name = buffer_name + " " + line[SLICE_NAME_MULTI_LINE].strip()
                    logger.debug(f"Continuation line found. Merged name: {full_name}")
                    raw_data = line[SLICE_DATA]
                    logger.debug(f"Continuation line raw data: {raw_data.strip()}")
                    yield {
                        "code": buffer_code, 
                        "name": full_name, 
                        "raw_data": raw_data
                    }
                    buffer_code = None # Buffer consumed
                else:
                    # Orphaned continuation line? (Shouldn't happen)
                    continue
    logger.debug("Finished parsing file.")

def convert_parsed_record(record):
    """
    Convert a parsed record into a structured dictionary.
    This function can be expanded based on specific data processing needs.
    """
    # Example conversion logic (to be customized)
    data_values = record["raw_data"].strip().split()
    code_values = record["code"].strip().split()

    if len(code_values) != 2:
        logger.error(f"Unexpected code format: {record['code']}")
        raise ValueError(f"Unexpected code format: {record['code']}")
    if len(data_values) != 7:
        logger.error(f"Unexpected data length: {record['raw_data']}")
        raise ValueError(f"Unexpected data length: {record['raw_data']}")
    for value in data_values:
        if not value.replace('.', '', 1).isdigit():
            logger.error(f"Non-numeric data value found: {value}")
            raise ValueError(f"Non-numeric data value found: {value}")
        
    structured_record = {
        "CSA": code_values[0],
        "CBSA": code_values[1],
        "Name": record["name"],
        "Total": int(data_values[0]),
        "1 Unit": int(data_values[1]),
        "2 Unit": int(data_values[2]),
        "3 & 4 Units": int(data_values[3]),
        "5 or more Units": int(data_values[4]),
        "Num of Structures With 5 Units or more": int(data_values[5]),
        "Monthly Coverage Percent": float(data_values[6]),
    }
    return structured_record


def convert_census_txt_to_csv(txt_path: Path, csv_path: Path) -> None:
    """Convert the census TXT format file to a cleaned CSV file."""
    import pandas as pd

    records = []
    for parsed_record in _parse_census_stream(txt_path):
        try:
            structured_record = convert_parsed_record(parsed_record)
            records.append(structured_record)
        except ValueError as e:
            logger.error(f"Error converting record: {e}")

    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False)
    logger.debug(f"Converted TXT file {txt_path} to CSV file {csv_path}")


def convert_census_txt_to_data_frame(txt_path: Path) -> 'pd.DataFrame':
    """Convert the census TXT format file to a pandas DataFrame."""
    import pandas as pd

    records = []
    for parsed_record in _parse_census_stream(txt_path):
        try:
            structured_record = convert_parsed_record(parsed_record)
            records.append(structured_record)
        except ValueError as e:
            logger.error(f"Error converting record: {e}")

    df = pd.DataFrame(records)
    return df
        