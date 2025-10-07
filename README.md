<h1 align="center">
  <b>Machine Learning survey</b><br>
</h1>

<p align="center">
      <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/Python-3.11-ff69b4.svg" /></a>    
</p>


## Purpose

The purpose of this repo is to perform a yearly survey of major machine learning conferences and arXiv.  Extract all the metadata, abstracts, and other information from of all the papers and look for topic frequencies that show up.  

## Disclaimer 

Current product version is 0.3.2.  `__main__.py` in the TUI folder is operational.  Current working search models are `Fuzzy, Cosine, Word2vec, Marco and Specter`.  
The two search parameters that work best are `title and abstract` as those have the least amount of missing values.  (Scraping data isn't always perfect)

## Requirements
- Python >= 3.11

## Main Libraries used
- numpy
- pandas
- rich
- textual
- requests
- matplotlib
- spacy
- scikit-learn
- beautifulsoup4
- pyzotero (eventually)

In `VSCODE` press `CTRL + SHIFT + ~` to open a terminal
Navigate to the directory where you want to clone the repo. 

## Cloning and setting up environment.
Launch VSCode if that is IDE of choice.

Next clone the paper_search repo to your desired location.  If using a blank VM you'll have to install git as shown below. 

```terminal
git clone https://www.github.com/Landcruiser87/paper_search.git
```

After opening the newly cloned folder (CTRL + K + O in Vscode) 
While in root directory run commands below

```terminal
$ mkdir data/logs data/logs/scrape data/logs/tui searches
$ mkdir data/searches data/models data/models/marco data/models/specter
```


### VM setup

If installing this onto a GCP VM, follow the steps below.  

Create your VM with your desired GPU.  For this example we'll use the standard Tesla T4 GPU onto a blank Linux Ubuntu 24.04 instance.  The first step will be to run the following commands to install the necessary dependencies and confirm the GPU is running.

```terminal
#Update your dependencies
sudo apt update && sudo apt upgrade
sudo apt install -y build-essential
sudo apt install -y git

sudo apt install -y python3.12 python3-pip python3-venv
lspci | grep -i nvidia
hostnamectl
gcc --version
```


Next we'll want to add the CUDA drivers to it.  (Get ready this is not fun!)
First we'll go here and check what drivers are available for our GPU
[Nvidia Developer page](https://developer.nvidia.com/cuda-downloads?)

From there we select our system and begin the joy of installing the Cuda drivers. 
The process will look something like this.  We'll use the open source kernel as that is the recommended for the T4 GPU. 

```terminal
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-ubuntu2404.pin
sudo mv cuda-ubuntu2404.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/13.0.1/local_installers/cuda-repo-ubuntu2404-13-0-local_13.0.1-580.82.07-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2404-13-0-local_13.0.1-580.82.07-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2404-13-0-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-13-0
sudo apt-get install -y nvidia-open
```

Now that the Nvidia/Cuda side is installed, you can follow the instructions below surrounding pytorch. We just installed Cuda 13.01 above, so we need to keep the pytorch version BELOW that number.  
If you'd like to monitor your GPU temps to make sure they don't explode.  Use the following. 

```terminal
watch -n 1 nvidia-smi
```

# Project setup with Poetry

## How to check Poetry installation

In your terminal, navigate to your root folder.

If poetry is not installed, do so in order to continue.

On Windows
```terminal
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

On Linux/Mac
```terminal
curl -sSL https://install.python-poetry.org | python3 -
```

If on a gcp image, you will need to add poetry to the path once you are SSH'd into the project folder.  Do so with the following. Change the user name to your gcp email. 

```terminal
export PATH="/home/useremail/.local/bin:$PATH"
```

To check if poetry is installed on your system. Type the following into your terminal

```terminal
poetry -V
```

if you see a `version` returned, you have Poetry installed.  The second command is to update poetry if its installed. (Always a good idea). If not, follow this [link](https://python-poetry.org/docs/) and follow installation commands for your systems requirements. If on windows, we recommend the `powershell` option for easiest installation. Using pip to install poetry will lead to problems down the road and we do not recommend that option.  It needs to be installed separately from your standard python installation to manage your many python installations.  `Note: Python 2.7 is not supported`.  You are more than welcome to go the pip route but I can't guarantee your dependencies won't clash.

## Environment storage

Some prefer Poetry's default storage method of storing environments in one location on your system.  The default storage are nested under the `{cache_dir}/virtualenvs`.  

If you want to store you virtual environment locally.  Set this global configuration flag below once poetry is installed.  This will now search for whatever environments you have in the root folder before trying any global versions of the environment in the cache.

```terminal
poetry config virtualenvs.in-project true
```

For general instruction as to poetry's functionality and commands, please read through poetry's [cli documentation](https://python-poetry.org/docs/cli/)

To create a new venv

```terminal
python -m venv .venv
```

This command will automatically activate the env
```terminal
poetry env use python3.12
```

or 

Activate the venv
Windows
```terminal
.venv/scripts/activate
```

Mac/Linux
```terminal
source .venv\bin\activate
```

### Installation with GPU
To use your GPU, or not to use your GPU.  That is the question.  If you're lucky enough to have workhorse GPU on your rig, you might be inclined to use it when selecting the "Marco" and "Specter" models.  To do so requires... a few extra annoying steps.  Hopefully you bought into the NVIDIA hype and have one of their GPU's as most of pytorch's implmentations are based on the NVIDIA CUDA drivers.  

First order of business is to see what NVIDIA drivers you can currently operate at.  

```terminal
nvidia-smi
```

After running the above look on the top right for `CUDA Version: xx.x`
This will be the maximum CUDA version you can use with your current installation. If you want to install pytorch, you'll need to install a CUDA toolkit that is `BELOW` that max version.  If you go over it... well that's on you.  

Now you'll need to head over to 
[pytorchs getting started page](https://pytorch.org/get-started/locally/)

Go through the selections and see which align with your system.  My only options were 11.8 or 12.6.  Since my NVIDIA max driver version is 12.5.  11.8 it is!  Because poetry is a bit extra, we'll have to add the source for whatever cuda version will fit below your GPU's current NVIDIA drivers.  

```terminal
poetry source add --priority=explicit pytorch-cuda "https://download.pytorch.org/whl/cu118"
or
poetry source add --priority=explicit pytorch-cuda "https://download.pytorch.org/whl/cu129"
```

After the source is added, you should see something like this in your project.toml file.

```
[[tool.poetry.source]]
name = "pytorch-cuda"
url = "https://download.pytorch.org/whl/cu118"
priority = "explicit"
```

Now you can install the specific versions of what you'll need to run SBert models on your GPU. In my case, these were the available versions from the 11.8 CUDA Toolkit.

```terminal
poetry add torch==2.7.0+cu118 torchaudio==2.7.0+cu118 torchvision==0.22.0+cu118 --source pytorch-cuda
poetry add torch==2.8.0+cu129 torchaudio==2.8.0+cu129 torchvision==0.23.0+cu129 --source pytorch-cuda
poetry add sentence-transformers
```

### Installation without GPU but with poetry

You'll want to go into the project.toml file and before you run the command below.  Delete lines `23-25` and `34-44`. Then run the following below.  To update the lock file (first) then install libraries.  Do the following

```terminal
poetry lock
poetry install --no-root
```

This will read from the project.toml file that is included in this repo and install all necessary packgage versions.  Should other versions be needed, the project TOML file will be utilized and packages updated according to your system requirements. To view the current libraries installed

```terminal
poetry show
```

To view only top level library requirements

```terminal
poetry show -T
```

### Installation without GPU on mac with pip
#TODO - Update README to mac installation without IDE. 



## Model setup
If you'd like to use `word2vec` to do your asymetric semantic search, you'll need to do a few things before starting.  `In your terminal, with your environment activated` type the following in your terminal. This should install the model in your activated environment. You can check by looking for something like en_core_web_md-3.8.0.... in your .venv/Lib/site-packages folder.


```terminal
python -m spacy download en_core_web_md
```

## TUI

This repo also comes with a TUI (Terminal User Interface) that allows you to explore the JSON objects for each conference / year.  This repo was forked from [here](https://github.com/oleksis/jtree).  Thank you to [oleksis](https://github.com/oleksis) for creating the initial structure!! :tada:

To run the TUI with poetry

```terminal
poetry run python tui/__main__.py data/scraped/2024_ICML.json 
#replace year/conf
```

With python
```terminal
python tui/__main__.py data/scraped/2024_ICML.json 
#replace year/conf
```

With no file args, like a madman.  This will launch a file picking application that scans the `data/conferences` folder and shows you a list of available files. Enter a number of the conference you want, and you're good to go.

```terminal
poetry run python tui/__main__.py

python tui/__main__.py
```

#### Runtime Notes

- Search with word2vec takes longer to run.  Patience Iago
- Fuzzy search on abstract will take even longer

Suggested operation ranges
- Fuzzy => 1 to 10
  - Best results around 5
- Cosine => -1 to 1
  - Best results around 0.40
- Word2vec => -1 to 1
  - Best results around 0.85
- Marco => -1 to 1
  - Best results around 0.85
- Specter => -1 to 1
  - Best results around 0.85

With the TUI running, it should look something like this. 

https://github.com/user-attachments/assets/b20b32c9-55f0-4e3b-a436-5571a47f9700

#### Todo

[ ] - Add Google Scholar
[ ] - Add Nature
[ ] - Add Pubmed