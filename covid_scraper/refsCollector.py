# -*- coding: utf-8 -*-
"""
Created on Wed May 13 14:23:21 2020

@author: philv
"""
import os
import json
import numpy as np
import cfscrape
from bs4 import BeautifulSoup as bs # HTML parser
from similarity.ngram import NGram
from similarity.metric_lcs import MetricLCS
import textdistance

def xml_to_str(ref):
    authors_list = []
    authors = ref.find_all('string-name')
    if authors:
        for author in authors:
            surname = author.find('surname')
            given_names = author.find('surname')
            if not surname:
                surname = ""
            else:
                surname = surname.text
            if not given_names:
                given_names = ""
            else:
                given_names = given_names.text
            authors_list.append(surname + ',' + given_names)
    authors_str = ','.join(authors_list)
    
    year = ref.find('year')
    if not year:
        year = ""
    else:
        year = year.text
        
    title = ref.find('article-title')
    if not title:
        title = ""
    else:
        title = title.text
        
    source = ref.find('source')
    if not source:
        source = ""
    else:
        source = source.text
    ref_str = authors_str+year+title+source
    ref_str = ref_str.replace(' ','%20')
    return ref_str

def crossref_to_str(ref):
    authors_str = ""
    if 'author' in ref:
        list_authors = ref['author']
        nb_authors = len(list_authors)
        keep_authors = []
        if nb_authors>3:
            for i in [0,1,-1]:
                keep_authors.append(list_authors[i])
        else:
            keep_authors= list_authors
        authors = []
        for author in keep_authors:
            if 'family' in author and 'given' in author:
                authors.append(','.join([author['family'],author['given']]))
        authors_str = ','.join(authors)
    title_str = ""
    if 'title' in ref:
        title_str = ref['title'][0]
    journal_str = ""
    if 'container-title' in ref:
        journal_str = ref['container-title'][0]
    date_str = ""
    if 'created' in ref:
        date_str = '-'.join(map(str,ref['created']['date-parts'][0]))
    return ','.join([authors_str,date_str,title_str,journal_str])
        
def match_refs(platform,force_match=False,parser="refextract",min_len_ref=100,
               min_sim=0.5):
    if parser == "cermine":
        files_dir = np.array(os.listdir(os.path.join("data","pdf",platform)))
        xml_files = files_dir[np.char.endswith(files_dir,'.cermxml')]
    elif parser == "refextract":
        files_dir = np.array(os.listdir(os.path.join("data","json",platform)))
        xml_files = files_dir[np.char.endswith(files_dir,'.json')]
    scraper = cfscrape.create_scraper() # returns a requests.Session object
    base_url = "https://api.crossref.org/works?query.bibliographic={}"

    #Get the list of downloaded pdfs.
    matched_refs = np.array(os.listdir(os.path.join("data","refs",platform)))
    matched_refs_IDs = np.array(['.'.join(x.split('.')[:-1]) for x in matched_refs])
    xml_IDs = np.array(['.'.join(x.split('.')[:-1]) for x in xml_files])
    if force_match:
        matched_refs_IDs = []
    files_to_match = xml_files[~np.isin(xml_IDs,matched_refs_IDs)]
    
    nb_files = len(files_to_match)
    for i in range(nb_files):
        print("Matching with Crossref {}: {}/{}.".format(platform,i+1,nb_files))
        file_name = files_to_match[i]
        if parser == "cermine":
            with open(os.path.join("data","pdf",platform,file_name),'r',encoding='utf-8') as f:
                xml = bs(f.read(), 'html.parser')
            references = xml.find_all('ref')
            references_str = [xml_to_str(ref) for ref in references]
        elif parser == "refextract":
            references = json.loads(open(os.path.join("data","json",platform,file_name),'r').read())
            raw_refs = []
            refs_linemarker = {}
            for ref in references:
                raw_ref = ref['raw_ref'][0]
                
                if 'linemarker' in ref:
                    marker = ref['linemarker'][0]
                    if marker in refs_linemarker:
                        refs_linemarker[marker].append(raw_ref)
                    else:
                        refs_linemarker[marker] = [raw_ref]
                else:
                    raw_refs.append(raw_ref)
            #Sometimes references are duplicated. Only keep the longest.
            for marker in refs_linemarker:
                refs = refs_linemarker[marker]
                len_refs = [len(x) for x in refs]
                raw_refs.append(refs[np.argmax(len_refs)])
            references_str = []
            for ref in raw_refs:
                if len(ref) >= min_len_ref:
                    references_str.append(ref.replace(' ','%20'))
                    
        ID_file = '.'.join(file_name.split('.')[:-1])
        with open(os.path.join("data","refs",platform,ID_file+'.csv'),'w',encoding='utf-8') as f:    
            f.write("doi|query|crossref_match|type|sim\n")
            for ref_str in references_str:
                query_url = base_url.format(ref_str)
                query = json.loads(scraper.get(query_url).text)
                items = query['message']['items']
                keep_items = []
                for item in items:
                    if 'type' in item:
                        if item['type'] in ["posted-content","journal-article"]:
                            keep_items.append(item)
                
                items_sim = []
                base = ref_str.replace('%20',' ')
                for item in keep_items:
                    item_str = crossref_to_str(item)
                    items_sim.append(textdistance.ratcliff_obershelp.similarity(item_str,base))
                
                if len(keep_items) > 0:
                    matched_item = keep_items[np.argmax(items_sim)]
                    matched_sim = np.max(items_sim)

            
                if matched_sim>=min_sim:
                    crossref_txt = crossref_to_str(matched_item)
                    doi = matched_item['DOI']
                    f.write('|'.join([doi,ref_str.replace('%20',' '),crossref_txt,matched_item['type'],str(matched_sim)])+'\n')
                    
                    
                
               

        
