import csv
import json
import lzma
import textwrap

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from datasets.arrow_dataset import Dataset
from datasets.features import ClassLabel, Features, Sequence, Value

from .s3_fixtures import *  # noqa: load s3 fixtures


@pytest.fixture(autouse=True)
def set_test_cache_config(tmp_path_factory, monkeypatch):
    # test_hf_cache_home = tmp_path_factory.mktemp("cache")  # TODO: why a cache dir per test function does not work?
    test_hf_cache_home = tmp_path_factory.getbasetemp() / "cache"
    test_hf_datasets_cache = test_hf_cache_home / "datasets"
    test_hf_metrics_cache = test_hf_cache_home / "metrics"
    test_hf_modules_cache = test_hf_cache_home / "modules"
    monkeypatch.setattr("datasets.config.HF_DATASETS_CACHE", str(test_hf_datasets_cache))
    monkeypatch.setattr("datasets.config.HF_METRICS_CACHE", str(test_hf_metrics_cache))
    monkeypatch.setattr("datasets.config.HF_MODULES_CACHE", str(test_hf_modules_cache))
    test_downloaded_datasets_path = test_hf_datasets_cache / "downloads"
    monkeypatch.setattr("datasets.config.DOWNLOADED_DATASETS_PATH", str(test_downloaded_datasets_path))
    test_extracted_datasets_path = test_hf_datasets_cache / "downloads" / "extracted"
    monkeypatch.setattr("datasets.config.EXTRACTED_DATASETS_PATH", str(test_extracted_datasets_path))


FILE_CONTENT = """\
    Text data.
    Second line of data."""


@pytest.fixture(scope="session")
def dataset():
    n = 10
    features = Features(
        {
            "tokens": Sequence(Value("string")),
            "labels": Sequence(ClassLabel(names=["negative", "positive"])),
            "answers": Sequence(
                {
                    "text": Value("string"),
                    "answer_start": Value("int32"),
                }
            ),
            "id": Value("int64"),
        }
    )
    dataset = Dataset.from_dict(
        {
            "tokens": [["foo"] * 5] * n,
            "labels": [[1] * 5] * n,
            "answers": [{"answer_start": [97], "text": ["1976"]}] * 10,
            "id": list(range(n)),
        },
        features=features,
    )
    return dataset


@pytest.fixture(scope="session")
def arrow_file(tmp_path_factory, dataset):
    filename = str(tmp_path_factory.mktemp("data") / "file.arrow")
    dataset.map(cache_file_name=filename)
    return filename


@pytest.fixture(scope="session")
def text_file(tmp_path_factory):
    filename = tmp_path_factory.mktemp("data") / "file.txt"
    data = FILE_CONTENT
    with open(filename, "w") as f:
        f.write(data)
    return filename


@pytest.fixture(scope="session")
def xz_file(tmp_path_factory):
    filename = tmp_path_factory.mktemp("data") / "file.xz"
    data = bytes(FILE_CONTENT, "utf-8")
    with lzma.open(filename, "wb") as f:
        f.write(data)
    return filename


@pytest.fixture(scope="session")
def gz_path(tmp_path_factory, text_path):
    import gzip

    path = str(tmp_path_factory.mktemp("data") / "file.gz")
    data = bytes(FILE_CONTENT, "utf-8")
    with gzip.open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture(scope="session")
def xml_file(tmp_path_factory):
    filename = tmp_path_factory.mktemp("data") / "file.xml"
    data = textwrap.dedent(
        """\
    <?xml version="1.0" encoding="UTF-8" ?>
    <tmx version="1.4">
      <header segtype="sentence" srclang="ca" />
      <body>
        <tu>
          <tuv xml:lang="ca"><seg>Contingut 1</seg></tuv>
          <tuv xml:lang="en"><seg>Content 1</seg></tuv>
        </tu>
        <tu>
          <tuv xml:lang="ca"><seg>Contingut 2</seg></tuv>
          <tuv xml:lang="en"><seg>Content 2</seg></tuv>
        </tu>
        <tu>
          <tuv xml:lang="ca"><seg>Contingut 3</seg></tuv>
          <tuv xml:lang="en"><seg>Content 3</seg></tuv>
        </tu>
        <tu>
          <tuv xml:lang="ca"><seg>Contingut 4</seg></tuv>
          <tuv xml:lang="en"><seg>Content 4</seg></tuv>
        </tu>
        <tu>
          <tuv xml:lang="ca"><seg>Contingut 5</seg></tuv>
          <tuv xml:lang="en"><seg>Content 5</seg></tuv>
        </tu>
      </body>
    </tmx>"""
    )
    with open(filename, "w") as f:
        f.write(data)
    return filename


