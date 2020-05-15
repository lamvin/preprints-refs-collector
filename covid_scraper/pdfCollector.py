# -*- coding: utf-8 -*-
"""
Created on Tue May 12 10:07:48 2020

@author: philv
"""


import os # Useful for file system operations
from bs4 import BeautifulSoup as bs # HTML parser
import cfscrape
import requests
import time
from selenium import webdriver # Web browser automation tools
import pandas as pd
import subprocess
from refextract import extract_references_from_file
import numpy as np
import json

def get_pdfs(platform,out_path):
    meta_data = pd.read_csv(os.path.join("data","meta",platform+".csv"),sep="|",
                            header=None,
                            error_bad_lines=False)
    if platform == "arxiv":
        meta_data.columns = ["ID","date","sub","title","authors","abstract","categories"]
        meta_data['link'] = meta_data["ID"].apply(lambda x: "http://arxiv.org/pdf/{}.pdf".format(x))
    elif platform in ['medrxiv','biorxiv']:
        meta_data.columns = ["ID","date","title","authors"]
        abstracts = pd.read_csv(os.path.join("data","meta",platform+"_abs.csv"),sep="|",
                            error_bad_lines=False)
        abstracts.columns = ["ID","abstract","link"]
        meta_data = pd.merge(meta_data,abstracts,on="ID",how="left")
        meta_data = meta_data.loc[~meta_data['link'].isnull()]
        meta_data['link'] = meta_data["link"].apply(lambda x: "http://" + x)
        
    try:
        #Get the list of downloaded pdfs.
        pdf_downloaded = open(os.path.join("data","meta",platform+"_pdf.txt"),'r').read().splitlines()
    except FileNotFoundError:
        pdf_downloaded = []
        
    key_data = pd.read_csv(os.path.join("data","meta",platform+"_key.csv"),sep="|")
    data = pd.merge(meta_data,key_data,on="ID")
    data = data.loc[data["key_related"]]
    data = data.loc[~data["ID"].isin(pdf_downloaded)]
    data = data.drop_duplicates("ID")
        
    dl_path = os.path.abspath(out_path)
    options = webdriver.ChromeOptions()
    options.add_experimental_option('prefs', {
    "download.default_directory": dl_path, #Change default directory for downloads
    "download.prompt_for_download": False, #To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
    })
    driver = webdriver.Chrome(options = options,executable_path="tools/chromedriver.exe")
    nb_links = len(data)
    
    with open(os.path.join("data","meta",platform+"_pdf.txt"),'a') as f:
        for i in range(nb_links):
            row = data.iloc[i]
            link = row["link"]
            ID = row["ID"]
            print("{}: Downloading pdf: {}/{}.".format(platform,i+1,nb_links))
            driver.get(link)
            f.write(ID+"\n")
            time.sleep(2)
    time.sleep(10)
        
def execute(cmd):
    popen = subprocess.Popen(cmd, cwd= os.path.abspath('tools'), stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)
        
def parse_pdfs(platform,parser="refextract"):
    pdf_path = os.path.join("..","data","pdf",platform)
    if parser == "cermine":
        jar_path = 'cermine-impl-1.13-jar-with-dependencies.jar'  
        for path in execute(['java', '-cp', jar_path, 'pl.edu.icm.cermine.ContentExtractor',
                     '-path', pdf_path,
                     '-outputs','jats'
                     ]):
            print(path, end="")
    elif parser == 'refextract':
        files_dir = np.array(os.listdir(os.path.join("data","pdf",platform)))
        pdf_files = files_dir[np.char.endswith(files_dir,'.pdf')]
        parsed_pdfs = np.array(os.listdir(os.path.join("data","json",platform)))
        parsed_json_IDs = np.array(['.'.join(x.split('.')[:-1]) for x in parsed_pdfs])
        parsed_IDs = np.array(['.'.join(x.split('.')[:-2]) for x in pdf_files])
        files_parse = pdf_files[~np.isin(parsed_IDs,parsed_json_IDs)]
        files_parse_ID = parsed_IDs[~np.isin(parsed_IDs,parsed_json_IDs)]
        nb_files = len(files_parse)
        with open(os.path.join("data","meta",platform+"_pdfs_parsed.txt"),'a') as f:
            for i in range(nb_files):
                print("Extracting refs {}: {}/{}.".format(platform,i+1,nb_files))
                file = files_parse[i]
                file_ID = files_parse_ID[i]
                references = extract_references_from_file(os.path.join("data","pdf",platform,file))
                with open(os.path.join("data","json",platform,file_ID+".json"),'w') as f:
                    json.dump(references,f)

