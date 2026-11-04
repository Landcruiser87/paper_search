# -*- coding: utf-8 -*-

#main libraries
import os
import json
import time
import shutil
import logging
import zipfile
import datetime
import requests
import numpy as np
from io import BytesIO
from importlib import resources
from bs4 import BeautifulSoup
from rich import print
from rich.tree import Tree
from rich.text import Text
from rich.markup import escape
from rich.filesize import decimal
from rich.console import Console
from rich.logging import RichHandler
from pathlib import Path
from rich.progress import (
    Progress,
    BarColumn,
    SpinnerColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)

################################# Logger functions ####################################
#FUNCTION Logging Futures
def get_file_handler(log_dir:Path)->logging.FileHandler:
    """Assigns the saved file logger format and location to be saved

    Args:
        log_dir (Path): Path to where you want the log saved

    Returns:
        filehandler(handler): This will handle the logger's format and file management
    """	
    log_format = "%(asctime)s|%(levelname)-8s|%(lineno)-4d|%(funcName)-13s|%(message)-108s|" 
                 #f"%(asctime)s - [%(levelname)s] - (%(funcName)s(%(lineno)d)) - %(message)s"
    # current_date = time.strftime("%m_%d_%Y")
    file_handler = logging.FileHandler(log_dir)
    file_handler.setFormatter(logging.Formatter(log_format, "%m-%d-%Y %H:%M:%S"))
    return file_handler

def get_rich_handler(console:Console)-> RichHandler:
    """Assigns the rich format that prints out to your terminal

    Args:
        console (Console): Reference to your terminal

    Returns:
        rh(RichHandler): This will format your terminal output
    """
    rich_format = "|%(funcName)-13s| %(message)s"
    rh = RichHandler(console=console)
    rh.setFormatter(logging.Formatter(rich_format))
    return rh

def get_logger(console:Console, log_dir:Path)->logging.Logger:
    """Loads logger instance.  When given a path and access to the terminal output.  The logger will save a log of all records, as well as print it out to your terminal. Propogate set to False assigns all captured log messages to both handlers.

    Args:
        log_dir (Path): Path you want the logs saved
        console (Console): Reference to your terminal

    Returns:
        logger: Returns custom logger object.  Info level reporting with a file handler and rich handler to properly terminal print
    """	
    #Load logger and set basic level
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    #Load file handler for how to format the log file.
    file_handler = get_file_handler(log_dir)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    #Load rich handler for how to display the log in the console
    # rich_handler = get_rich_handler(console)
    # rich_handler.setLevel(logging.INFO)
    # logger.addHandler(rich_handler)
    logger.propagate = False
    return logger

#FUNCTION timer
################################# Timing Funcs ####################################
def log_time(fn):
    """Decorator timing function.  Accepts any function and returns a logging
    statement with the amount of time it took to run. DJ, I use this code everywhere still.  Thank you bud!

    Args:
        fn (function): Input function you want to time
    """	
    def inner(*args, **kwargs):
        tnow = time.time()
        out = fn(*args, **kwargs)
        te = time.time()
        took = round(te - tnow, 2)
        if took <= 60:
            logger.info(f"{fn.__name__} ran in {took:.3f}s")
        elif took <= 3600:
            logger.info(f"{fn.__name__} ran in {(took)/60:.3f}m")		
        else:
            logger.info(f"{fn.__name__} ran in {(took)/3600:.3f}h")
        return out
    return inner

#FUNCTION get time
def get_time():
    """Function for getting current time

    Returns:
        t_adjusted (str): String of current time
    """
    current_t_s = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    current_t = datetime.datetime.strptime(current_t_s, "%m-%d-%Y-%H-%M-%S")
    return current_t

################################# Size Funcs ############################################

def sizeofobject(folder)->str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(folder) < 1024:
            return f"{folder:4.1f} {unit}"
        folder /= 1024.0
    return f"{folder:.1f} PB"

def getfoldersize(folder:Path):
    fsize = 0
    for root, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(folder,f)
            fsize += os.stat(fp).st_size

    return sizeofobject(fsize)

def getpapercount(file:Path):
    with open(file, "r") as jfile:
        jfile = json.loads(jfile.read())
        numpapers = len(jfile.keys())

    return numpapers

################################# TUI Funcs ############################################

