import os
import json
import hashlib
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class LocalIndexer:
    def __init__(self, index_file='index.json', hash_file='hashes.json'):
        self.index_file = index_file
        self.hash_file = hash_file
        self.inverted_index = defaultdict(dict)  # word -> {file_path: frequency}
        self.file_hashes = {}  # file_path -> hash
        self.lock = threading.Lock()
        
        self.load_index()

    def load_index(self):
        """Load the inverted index and file hashes from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.inverted_index = defaultdict(dict, data)
            except json.JSONDecodeError:
                print("Warning: index file corrupted, starting fresh.")

        if os.path.exists(self.hash_file):
            try:
                with open(self.hash_file, 'r', encoding='utf-8') as f:
                    self.file_hashes = json.load(f)
            except json.JSONDecodeError:
                print("Warning: hash file corrupted, starting fresh.")

    def save_index(self):
        """Save the inverted index and file hashes to disk."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.inverted_index, f, indent=4)
        with open(self.hash_file, 'w', encoding='utf-8') as f:
            json.dump(self.file_hashes, f, indent=4)

    def compute_file_hash(self, file_path):
        """Compute MD5 hash of a file to track changes."""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle potentially large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            return None

    def process_file(self, file_path):
        """Reads a file, checks its hash, extracts words, and returns index data."""
        file_hash = self.compute_file_hash(file_path)
        if not file_hash:
            return None, None
        
        # Check if file has changed since last indexing
        if self.file_hashes.get(file_path) == file_hash:
            return file_path, None  # No change, skip reading content

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple tokenization: extract alphanumeric words
            words = re.findall(r'\b[a-zA-Z0-9_]+\b', content.lower())
            
            word_freq = defaultdict(int)
            for word in words:
                word_freq[word] += 1
                
            return file_path, (file_hash, dict(word_freq))
        except Exception as e:
            return file_path, str(e)

    def update_index_with_result(self, file_path, result):
        """Thread-safe update of the inverted index and file hashes."""
        if result is None:
            return  # No change needed
            
        if isinstance(result, str):
            print(f"Error processing {file_path}: {result}")
            return
            
        file_hash, word_freq = result
        
        with self.lock:
            # Clean up old index entries for this file
            # This handles words that were removed from the file in its latest version
            words_to_delete = []
            for word in self.inverted_index:
                if file_path in self.inverted_index[word]:
                    del self.inverted_index[word][file_path]
                    if not self.inverted_index[word]:
                        words_to_delete.append(word)
                        
            for word in words_to_delete:
                del self.inverted_index[word]

            # Add new entries
            for word, freq in word_freq.items():
                self.inverted_index[word][file_path] = freq
            
            self.file_hashes[file_path] = file_hash

    def build_index(self, directory, extensions=None, max_workers=8):
        """Crawls a directory and processes files concurrently."""
        if extensions is None:
            extensions = ['.txt', '.md', '.html', '.csv', '.json', '.py', '.js']

        files_to_process = []
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    files_to_process.append(os.path.join(root, file))

        print(f"Found {len(files_to_process)} target files.")
        
        indexed_count = 0
        skipped_count = 0
        error_count = 0

        # Concurrently process files
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.process_file, file): file for file in files_to_process}
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    fp, result = future.result()
                    if result and not isinstance(result, str):
                        self.update_index_with_result(fp, result)
                        indexed_count += 1
                        print(f"Indexed: {fp}")
                    elif result and isinstance(result, str):
                        error_count += 1
                        print(f"Failed: {fp} - {result}")
                    elif fp:
                        skipped_count += 1
                        # Uncomment to see skipped files
                        # print(f"Skipped (Unchanged): {fp}")
                except Exception as exc:
                    error_count += 1
                    print(f"File {file_path} generated an exception: {exc}")
                    
        self.save_index()
        print("\n--- Indexing Summary ---")
        print(f"Newly Indexed/Updated: {indexed_count}")
        print(f"Skipped (Unchanged):   {skipped_count}")
        print(f"Errors:                {error_count}")
        print("Index saved successfully.\n")

    def search(self, query):
        """Searches the inverted index for the given query using AND logic."""
        words = re.findall(r'\b[a-zA-Z0-9_]+\b', query.lower())
        if not words:
            return []

        # Find files that contain all words
        matched_files = None
        for word in words:
            files_with_word = set(self.inverted_index.get(word, {}).keys())
            if matched_files is None:
                matched_files = files_with_word
            else:
                matched_files &= files_with_word
                
            if not matched_files:
                break # No files contain all words

        if not matched_files:
            return []

        # Rank files based on cumulative term frequency
        results = []
        for file_path in matched_files:
            score = sum(self.inverted_index[word][file_path] for word in words)
            results.append((file_path, score))

        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

if __name__ == "__main__":
    import sys
    import time
    
    indexer = LocalIndexer()
    
    if len(sys.argv) < 2:
        print("Local Search Engine CLI")
        print("Usage:")
        print("  python indexer.py index <directory_path>")
        print("  python indexer.py search <query_string>")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "index":
        if len(sys.argv) < 3:
            print("Error: Please provide a directory path to index.")
            sys.exit(1)
            
        target_dir = sys.argv[2]
        if not os.path.isdir(target_dir):
            print(f"Error: Directory '{target_dir}' does not exist.")
            sys.exit(1)
            
        print(f"Starting indexing on: {target_dir}")
        start_time = time.time()
        indexer.build_index(target_dir, max_workers=8)
        print(f"Time taken: {time.time() - start_time:.2f} seconds")
            
    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Please provide a search query.")
            sys.exit(1)
            
        query = " ".join(sys.argv[2:])
        print(f"Searching for: '{query}'")
        
        start_time = time.time()
        results = indexer.search(query)
        search_time = time.time() - start_time
        
        if not results:
            print(f"No results found in {search_time:.4f} seconds.")
        else:
            print(f"Found {len(results)} results in {search_time:.4f} seconds:\n")
            for idx, (file_path, score) in enumerate(results, 1):
                print(f"[{idx}] Score: {score} | File: {file_path}")
    else:
        print(f"Unknown command: {command}")
