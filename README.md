<h1 align="center">
  <b>Machine Learning survey</b><br>
</h1>

<p align="center">
      <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/Python-3.11-ff69b4.svg" /></a>    
</p>

## Purpose

The purpose of this repo is to perform a yearly survey of major machine learning conferences, arXiv, bioRxiv, medRxiv, and Semantic Scholar. Extract all the metadata, abstracts, and other information from all the papers and look for topic frequencies that show up.  

## Disclaimer 

Current product version is 0.4.0. This project operates as a fully packaged CLI application. Current working search models are `Fuzzy, Cosine, Word2vec, Marco and Specter`.  
The two search parameters that work best are `title and abstract` as those have the least amount of missing values. (Scraping data isn't always perfect)

## Requirements
- Python >= 3.11
- pip | poetry

## Main Libraries used
- numpy, pandas, scikit-learn, spacy, sentence-transformers, torch
- rich, textual, textual-serve
- requests, beautifulsoup4, curl_cffi

---

## 🚀 Installation

Because this is a packaged application, data, models, and logs are managed for you in your user home directory (`~/.paper_search/`). You no longer need to manually create directories or download base models!

### Poetry Setup
Install Poetry if you want (I recommend the official installer over pip):
```bash
# Linux/Mac/Windows WSL
curl -sSL https://install.python-poetry.org | python3 -

# Power Shell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# If installing a specific version of poetry, add `--version 2.0.0` or whatever version at the end of the above two commands

# If on GCP, add to path (replace useremail with your GCP user)
export PATH="/home/useremail/.local/bin:$PATH"
```

Configure virtual environments to stay inside the project because we don't believe in one virtual environment to rule them all.  🧙🏼‍♂💍🌋

```bash
poetry config virtualenvs.in-project true
```

### Installing via Poetry (For Development)
Clone the repository and install dependencies:
```bash
git clone https://www.github.com/Landcruiser87/paper_search.git
cd paper_search
poetry install
```
### Installing via Pip

```bash
# Clone the repository
git clone https://github.com/Landcruiser87/paper_search.git
cd paper_search

# Create and activate a virtual environment
python -m venv .venv

# Windows (Command Prompt / PowerShell)
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Optional: Install GPU-accelerated PyTorch for your system
python install_torch.py

# Install PaperSearch in editable mode
pip install -e .
```

### Semantic Scholar API
Due to obvious reasons of not wanting to version an API key into git, you will need to manually drop an API key into the `~.paper_search/data/secret` folder in order to use Semantic Scholar quickly.  The instructions for obtaining said key can be found here.  `https://www.semanticscholar.org/product/api#api-key`  If you have a .edu email, they will prioritize getting you a key quickly.  

## 🛠️ Advanced GPU & VM Setup (GCP / Ubuntu)

If you'd like to use GPU-accelerated searches (`Marco` and `Specter`) on a Linux VM (e.g., GCP instance with a Tesla T4), follow these steps to configure CUDA and PyTorch.

### 1. System Dependencies
```terminal
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git python3.12 python3-pip python3-venv
lspci | grep -i nvidia
```
### 2. CUDA Toolkit Installation
Check available drivers on the [Nvidia Developer page](https://developer.nvidia.com/cuda-downloads). Keep your PyTorch version *below* your max installed CUDA version.

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-ubuntu2404.pin
sudo mv cuda-ubuntu2404.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/13.0.1/local_installers/cuda-repo-ubuntu2404-13-0-local_13.0.1-580.82.07-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2404-13-0-local_13.0.1-580.82.07-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2404-13-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-13-0
sudo apt-get install -y nvidia-open
```
*(Monitor your GPU temps with: `watch -n 1 nvidia-smi`)*

### 3. GPU-Enabled PyTorch Installation
Check your max CUDA version (`nvidia-smi`). In this example, we use CUDA 11.8. 

Your `pyproject.toml` is already configured with the PyTorch explicit wheel source. Just install the dependencies:
```bash
poetry install
```
*(If you need a different CUDA version, modify the `[[tool.poetry.source]]` URL in `pyproject.toml` prior to running `poetry install`.)*



---
## 💻 Usage & CLI Commands

Once installed, you can run the application from anywhere on your system using the following commands:

### 1. Launch the TUI
```bash
# Launch interactively (prompts for dataset)
paper-search

# Launch with a specific dataset
paper-search ~/.paper_search/data/conferences/2024_ICML.json

# Skip prompt and open a blank workspace
paper-search --no-prompt
```

### 2. Run the Web Server
Launch the application in your browser (defaults to `http://localhost:8000`). 

```bash
paper-search-serve
```

### 3. Sync & Download New Conferences

To scrape the latest datasets from supported conferences (ICML, ICLR, NEURIPS, etc.) and save them directly to your `~/.paper_search/data/conferences/` folder:
```bash
paper-search-sync 
```

Paper sync comes with a few new cli arguments that allow you to pull down papers in whatever fashion you deem fit. The arguments are below

```
No arguments = Sync existing files to app
--scrape = Run the web scraper on all conferences
--force = Redownload conferences even if they're already cached
--year = Target a specific year
```

For example, if you wanted to scrape all the conferences with fresh data you for 2025

```terminal
paper-search-sync --scrape --force --year 2025
```

---

## 🧠 Model Management (Automatic)

- When you first select **Word2Vec**, the application will automatically download and cache `en_core_web_md` via SpaCy.
- When you first select **Marco** or **Specter**, the application will automatically pull the weights from HuggingFace and cache them locally in `~/.paper_search/models/`. If a compatible GPU is detected, it will utilize it automatically.
---


---

## 📊 Runtime Notes

- Search with **Word2Vec** takes longer to run. *Patience Iago.*
- **Fuzzy** search on abstracts will take even longer.
- **Marco/Specter** without a GPU will be slow on large datasets, but lightning fast with CUDA.

**Suggested Operation Ranges (Thresholds):**
- **Fuzzy** => 1 to 10 (Best results around 5)
- **Cosine** => -1 to 1 (Best results around 0.40)
- **Word2vec** => -1 to 1 (Best results around 0.85)
- **Marco** => -1 to 1 (Best results around 0.85)
- **Specter** => -1 to 1 (Best results around 0.85)

### TUI Preview
With the TUI running, it should look something like this:

https://github.com/user-attachments/assets/b20b32c9-55f0-4e3b-a436-5571a47f9700

*(Note: This repo was originally forked from [oleksis/jtree](https://github.com/oleksis/jtree). Thank you to [oleksis](https://github.com/oleksis) for creating the initial structure! )* 🎉

---

### Future Updates
- [x] Add Semantic Scholar API
- [x] Add Nature? (https://dev.springernature.com/docs/quick-start/api-access/)
  - Included in Semantic
- [ ] Add Papers with Code - API 
- [ ] Add Google Scholar
- [ ] Add Pubmed