DATA = [
    {"col_1": "0", "col_2": 0, "col_3": 0.0},
    {"col_1": "1", "col_2": 1, "col_3": 1.0},
    {"col_1": "2", "col_2": 2, "col_3": 2.0},
    {"col_1": "3", "col_2": 3, "col_3": 3.0},
]
DATA_DICT_OF_LISTS = {
    "col_1": ["0", "1", "2", "3"],
    "col_2": [0, 1, 2, 3],
    "col_3": [0.0, 1.0, 2.0, 3.0],
}

DATA_312 = [
    {"col_3": 0.0, "col_1": "0", "col_2": 0},
    {"col_3": 1.0, "col_1": "1", "col_2": 1},
]

DATA_STR = [
    {"col_1": "s0", "col_2": 0, "col_3": 0.0},
    {"col_1": "s1", "col_2": 1, "col_3": 1.0},
    {"col_1": "s2", "col_2": 2, "col_3": 2.0},
    {"col_1": "s3", "col_2": 3, "col_3": 3.0},
]


@pytest.fixture(scope="session")
def dataset_dict():
    return DATA_DICT_OF_LISTS


@pytest.fixture(scope="session")
def arrow_path(tmp_path_factory):
    dataset = Dataset.from_dict(DATA_DICT_OF_LISTS)
    path = str(tmp_path_factory.mktemp("data") / "dataset.arrow")
    dataset.map(cache_file_name=path)
    return path


@pytest.fixture(scope="session")
def csv_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset.csv")
    with open(path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=["col_1", "col_2", "col_3"])
        writer.writeheader()
        for item in DATA:
            writer.writerow(item)
    return path


@pytest.fixture(scope="session")
def parquet_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset.parquet")
    schema = pa.schema(
        {
            "col_1": pa.string(),
            "col_2": pa.int64(),
            "col_3": pa.float64(),
        }
    )
    with open(path, "wb") as f:
        writer = pq.ParquetWriter(f, schema=schema)
        pa_table = pa.Table.from_pydict({k: [DATA[i][k] for i in range(len(DATA))] for k in DATA[0]}, schema=schema)
        writer.write_table(pa_table)
        writer.close()
    return path


@pytest.fixture(scope="session")
def json_list_of_dicts_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset.json")
    data = {"data": DATA}
    with open(path, "w") as f:
        json.dump(data, f)
    return path


@pytest.fixture(scope="session")
def json_dict_of_lists_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset.json")
    data = {"data": DATA_DICT_OF_LISTS}
    with open(path, "w") as f:
        json.dump(data, f)
    return path


@pytest.fixture(scope="session")
def jsonl_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset.jsonl")
    with open(path, "w") as f:
        for item in DATA:
            f.write(json.dumps(item) + "\n")
    return path


@pytest.fixture(scope="session")
def jsonl_312_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset_312.jsonl")
    with open(path, "w") as f:
        for item in DATA_312:
            f.write(json.dumps(item) + "\n")
    return path


@pytest.fixture(scope="session")
def jsonl_str_path(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("data") / "dataset-str.jsonl")
    with open(path, "w") as f:
        for item in DATA_STR:
            f.write(json.dumps(item) + "\n")
    return path


@pytest.fixture(scope="session")
def text_path(tmp_path_factory):
    data = ["0", "1", "2", "3"]
    path = str(tmp_path_factory.mktemp("data") / "dataset.txt")
    with open(path, "w") as f:
        for item in data:
            f.write(item + "\n")
    return path


@pytest.fixture(scope="session")
def text_gz_path(tmp_path_factory, text_path):
    import gzip

    path = str(tmp_path_factory.mktemp("data") / "dataset.txt.gz")
    with open(text_path, "rb") as orig_file:
        with gzip.open(path, "wb") as zipped_file:
            zipped_file.writelines(orig_file)
    return path


@pytest.fixture(scope="session")
def jsonl_gz_path(tmp_path_factory, jsonl_path):
    import gzip

    path = str(tmp_path_factory.mktemp("data") / "dataset.jsonl.gz")
    with open(jsonl_path, "rb") as orig_file:
        with gzip.open(path, "wb") as zipped_file:
            zipped_file.writelines(orig_file)
    return path
