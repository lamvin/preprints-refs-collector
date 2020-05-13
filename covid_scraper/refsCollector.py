# -*- coding: utf-8 -*-
"""
Created on Wed May 13 14:23:21 2020

@author: philv
"""
import os
from bs4 import BeautifulSoup as bs
import numpy as np

def xml_to_str(ref):
    authors_list = []
    authors = ref.find_all('string-name')
    if authors:
        for author in authors:
            surname = author.find('surname').text
            given_names = author.find('surname').text
            if not surname:
                surname = ""
            if not given_names:
                given_names = ""
            authors_list.append(surname + ',' + given_names)
    authors_str = ','.join(authors_list)
    
    year = ref.find('year').text
    if not year:
        year = ""
        
    title = ref.find('article-title').text
    if not title:
        title = ""
        
    source = ref.find('source').text
    if not source:
        source = ""
    ref_str = authors_str+year+title+source
    ref_str = ref_str.replace(' ','%20')
    return ref_str
    
def match_refs(platform,force_match=False):
    files_dir = np.array(os.listdir(os.path.join("data","pdf",platform)))
    xml_files = files_dir[np.char.endswith(files_dir,'.cermxml')]
    
    try:
        #Get the list of downloaded pdfs.
        refs_matched = open(os.path.join("data","meta",platform+"_matched_refs.txt"),'r').read().splitlines()
    except FileNotFoundError:
        refs_matched = []
    if force_match:
        refs_matched = []
    files_to_match = xml_files[~np.isin(xml_files,refs_matched)]
    
    nb_files = len(files_to_match)
    for i in range(nb_files):
        file_name = files_to_match[i]
        with open(os.path.join("data","pdf",platform,file_name),'r') as f:
            xml = bs(f.read(), 'html.parser')
        references = xml.find_all('ref')
        for ref in references:
            ref_str = xml_to_str(ref)
        