#FUNCTION Launch TUI
def launch_tui() -> Path | None:
    """Scans the conferences directory, prints available datasets,
    and prompts the user to select one or skip.
    """
    directory = CONF_DIR
    directory.mkdir(parents=True, exist_ok=True)

    tree = Tree(
        f":open_file_folder: [bold bright_blue]{directory}[/]",
        guide_style="bold bright_blue",
    )
    paths = walk_directory(directory, tree)
    
    # Filter to actual files
    files = [p for p in paths if p.is_file()]

    # If no files exist, offer the automatic archive download
    if not files:
        console.print(f"[yellow]No conference datasets found in {directory}[/yellow]")
        prompt_dl = console.input(
            "[bold cyan]Download pre-compiled conference bundle (NeurIPS, ICML, ICLR)? [Y/n]: [/bold cyan]"
        ).strip().lower()

        if prompt_dl in ("", "y", "yes"):
            if download_conferences_bundle(directory):
                # Re-scan folder after extraction
                tree = Tree(
                    f":open_file_folder: [bold bright_blue]{directory}[/]",
                    guide_style="bold bright_blue",
                )
                paths = walk_directory(directory, tree)
                files = [p for p in paths if p.is_file()]

        if not files:
            console.print("[dim]Starting with empty workspace (live APIs still functional)...[/dim]\n")
            return None

    # Print the tree of files found
    console.print(tree)
    console.print()

    while True:
        choice = console.input(
            f"[bold green]Select dataset to load [1-{len(files)}] (or press Enter to skip): [/bold green]"
        ).strip()
        
        # User hit Enter without typing a number
        if not choice:
            return None

        if choice.isnumeric():
            idx = int(choice)
            if 1 <= idx <= len(files):
                return files[idx - 1]

        console.print(
            f"[red]Invalid selection. Please enter a number between 1 and {len(files)}, or press Enter to skip.[/red]"
        )

#FUNCTION Walk Directory
def walk_directory(directory: Path, tree: Tree) -> None:
    """Build a Tree with directory contents.
    Source Code: https://github.com/Textualize/rich/blob/master/examples/tree.py

    """
    # Sort dirs first then by filename
    paths = sorted(
        Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    idx = 1
    # paper_count = 0
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        # Just list the CAM folders
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            file_size = getfoldersize(path)
            branch = tree.add(
                f"[bold green]{idx} [/bold green][bold magenta]:open_file_folder: [link file://{path}]{escape(path.name)}[/bold magenta] [bold blue]{file_size}[/bold blue]",
                style=style,
                guide_style=style,
            )
            
            # walk_directory(path, branch)
        else:
            # paper_count += getpapercount(path)
            text_filename = Text(path.name, "green")
            text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            # if path.name.split(".")[0].split("_")[1] in MAIN_CONFERENCES:
            #     icon = "🔥 "
            # elif path.name.split(".")[0].split("_")[1] in SUB_CONFERENCES:
            #     icon = "🐍 "
            # elif path.suffix == ".mib":
            #     icon = "👽 "
            # else:
            #     icon = "🔫 "
            # tree.add(Text(f'{idx} ', "blue") + Text(icon) + text_filename)
            tree.add(Text(f'{idx} ', "blue") + text_filename)
        idx += 1

    return paths

def list_datasets() -> list[tuple]:
    """Main function is list available datasources

    Args:
        paths list[Path]: List of pathlib Path's

    Returns:
        results list[tuple]: Returns a list of file names with their index as tuples
    """
    results = []
    filenum = 0
    s_paths = [Path(f"{DATA_DIR}/conferences/"), Path(f"{DATA_DIR}/searches/")]
    for directory in s_paths:
        paths = sorted(
            directory.iterdir(),
            key=lambda path: (path.is_file(), path.name.lower()),
        )
        for val in paths:
            results.append((val.stem, filenum))
            filenum += 1

    return results

########################## Saving funcs ##########################################

class NumpyArrayEncoder(json.JSONEncoder):
    """Custom numpy JSON Encoder.  Takes in any type from an array and formats it to something that can be JSON serialized. Source Code found here. https://pynative.com/python-serialize-numpy-ndarray-into-json/
    
    Args:
        json (object): Json serialized format
    """	
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return obj.__dict__
        elif isinstance(obj, str):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return datetime.datetime.strftime(obj, "%m-%d-%Y-%H-%M-%S")
        else:
            return super(NumpyArrayEncoder, self).default(obj)
    
# FUNCTION Save JSON
def save_data(search_name:str, data:dict):
    result_json = json.dumps(data, indent=2, cls=NumpyArrayEncoder)
    with open(f"{DATA_DIR}/searches/{search_name}.json", "w") as outf:
        outf.write(result_json)

# FUNCTION Save Conference
def save_conference(results: dict, conf: str, year: int):
    dest = CONF_DIR / f"{year}_{conf}.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

# FUNCTION Load JSON
def load_json(fp:str)->json:
    """Loads the saved JSON arXiv categories

    Args:
        fp (str): File path for ze loading

    Returns:
        jsondata (JSON): dictionary version of saved JSON
    """    
    if os.path.exists(fp):
        with open(fp, "r") as f:
            jsondata = json.loads(f.read())
            return jsondata	

########################## Web functions ##########################################
def download_conferences_bundle(target_dir: Path | None = None) -> bool:
    """Streams and unpacks the pre-compiled conference datasets into ~/.paper_search."""
    dest_dir = target_dir or CONFERENCES_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold cyan]Connecting to GitHub to download conference datasets...[/bold cyan]")

    try:
        response = requests.get(BUNDLE_URL, stream=True, timeout=15)
        if response.status_code == 404:
            console.print("[red]Download failed: conferences_bundle.zip not found on GitHub Releases.[/red]")
            console.print("[dim]Make sure conferences_bundle.zip is attached to your latest GitHub release.[/dim]")
            return False
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        buffer = BytesIO()

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        with progress:
            task = progress.add_task("Downloading bundle...", total=total_size)
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    buffer.write(chunk)
                    progress.update(task, advance=len(chunk))

        console.print("[dim]Extracting archive into ~/.paper_search/data/conferences/...[/dim]")
        with zipfile.ZipFile(buffer) as zip_file:
            zip_file.extractall(dest_dir)

        console.print("[bold green]Success: Conference datasets downloaded and ready![/bold green]\n")
        return True

    except Exception as error:
        console.print(f"[red]Error downloading conference archive: {error}[/red]\n")
        return False
    
