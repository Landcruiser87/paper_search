import re
import json
import requests
import argparse
import datetime
import numpy as np
from itertools import cycle
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from .support import (
    console, logger, log_time, 
    save_conference, mainspinner, add_spin_subt,
    download_conferences_bundle, CONF_DIR
    )

MAIN_CONFERENCES  = ["ICML", "ICLR", "NEURIPS"]
SUB_CONFERENCES   =  ["COLT", "AISTATS", "AAAI", "CHIL", "ML4H", "ECCV"] #"CLDD"-Got an xml error for 2024
FUN_STATUS_UPDATE = cycle(["Patience Iago", "Phenominal COSMIC POWER", "Iiiiiity bitty living space", "Books, i've read these books", "Your conclusions were all wrong Ryan", "Let it go Indiana", "Duuuude", "wheres my car", "I wanna talk to sampson!!"])

#FUNCTION Request Conference
def request_conf(conference:str, year:int=None, version:str=""):
    """Function to request a single years conference papers

    Args:
        conference (str): Conference of interest
        year (int): Year of interest

    Returns:
        results (dict): Dictionary of papers from each conference
    """    
    chrome_version = np.random.randint(120, 152)
    conf_dict={
        "NEURIPS":{
            "name":"Conference and Workshop on Neural Information Processing Systems",
            "abbrv":"NEURIPS",
            "url":f"https://neurips.cc/static/virtual/data/neurips-{year}-orals-posters.json",
            "headers":{
                "authority":f"https://neurips.cc/static/virtual/data/neurips-{year}-orals-posters.json",
                "method":"GET",
                "path":f"/static/virtual/data/neurips-{year}-orals-posters.json",
                "scheme":"https",
                "accept":"*/*",
                "accept-encoding":"gzip,deflate,br,zstd",
                "accept-language":"en-US,en;q=0.9",
                "referer":f"https://neurips.cc/virtual/{year}/papers.html?layout=detail",
                "sec-ch-ua":f'"Chromium";v="{chrome_version}", "Not(A:Brand";v="24", "Google Chrome";v="{chrome_version}"',
                "sec-ch-ua-Mobile":"?0",
                "sec-ch-ua-platform":"Windows",
                "sec-fetch-dest":"empty",
                "sec-fetch-mode":"cors",
                "sec-fetch-site":"same-origin",
                "user-agent": f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
                "x-requested-with":"XMLHttpRequest"
            }
        },
        "ICML":{
            "name":"International Conference of Machine Learning",
            "abbrv":"ICML",
            "url":f"https://icml.cc/static/virtual/data/icml-{year}-orals-posters.json",
            "headers":{
                "authority":f"https://icml.cc/static/virtual/data/icml-{year}-orals-posters.json",
                "method":"GET",
                "path":f"/static/virtual/data/icml-{year}-orals-posters.json",
                "scheme":"https",
                "accept":"*/*",
                "accept-encoding":"gzip,deflate,br,zstd",
                "accept-language":"en-US,en;q=0.9",
                "referer":f"https://icml.cc/virtual/{year}/papers.html?layout=detail",
                "sec-ch-ua":f'"Chromium";v="{chrome_version}", "Not(A:Brand";v="24", "Google Chrome";v="{chrome_version}"',
                "sec-ch-ua-Mobile":"?0",
                "sec-ch-ua-platform":"Windows",
                "sec-fetch-dest":"empty",
                "sec-fetch-mode":"cors",
                "sec-fetch-site":"same-origin",
                "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
                "x-requested-with":"XMLHttpRequest"
            }
        },
        "ICLR":{
            "name":"International Conference of Learning Representations",
            "abbrv":"ICLR",
            "url":f"https://iclr.cc/static/virtual/data/iclr-{year}-orals-posters.json",
            "headers":{
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Referer": f"https://iclr.cc/virtual/{year}/papers.html?layout=detail",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "sec-ch-ua": f"'Chromium';v='{chrome_version}', 'Not:A-Brand';v='24', 'Google Chrome';v='{chrome_version}'",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "'Windows'",
            }
        },
        "PMLR":{
            "name":"Proceedings in Machine Learning Research",
            "abbrv":"PMLR",
            "url":f"https://proceedings.mlr.press//assets/rss/feed.xml",
            "headers" : {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "if-modified-since": "Tue, 18 Feb 2025 09:52:46 GMT",
                "if-none-match": "W/'67b4586e-111f4'",
                "priority": "u=0, i",
                "referer": "https://proceedings.mlr.press/",
                "sec-ch-ua": f"'Chromium';v={chrome_version}, 'Not:A-Brand';v='24', 'Google Chrome';v={chrome_version}",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "'Windows'",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
            }
        },
        "IND_CONF":{
            "name":"Individual conference request",
            "abbrv":"PMLR",
            "url":f"https://proceedings.mlr.press//{version}//assets/rss/feed.xml",
            "headers" : {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "max-age=0",
                "if-modified-since": "Tue, 18 Feb 2025 09:52:46 GMT",
                "if-none-match": "W/'67b4586e-111f4'",
                "priority": "u=0, i",
                "referer": "https://proceedings.mlr.press/",
                "sec-ch-ua": f"'Chromium';v={chrome_version}, 'Not:A-Brand';v='24', 'Google Chrome';v={chrome_version}",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "'Windows'",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
            }
        },        
        "ML4H":{
            "name":"Machine Learning for Health",
            "abbrv":"ML4H",
            "url":"stuff",
            "headers":"morestuff"
        }
    }
    if version:
        url = conf_dict["IND_CONF"]["url"]
        headers = conf_dict["IND_CONF"]["headers"]

    else:
        url = conf_dict[conference]["url"]
        headers = conf_dict[conference]["headers"]
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            # If there's an error, log it and return no data for that conference
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Reason: {resp.reason}")
            return None
        else:
            logger.debug(f"request successful for {url}, parsing data")
            #If its the overall scrape of PLMR
            if conference == "PMLR":
                results = parse_all(resp.content, year_limit=year)
            #If its a main conference
            elif conference in MAIN_CONFERENCES:
                resp_json = resp.json()
                results = extract_json(resp_json, url)
                results = get_abstracts(results, headers, url)
            #If its a sub conference
            else:
                results = parse_conf(resp.content)
        return results
    
    except Exception as e:
        logger.warning(f"Error extracting {url} {e}")
        return None

