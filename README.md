# Dataset Version Control

Lightweight version control utility for Machine Learning datasets, designed to guarantee traceability and scientific reproducibility in MLOps workflows.

This module works analogously to Git, abstracting versioning through compressed physical snapshots stored in a directory indexed by cryptographic hashes. This allows auditing changes to the data, reverting to previous versions (checkout), and computing semantic differences at the level of logical JSON records.

## Data Versioning Architecture and Flow

The system encapsulates history management by structuring a hidden local store at the path `.dvc_store/`.

```mermaid
flowchart TD
    Dataset[Working Dataset: dataset.json] --> CommitCmd[Command: VCS.commit]
    
    subgraph Snapshot Creation (Content-Addressed Storage)
        CommitCmd --> MD5Calc[Compute MD5 of dataset.json]
        MD5Calc --> ObjectStore{Does hash exist in objects/?}
        ObjectStore -->|Yes - Avoid Duplication| SkipCopy[Deduplicate Content]
        ObjectStore -->|No| CopyFile[Copy to objects/hash.dat]
    end
    
    subgraph Commit Creation in the Graph
        SkipCopy & CopyFile --> Metadata[Generate CommitMetadata]
        Metadata --> SHA1[SHA-1 of Metadata + Parent Hash]
        SHA1 --> UpdateCommits[Register in commits.json]
        UpdateCommits --> UpdateHEAD[Update head.json]
    end
    
    CheckoutCmd[Command: VCS.checkout] --> ReadHEAD[Read head.json & commits.json]
    ReadHEAD --> GetObject[Locate objects/file_hash.dat]
    GetObject --> Restore[Restore dataset.json in the working area]
    
    DiffCmd[Command: VCS.diff] --> ParseJSON[Deserialize JSONs of Commits A and B]
    ParseJSON --> PKDetect[Auto-detect Primary Key: id, guid, instruction]
    PKDetect --> CompareSets[Compute Set and Attribute Differences]
    CompareSets --> ReturnStats[Return Statistics: Added, Removed, Modified]
```

### 1. Content-Addressed Storage (CAS)

To optimize disk usage and support large-volume datasets, the module implements a Content Deduplication strategy:

*   **MD5 Identifier:** When committing a data file, the system computes its MD5 signature:
    $$H_{\text{file}} = \text{MD5}(\text{file\_bytes})$$
*   **Object Store (CAS):** The file is copied to the directory `.dvc_store/objects/[H_file].dat`. If the dataset's content hasn't changed, the resulting hash will be identical, so the system skips the physical copy and registers only a new pointer in the history, reducing storage overhead.
*   **HEAD Pointers:** A pointer is kept in `.dvc_store/head.json` with the active branch and current commit.

### 2. Commit Structure and DAG (Directed Acyclic Graph)

Each commit generates a `CommitMetadata` node that is persisted in `.dvc_store/commits.json`. The unique commit hash is computed via the SHA-1 function:

$$H_{\text{commit}} = \text{SHA-1}(H_{\text{parent}} + H_{\text{file}} + \text{message} + \text{timestamp})$$

By storing the parent commit's hash ($H_{\text{parent}}$), an immutable chronological chain is established that allows the history to be reconstructed as a Directed Acyclic Graph (DAG) and cleanly reverts the working area to any past state.

### 3. Semantic JSON Differ (Data Diffs)

Unlike conventional software tools (such as `git diff` or `diff`) that operate at the plain-text line level (producing false positives due to changes in key ordering, line formatting, or indentation), this module semantically analyzes the data's structure:

1.  **Deserialization:** Converts the JSON files of the compared commits into Python in-memory objects.
2.  **Primary Key Mapping:** If the file is a structured list, it auto-detects a unique identifier column for each record, prioritizing the `id`, `guid`, and `instruction` fields in that order.
3.  **Difference Evaluation:**
    *   *Added:* Records whose primary keys exist in the target commit but not in the source commit.
    *   *Removed:* Records whose primary keys exist in the source commit but not in the target commit.
    *   *Modified:* Records that share a primary key but differ in the value of at least one of their internal fields or attributes.

## Connection to the Ecosystem

This module acts as the Data Control Plane for:
1.  **synthetic-data-generator:** Versions and catalogs the generated data outputs (`synthetic_instruction_dataset.json` and `synthetic_dpo_dataset.json`), allowing the impact of different modifications to the mutated directives to be compared semantically.
2.  **llm-qlora-finetuner:** Ensures reproducibility. Before launching parametric training, the pipeline checks out the dataset to the exact commit hash to be audited, blocking data drift.

## Project Structure

*   `dvc.py`: Implementation of the main `DatasetVCS` class and the `CommitMetadata` Pydantic schema for managing commits, checkouts, and diffs.
*   `test_dvc.py`: Unit test suite that checks initialization, commit creation, physical deduplication, restoration (checkout), and graph integrity.
*   `example.py`: Interactive demonstration of the versioning lifecycle. Modifies records in a JSON dataset simulating insertions and deletions, computes the differences, and restores the initial version.

## Installation and Usage

### 1. Activate the Local Environment and Install Dependencies

Navigate to the working directory and install the requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Version Control Tests

```bash
.venv/bin/python -m unittest test_dvc.py
```

### 3. Run the VCS Demo

```bash
.venv/bin/python example.py
```

The script will initialize the `.dvc_store` repository, commit the initial file, perform controlled edits (modifications and deletions), issue a detailed report with the record differences, and finally revert the file to its original state to illustrate version control.