def get_categories(result:BeautifulSoup) -> dict:
    """[Ingest XML of summary page for articles info]

    Args:
        result (BeautifulSoup object): html of apartments page

    Returns:
        categories (dict): [Dictionary of the arXiv categories]
    """
    #Base data container
    categories = {}

    #Iterate over taxonomy children
    for child in result.contents:
        #If its an H2 tag, its a category
        if child.name == "h2":
            key = child.text
            categories[key] = {}
            continue
        #If its blank, skip it
        elif child == '\n':
            continue
        #If its the body, extract the sub categories we want        
        elif child.attrs.get("class")[0] == "accordion-body":
            containers = child.find_all("div", class_="columns divided")
            for subchild in containers:
                code_search = subchild.find("h4")
                code = code_search.text.split()[0].strip()
                abb_search = subchild.find("span")
                abb = abb_search.text.strip("()")
                desc_search = subchild.find("p")
                desc = desc_search.text.strip()
                categories[key][code] = (abb, desc)

    return categories

def rebuild_taxonomy() -> dict:
    url = "https://www.arxiv.org/category_taxonomy"
    referrer = "https://info.arxiv.org/"
    chrome_version = np.random.randint(120, 137)
    headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': f'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36',
        'sec-ch-ua': f'"Not)A;Brand";v="99", "Google Chrome";v={chrome_version}, "Chromium";v={chrome_version}',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'referer': referrer,
        'Content-Type': 'text/html,application/xhtml+xml,application/xml'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Parse the XML
    bs4ob = BeautifulSoup(response.text, features="lxml")

    #Find all the categories
    results = bs4ob.find("div", {"id":"category_taxonomy_list"})
    if results:
        categories = get_categories(results)
        logger.debug(f'categories successfully returned from {url}')
        return categories
            
    else:
        logger.warning(f"An error occured and categories could not be extracted. Check DOM for updated field names")