def request_paper(paper:dict, version:str) -> dict | None:
    chrome_version = np.random.randint(120, 132)
    paper_dict = {
        "name":"Individual paper request",
        "abbrv":"PMLR",
        "url":paper["url"],
        "headers" : {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "referer": f"https://proceedings.mlr.press/{version}/",
            "sec-ch-ua": f"'Chromium';v={chrome_version}, 'Not:A-Brand';v='24', 'Google Chrome';v={chrome_version}",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "'Windows'",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        }
    }

    url = paper_dict["url"]
    headers = paper_dict["headers"]
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        # If there's an error, log it and return no data for that conference
        logger.warning(f"Status code: {resp.status_code}")
        logger.warning(f"Reason: {resp.reason}")

    else:
        logger.debug(f"request successful for {url}, parsing data")
        extras = parse_paper(resp.text)
        paper.update(**extras)

    return paper

############################### Data Extraction Functions ##################
#FUNCTION Filter result
def extract_json(json_data:json, url:str)->dict:
    ids = list(range(json_data["count"]))
    base_keys = ["id","name","author","abstract","keywords","topic","session","event_type","virtualsite_url","url","paper_url", "paper_pdf_url", "sourceurl"]
    base_dict = {str(val) + "_" + json_data["results"][val]["name"]:{key:"" for key in base_keys} for val in ids}
    for id, idx in zip(base_dict.keys(), ids):
        authors = [str(x) + "_" + json_data['results'][idx]['authors'][x]["fullname"] for x in range(len(json_data['results'][idx]['authors']))]
        base_dict[id]["author"] = {author:{} for author in authors} 
        #Grab author info
        for num, author in enumerate(authors):
            auth_info = json_data["results"][idx]["authors"][num]
            base_dict[id]["author"][author].update(**auth_info)
        
        #Grab other keys we want from the paper
        for key in base_keys:
            temp = json_data["results"][idx].get(key)
            if key == "virtualsite_url" and temp:
                base_dict[id][key] = "https://"+ url.split("/")[2] + temp
            elif temp:
                base_dict[id][key] = temp

    return base_dict

