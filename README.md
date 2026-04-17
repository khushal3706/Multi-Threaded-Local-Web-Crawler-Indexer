# Multi-Threaded Local Web Crawler & Indexer 🕷️⚡

A high-performance, concurrent local search engine built in Python. Instead of relying on slow, linear file searches, this tool builds an **Inverted Index** (just like Google does for the web) to make searching through thousands of local files, documents, and code instantaneous.

## 🚀 Features

- **Lightning Fast Search**: Uses an Inverted Index data structure for `O(1)` search time complexity.
- **Concurrent Processing**: Utilizes `ThreadPoolExecutor` to process and tokenize multiple files simultaneously across available CPU cores.
- **Smart Caching & Versioning**: Computes MD5 hashes for all files. During re-indexing, unchanged files are instantly skipped, vastly improving performance.
- **Relevance Scoring**: Ranks search results dynamically based on term frequency (TF) within the matched documents.
- **Thread-Safe Data Structures**: Implements `threading.Lock()` to safely manage state updates across multiple parallel workers.

## 🛠️ Tech Stack

- **Language**: Python 3.x
- **Concurrency**: `concurrent.futures.ThreadPoolExecutor`, `threading`
- **Data Structures**: `collections.defaultdict` (Inverted Index)
- **Hashing/Optimization**: `hashlib` (MD5 for file state tracking)
- **Persistence**: `json`

## 🧠 How it Works

1. **Crawling**: The script recursively traverses a given directory looking for readable text formats (`.txt`, `.md`, `.html`, `.json`, `.py`, etc.).
2. **Hashing**: Takes a digital fingerprint of each file. If the file was indexed previously and hasn't changed, the worker skips reading it.
3. **Tokenization**: Parses file contents, extracting alphanumeric words using Regex.
4. **Inverted Indexing**: Maps each unique word to a dictionary of files containing that word, along with the frequency of occurrences.
5. **Searching**: When a query is entered, the engine performs a boolean `AND` search across the inverted index, calculating a cumulative score for ranking.

## 💻 Usage

### 1. Clone the repository
```bash
git clone https://github.com/your-username/local-search-engine.git
cd local-search-engine
```

### 2. Build the Index
Point the indexer to a directory on your computer to crawl and map.
```bash
python indexer.py index ./your_target_directory
```
*The tool will generate `index.json` and `hashes.json` in the root folder.*

### 3. Search
Query your indexed data. Results are returned in milliseconds.
```bash
python indexer.py search "your search query"
```

## 📊 Example Output

**Indexing:**
```text
> python indexer.py index test_data
Starting indexing on: test_data
Found 2 target files.
Indexed: test_data\concurrency_notes.txt
Indexed: test_data\tutorial.html

--- Indexing Summary ---
Newly Indexed/Updated: 2
Skipped (Unchanged):   0
Errors:                0
Index saved successfully.

Time taken: 0.01 seconds
```

**Searching:**
```text
> python indexer.py search python threading
Searching for: 'python threading'
Found 2 results in 0.0002 seconds:

[1] Score: 2 | File: test_data\concurrency_notes.txt
[2] Score: 2 | File: test_data\tutorial.html
```

## 🎯 Why This Project?

This project demonstrates a deep understanding of core Computer Science concepts that power modern data-heavy applications:
- Moving beyond basic scripts to design **efficient algorithms and data structures**.
- Handling **I/O bound operations** safely using multithreading and locks.
- Optimizing resource usage with **hashing and caching mechanisms**.