def load_taxonomy(search:bool=False):
    try:
        if search:
            categories = rebuild_taxonomy()
            cat_json = json.dumps(categories, indent=2, cls=NumpyArrayEncoder)
            with open(f"{DATA_DIR}/arxiv_cat.json", "w") as outf:
                outf.write(cat_json)

        else:
            path = f"{DATA_DIR}/arxiv_cat.json"
            if os.path.exists(path):
                categories = load_json(path)
            else:
                logger.warning(f"An error occured loading the arx-cat.json file")

        return categories 
    
    except Exception as e:
        logger.warning("Arxiv Categories were not loaded properly")
        logger.warning(f"Error: {e}")
        logger.warning("To rebuild Taxonomy, set initial search variable to True")
################################# Rich Spinner Control ####################################

#FUNCTION Progress bar
def mainspinner(console:Console, totalstops:int):
    """Load a rich Progress bar for alerting you to the progress of the search

    Args:
        console (Console): reference to the terminal
        totalstops (int): Amount of years * num of conferences to be searched

    Returns:
        my_progress_bar (Progress): Progress bar for tracking overall progress
        jobtask (int): mainjob id for ecg extraction
    """

    my_progress_bar = Progress(
        TextColumn("{task.description}"),
        SpinnerColumn("aesthetic"),
        BarColumn(),
        TextColumn("*"),
        "time elapsed:",
        TextColumn("*"),
        TimeElapsedColumn(),
        TextColumn("*"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
        console=console,
        refresh_per_second=6,
        redirect_stdout=False
    )
    jobtask = my_progress_bar.add_task("[green] searching papers", total=totalstops + 1)
    return my_progress_bar, jobtask

def add_spin_subt(prog:Progress, msg:str, howmanysleeps:int):
    """Adds a secondary job to the main progress bar

    Args:
        prog (Progress): Main progress bar
        msg (str): Message to update secondary progress bar
        howmanysleeps (int): How long to let the timer sleep
    """
    #Add secondary task to progbar
    liljob = prog.add_task(f"[magenta]{msg}", total = howmanysleeps)
    #Run job for random sleeps
    for _ in range(howmanysleeps):
        time.sleep(1)
        prog.update(liljob, advance=1)
    #Hide secondary progress bar
    prog.update(liljob, visible=False)

########################## Global Variables for import ##########################################
def init_workspace():
    # Ensure folders exist on startup
    for path in [DATA_DIR, LOG_DIR, MODEL_DIR, SCREEN_DIR, SECRET_DIR, CONF_DIR, DATA_DIR / "searches", LOG_DIR / "tui"]:
        path.mkdir(parents=True, exist_ok=True)
    
    if not any(CONF_DIR.iterdir()):
        try:
            # Locate seed data inside installed package
            seed_path = resources.files("paper_search") / "seed_data"
            
            # Copy bundled conference seed files
            seed_conf = seed_path / "conferences"
            if seed_conf.is_dir():
                for file_path in seed_conf.iterdir():
                    if file_path.is_file():
                        shutil.copy2(file_path, CONF_DIR / file_path.name)

            # Copy baseline taxonomy if available
            taxonomy = seed_path / "arxiv_cat.json"
            if taxonomy.is_file():
                shutil.copy2(taxonomy, CONF_DIR / "arxiv_cat.json")

        except Exception as e:
            # Non-fatal: user can still fetch new datasets
            pass          

USER_DIR = Path.home() / ".paper_search"
DATA_DIR = USER_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
CONF_DIR = DATA_DIR / "conferences"
MODEL_DIR = DATA_DIR / "models"
SCREEN_DIR = DATA_DIR / "screenshots"
SECRET_DIR = DATA_DIR / "secrets"

#logger/console stuffs
date_json = get_time().strftime("%m-%d-%Y_%H-%M-%S")
console = Console(color_system="auto", stderr=True)
logger = get_logger(console, log_dir = f"{DATA_DIR}/logs/{date_json}.log")
chrome_version = np.random.randint(125, 152)

# Confernces
MAIN_CONFERENCES  = ["ICML", "ICLR", "NEURIPS"]
SUB_CONFERENCES   =  ["COLT", "AISTATS", "AAAI", "CHIL", "ML4H", "ICCV"] 
SEARCH_FIELDS = ["title", "keywords", "topic", "abstract"]  
# Conf data
BUNDLE_URL = "https://github.com/Landcruiser87/paper_search/releases/latest/download/conferences_bundle.zip"

#Metrics for asymetric similarity search
SEARCH_MODELS = ["Fuzzy", "Cosine", "Word2Vec", "Marco", "Specter"]
MODEL_DESC = [
    "Fuzzy matching like regex.  Warning: Very slow when run against the abstract field", 
    "Very fast and good for basic retrieval.  Uses TF-IDF with L1 regularization", 
    "Using the standard spacy pipeline, calculates a cosine sim with more detailed embeddings", 
    "Good for Asymetric Semantic Search.  Slower than above, but more accurate. Available for GPU",
    "Meant for comparing scientific papers.   Runs quite slowly on abstracts. Available for GPU"
]
#arXiv Params
ARXIV_FIELDS = ["Title", "Abstract", "Author(s)",  "Comments", "DOI", "arXiv id", "ORCID"]
ARXIV_SUBJECTS = ["Computer Science", "Economics", "Electrical Engineering and Systems Science", "Mathematics", "Physics", "Quantitative Biology", "Quantitative Finance", "Statistics"]
ARXIV_DATES = ["All Dates", "Past 12 Months", "Specific Year", "Date Range"]
ARXIV_AREAS = load_taxonomy()

XARXIV_FIELDS = ["Title", "Abstract", "Author(s)", "Abstract|Title", "Text|Abstract|Title"]  
XARXIV_SOURCES = ["bioRxiv", "medRxiv"]
XARXIV_SORT = ["Best match", "Oldest first", "Newest first", "Popularity"]
BIOARXIV_SUBJECTS =[
    "Animal Behavior and Cognition", "Biochemistry", "Bioengineering",
    "Bioinformatics", "Biophysics", "Cancer Biology", "Cell Biology",
    "Clinical Trials", "Developmental Biology", "Ecology", "Epidemiology",
    "Evolutionary Biology", "Genetics", "Genomics", "Immunology", "Microbiology", 
    "Molecular Biology", "Neuroscience", "Paleontology", "Pathology", 
    "Pharmacology and Toxicology", "Physiology", "Plant Biology", 
    "Scientific Communication and Education", "Synthetic Biology", "Systems Biology", "Zoology"
]

MEDARXIV_SUBJECTS= [
    "Addiction Medicine", "Allergy and Immunology", "Anesthesia",
    "Cardiovascular Medicine", "Dentistry and Oral Medicine", "Dermatology",
    "Emergency Medicine", "Endocrinology (including Diabetes Mellitus and Metabolic Disease)", 
    "Epidemiology", "Forensic Medicine", "Gastroenterology", "Genetic and Genomic Medicine", "Geriatric Medicine",
    "Health Economics", "Health Informatics", "Health Policy", 
    "Health Systems and Quality Improvement", "Hematology", "HIV/AIDS", 
    "Infectious Diseases (except HIV/AIDS)", "Intensive Care and Critical Care Medicine", "Medical Education",
    "Medical Ethics", "Nephrology", "Neurology", "Nursing",
    "Nutrition", "Obstetrics and Gynecology", "Occupational and Environmental Health",
    "Oncology", "Ophthalmology", "Orthopedics", "Otolaryngology",
    "Pain Medicine", "Palliative Medicine", "Pathology", "Pediatrics",
    "Pharmacology and Therapeutics", "Primary Care Research", "Psychiatry and Clinical Psychology", 
    "Public and Global Health", "Radiology and Imaging",
    "Rehabilitation Medicine and Physical Therapy", "Respiratory Medicine",
    "Rheumatology", "Sexual and Reproductive Health", "Sports Medicine",
    "Surgery", "Toxicology", "Transplantation", "Urology"
]

SEMANTIC_SUBJECTS = ["Computer Science", "Medicine", "Chemistry", "Biology", "Materials Science",
"Physics", "Geology", "Psychology", "Art", "History", "Geography",
"Sociology", "Business", "Political Science", "Economics", "Philosophy",
"Mathematics", "Engineering", "Environmental Science", "Agricultural and Food Sciences", 
"Education", "Law", "Linguistics"]

SEMANTIC_PUBS = ["Review", "JournalArticle", "CaseReport", "ClinicalTrial", "Conference",
"Dataset", "Editorial", "LettersAndComments", "MetaAnalysis", "News", "Study",
"Book", "BookSection"]