def get_abstracts(json_data:json, headers:dict, url:str) -> dict:
    """They split the abstracts into another JSON call in 2026 with the major conferences.
    This will make an additional request to grab those abstracts and align them by ID. 

    Args:
        json_data (json): returned abstracts 
        headers (dict): headeres used in previous request
        url (str): url to be modified for abstracts

    Returns:
        results (dict): Dictionary of updated results with abstracts
    """
    try:
        url = url.replace("orals-posters", "abstracts")
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            # If there's an error, log it and return no data for that conference
            logger.warning(f"Status code: {resp.status_code}")
            logger.warning(f"Reason: {resp.reason}")
            return json_data

    except Exception as e:
        logger.warning(f"Error extracting {url} {e}")
        return json_data

    logger.debug(f"request successful for {url}, parsing data")
    abstracts = resp.json()
    abstract_ids = [str(y) for y in abstracts.keys()]
    for j_name in json_data.keys():
        j_id = str(json_data[j_name].get("id", None))
        if j_id in abstract_ids:
            json_data[j_name]["abstract"] = abstracts.get(j_id)

    return json_data
    
    #Make abstracts request
    #Find the id 
    #iterate id's of abstracts,  lineup with 

def parse_all(xml:str, year_limit:int=2010) -> dict:
    """parses xml from initial RSS feed of possible conferences

    Args:
        xml (str): Biiiiig old text dump
        year_limit (int, optional): _description_. Defaults to 2016.

    Returns:
        dict: Returns dictionary of PMLR data. Order + Paper title == key
    """
    results = {}
    root = ET.fromstring(xml)
    for paper in root.findall("channel/item"):
        description = paper.find("description").text
        for conf in SUB_CONFERENCES:
            if conf in description:
                #regex for any year (four consecutive numbers) between 1900 and 2100
                pattern = r"\b(19[0-9]{2}|20[0-9]{2}|2100)\b"
                match = re.findall(pattern, description)
                if match:
                    if int(match[0]) >= year_limit:
                        year = match[0]
                    else:
                        continue
                else:
                    continue
                results[year + "_" + conf]= paper.find("link").text
    return results

def parse_conf(xml:str):
    results = {}
    root = ET.fromstring(xml)
    for idx, paper in enumerate(root.findall("channel/item")):
        key = paper.find("title").text
        key = "".join(str(x) for x in key if x.isalnum() | x.isspace())
        key = str(idx) + "_" + key.strip()
        url = paper.find("link").text
        results[key] = {}
        results[key]["title"] = paper.find("title").text
        results[key]["abstract"] = paper.find("description").text
        results[key]["url"] = paper.find("link").text
        results[key]["id"] = paper.find("guid").text
        user = url.split("/")[-1].split(".")[0]
        results[key]["pdf"] = url[:url.rindex(".")] + "/" + user + ".pdf"

    return results

def parse_paper(page_text:str):
    temp = {
        "authors":{},
        "pmlr_pdf":"",
        "github_url":"",
        "conf_info":"",
        "supplemental":""
    }
    bs4ob = BeautifulSoup(page_text, features="lxml")
    authors = bs4ob.find("span", class_="authors")
    if authors:
        auth_l = authors.text.split(",")
        for idx, author in enumerate(auth_l):
            temp["authors"][str(idx) + "_" + author.strip()] = author.strip()

    extras = bs4ob.find_all("li")
    if extras:
        pullbacks = ["Software", "Download PDF", "Supplementary PDF"]
        for extra in extras:
            if extra.text in pullbacks:
                funstuff = extra.find("a").get("href")
                if extra.text == "Software":
                    temp["github_url"] = funstuff
                elif extra.text == "Download PDF":
                    temp["pmlr_pdf"] = funstuff
                elif extra.text == "Supplmentary PDF":
                    temp["supplemental"] = funstuff

    #Pull in Conf into as well
    info = bs4ob.find("div", id="info")
    if info:
        temp["conf_info"] = info.text.strip()

    return temp

def cli():
    parser = argparse.ArgumentParser(
        prog="paper-search-sync",
        description="Synchronize conference datasets for PaperSearch",
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Run live web crawler to sync conference abstracts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scraping of conferences even if already cached locally.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Target a specific year (default: current year).",
    )

    args = parser.parse_args()

    if args.scrape:
        main(force=args.force, target_year=args.year)
    else:
        success = download_conferences_bundle()
        if not success:
            console.print("[yellow]Falling back to live scraper...[/yellow]")
            main(force=args.force, target_year=args.year)

def is_historical_and_cached(conf: str, year: int, force: bool) -> bool:
    """Historical years don't change. Skip them if they already exist on disk."""
    if force:
        return False
    current_year = datetime.datetime.now().year
    dest = CONF_DIR / f"{year}_{conf}.json"
    return year < current_year and dest.exists()


