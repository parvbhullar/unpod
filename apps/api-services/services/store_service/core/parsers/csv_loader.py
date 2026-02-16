from collections import OrderedDict
import csv
from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from services.store_service.core.parsers.base import BaseLoader
import inflection
import re


def infer_data_type(value):
    """Infer the data type of a CSV column value."""
    if value.lower() in ["true", "false"]:
        return "boolean"

    try:
        int(value)
        return "int"
    except ValueError:
        pass

    try:
        float(value)
        return "float"
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            datetime.strptime(value, fmt)
            return "date"
        except ValueError:
            pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            datetime.strptime(value, fmt)
            return "datetime"
        except ValueError:
            pass

    try:
        json.loads(value)
        return "dict"
    except ValueError:
        pass

    try:
        return str(type(value)).split("'")[1]
    except ValueError:
        pass

    return "str"


class CSVLoader(BaseLoader):
    """Loads a CSV file into a list of documents."""

    def __init__(
        self,
        file_path: str,
        source_column: Optional[str] = None,
        csv_args: Optional[Dict] = None,
        encoding: Optional[str] = None,
    ):
        self.file_path = file_path
        self.source_column = source_column
        self.encoding = encoding
        self.csv_args = csv_args or {}

    def load(self) -> List[Any]:
        """Load data into document objects."""
        docs = []
        headers = []
        columns = OrderedDict()

        with open(self.file_path, newline="", encoding=self.encoding) as csvfile:
            csv_reader = csv.DictReader(csvfile, **self.csv_args)
            headers = next(csv_reader)
            for col in headers:
                col = inflection.underscore(self.to_column_name(col))
                columns[col] = "unknown"
            for i, row in enumerate(csv_reader):
                doc = {self.to_column_name(k): v.strip() for k, v in row.items()}
                docs.append(doc)
                for col, value in zip(headers, doc.values()):
                    col = inflection.underscore(self.to_column_name(col))
                    if columns[col] == "unknown" or columns[col] == "string":
                        col_type = infer_data_type(value)
                        columns[col] = col_type

        return {
            "docs": docs,
            "columns": columns,
            "metadata": {
                "source_column": self.source_column or {},
                "encoding": self.encoding,
                "csv_args": self.csv_args,
            },
        }

    def to_column_name(self, name):
        name = name.lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        name = re.sub(r"^[0-9_]+", "", name)
        name = name[:63]
        name = name.rstrip("_")
        if not name:
            name = "column"
        return name
