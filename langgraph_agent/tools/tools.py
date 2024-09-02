from collections import defaultdict
from statistics import mode, StatisticsError

import pandas
import pandas as pd
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolExecutor, ToolNode
import matplotlib.pyplot as plt

class ToolEditor:
    def __init__(self) -> None:
        self.tools = self.get_tools()
        self.tool_executor = ToolExecutor(self.tools)
        self.tool_node = ToolNode(self.tools)

    def get_tools(self) -> list:
        return [summarize_dataset, calculate_missing_values, handle_missing_values,
                replace_with_mean, replace_with_mode, replace_with_median]


df = pd.read_csv(r"C:\Users\emirs\Documents\Projects\python\LanggraphGPT_DataProcessor\dataset\death_causes.csv")
global dataset


def set_dataset(path):
    global dataset
    dataset = pd.read_csv(path)


@tool
def summarize_dataset() -> dict:
    """
        Summarizes a pandas DataFrame by calculating the data type, minimum, maximum, mean, median,
        and mode for each column in the dataset.

        Returns:
        --------
        dict
            A dictionary where each key is a column name from the DataFrame and each value
            is another dictionary containing the following keys:
            - 'type': The data type of the column.
            - 'min': The minimum value in the column.
            - 'max': The maximum value in the column.
            - 'mean': The mean value of the column (if numeric).
            - 'median': The median value of the column (if numeric).
            - 'mode': The mode of the column (if applicable; None if multimodal).

        Notes:
        ------
        - The 'mean' and 'median' are calculated only for columns with numeric data types ('int64', 'float64').
        - The 'mode' is calculated by dropping NaN values from the column. If the column is multimodal
          or contains no valid values, the 'mode' will be set to None.
        - This function is designed to handle columns with mixed data types, and it ensures that
          the appropriate statistical measures are calculated based on the column's data type.
        """
    summary = defaultdict(dict)

    for column in dataset.columns:
        col_data = dataset[column]
        summary[column]['type'] = str(col_data.dtype)
        summary[column]['min'] = float(col_data.min()) if col_data.dtype in ['int64', 'float64'] else col_data.min()
        summary[column]['max'] = float(col_data.max()) if col_data.dtype in ['int64', 'float64'] else col_data.max()
        summary[column]['mean'] = float(col_data.mean()) if col_data.dtype in ['int64', 'float64'] else None
        summary[column]['median'] = float(col_data.median()) if col_data.dtype in ['int64', 'float64'] else None

        try:
            summary[column]['mode'] = mode(col_data.dropna())
        except StatisticsError:
            summary[column]['mode'] = None

    return dict(summary)


@tool
def calculate_missing_values() -> dict:
    """
    Calculate the missing value ratios and counts for each column in a DataFrame.

    Returns:
    - dict: A dictionary where the keys are column names and the values are dictionaries containing the
      count and ratio of missing values for each column.
    """
    missing_values_info = {}

    total_rows = len(dataset)

    for column in dataset.columns:
        missing_count = dataset[column].isna().sum()
        missing_ratio = missing_count / total_rows

        missing_values_info[column] = {
            'missing_count': int(missing_count),
            'missing_ratio': missing_ratio
        }

    return missing_values_info


@tool
def handle_missing_values(column_name: str) -> str:
    """
    Replace missing values in the specified column with the column's mean value.
    This function calculates the mean of the specified column, replaces any missing
    values (NaNs) with this mean, and returns a summary string indicating the mean
    value and the number of missing values that were replaced.
    Parameters:
    ----------
    column_name : str
        The name of the column in which missing values will be replaced with the mean value.
    Returns:
    -------
    str
        A string summarizing the operation, including the mean value used for replacement
        and the number of missing values that were filled.
    """
    mean_value = df[column_name].mean()
    missing_count = df[column_name].isna().sum()
    df[column_name] = df[column_name].fillna(mean_value)
    return (f"The mean value for '{column_name}' is {mean_value:.2f}. "
            f"Replaced {missing_count} missing values with this mean.")


@tool
def replace_with_mean(column_name: str) -> str:
    """
    Replace missing values in the specified column with the mean of the column.

    Parameters:
    - df: pd.DataFrame: The DataFrame containing the column.
    - column_name: str: The name of the column to process.

    Returns:
    - str: A message describing the operation performed, including the mean value used and the number of missing values filled.
    """
    if pd.api.types.is_numeric_dtype(dataset[column_name]):
        mean_value = dataset[column_name].mean()
        missing_count = dataset[column_name].isna().sum()
        dataset[column_name].fillna(mean_value, inplace=True)
        return f"Filled {missing_count} missing values in '{column_name}' with mean value {mean_value}."
    else:
        raise ValueError(f"Column '{column_name}' is not numeric.")


@tool
def replace_with_median(column_name: str) -> str:
    """
    Replace missing values in the specified column with the median of the column.

    Parameters:
    - df: pd.DataFrame: The DataFrame containing the column.
    - column_name: str: The name of the column to process.

    Returns:
    - str: A message describing the operation performed, including the median value used and the number of missing values filled.
    """
    if pd.api.types.is_numeric_dtype(dataset[column_name]):
        median_value = dataset[column_name].median()
        missing_count = dataset[column_name].isna().sum()
        dataset[column_name].fillna(median_value, inplace=True)
        return f"Filled {missing_count} missing values in '{column_name}' with median value {median_value}."
    else:
        raise ValueError(f"Column '{column_name}' is not numeric.")


@tool
def replace_with_mode(column_name: str) -> str:
    """
    Replace missing values in the specified column with the mode of the column.

    Parameters:
    - df: pd.DataFrame: The DataFrame containing the column.
    - column_name: str: The name of the column to process.

    Returns:
    - str: A message describing the operation performed, including the mode value used and the number of missing values filled.
    """
    mode_value = dataset[column_name].mode()[0]
    missing_count = dataset[column_name].isna().sum()
    dataset[column_name].fillna(mode_value, inplace=True)
    return f"Filled {missing_count} missing values in '{column_name}' with mode value '{mode_value}'."


def calculate_total_missing_values() -> int:
    total_missing = dataset.isna().sum().sum()
    return total_missing


def generate_tool_calls_for_missing_values() -> list:
    tool_calls = []

    for column in dataset.columns:
        if dataset[column].isna().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(dataset[column]):
            tool_calls.append(f"Tool: replace_with_mean(), Args: column: '{column}'\n")
        elif pd.api.types.is_string_dtype(dataset[column]):
            tool_calls.append(f"Tool: replace_with_mode(), Args: column: '{column}'\n")
        elif pd.api.types.is_datetime64_any_dtype(dataset[column]):
            tool_calls.append(f"Tool: replace_with_median(), Args: column: '{column}'\n")

    return tool_calls