#NOTE START PROGRAM
#FUNCTION main
@log_time
def main(force: bool = False, target_year: int | None = None):
    """Main driver with delta/incremental sync."""
    current_year = datetime.datetime.now().year
    years = [target_year] if target_year else [current_year]
    logger.debug("Searching PMLR index...")
    PMLR = request_conf("PMLR", year=years[0])
    global prog, task
    prog, task = mainspinner(console, len(MAIN_CONFERENCES) * len(years) + len(PMLR.keys()))
    subconf = True  # Enable subconferences
    with prog:
        try:
            # ---------------------------------------------------------
            # 1. Main Conferences (Bulk JSONs - fast)
            # ---------------------------------------------------------
            for year in years:
                for conference in MAIN_CONFERENCES:
                    dest = CONF_DIR / f"{year}_{conference}.json"
                    
                    if is_historical_and_cached(conference, year, force):
                        logger.info(f"{conference}:{year} already cached. Skipping.")
                        prog.advance(task, 1)
                        continue

                    logger.info(f"{conference:7s}:{year} fetching bulk data")
                    prog.update(task_id=task, description=f"[green]{year}[/green]:[yellow]{conference}[/yellow]", advance=1)
                    
                    result = request_conf(conference, year)
                    if result:
                        save_conference(result, conference, year)
                    else:
                        logger.warning(f"{conference:7s}:{year} not available.")
                    
                    add_spin_subt(prog, f"[purple]{next(FUN_STATUS_UPDATE)}[/purple]", np.random.randint(2, 4))

            # ---------------------------------------------------------
            # 2. Minor Conferences (PMLR - individual paper scraping)
            # ---------------------------------------------------------
            if subconf and PMLR:
                for conference, link in PMLR.items():
                    year_str, conf = conference.split("_")
                    year = int(year_str)
                    conf = conf.strip()

                    if target_year and year != target_year:
                        continue

                    dest = CONF_DIR / f"{year}_{conf}.json"

                    if is_historical_and_cached(conf, year, force):
                        logger.info(f"{conf}:{year} is historical and cached. Skipping.")
                        prog.advance(task, 1)
                        continue

                    prog.update(task_id=task, description=f"[green]{year}[/green]:[yellow]{conf}[/yellow]", advance=1)
                    version = link.split("/")[-1]
                    
                    # 1 single request to get the PMLR conference paper list
                    feed_results = request_conf(link, version=version)
                    if not feed_results:
                        continue

                    # Load existing data if available
                    existing_data = {}
                    if dest.exists() and not force:
                        try:
                            with open(dest, "r", encoding="utf-8") as f:
                                existing_data = json.load(f)
                        except Exception as e:
                            logger.warning(f"Could not read existing {dest}: {e}")

                    # Determine which papers actually need detail fetching
                    papers_to_fetch = []
                    for title_key, paper_stub in feed_results.items():
                        # Fetch if:
                        # - Not in existing local data
                        # - Missing detail fields (like abstract or authors)
                        if title_key not in existing_data:
                            papers_to_fetch.append((title_key, paper_stub))
                        elif not existing_data[title_key].get("abstract") or not existing_data[title_key].get("authors"):
                            papers_to_fetch.append((title_key, paper_stub))
                        else:
                            # Keep cached version
                            feed_results[title_key] = existing_data[title_key]

                    # If everything is already cached and complete, skip the HTTP requests!
                    if not papers_to_fetch:
                        logger.info(f"{conf}:{year} is up-to-date ({len(existing_data)} papers). Skipping individual requests.")
                        add_spin_subt(prog, f"[green]{conf} up to date[/green]", 1)
                        continue

                    logger.info(f"{conf}:{year} has {len(papers_to_fetch)} new/updated papers to fetch out of {len(feed_results)}.")

                    # Only scrape details for new / incomplete papers
                    for title_key, paper_stub in papers_to_fetch:
                        detailed_paper = request_paper(paper_stub, version)
                        feed_results[title_key] = detailed_paper
                        logger.debug(f"Parsed {title_key}")
                        add_spin_subt(prog, f"[green]{title_key[:30]}[/green]", np.random.randint(1, 3))

                    save_conference(feed_results, conf, year)
                    add_spin_subt(prog, f"[yellow]{next(FUN_STATUS_UPDATE)}[/yellow]", 2)

        except KeyboardInterrupt:
            console.print("\n[yellow]Sync interrupted. Partial and completed datasets remain intact.[/yellow]")

if __name__ == "__main__":
    cli()
