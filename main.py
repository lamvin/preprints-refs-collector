# -*- coding: utf-8 -*-
"""
Created on Sun May 10 08:49:19 2020

@author: philv
"""

import os
from covid_scraper import MetaCollector, pdfCollector, refsCollector
import datetime
import sys

if __name__ == "__main__":
    
    args = sys.argv
    nb_args = len(args)
    mode = args[1]
    if nb_args == 3:
        start_date = datetime.datetime.strptime(args[2],'%Y-%m-%d')
    else:
        start_date = None
    platforms = ['medrxiv','biorxiv','arxiv']
    print(mode)
    if mode == "meta" or mode == "all":
        
        out_path = os.path.join("data","meta")
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        
        ''' This will collect metadata on all submissions that were last updated 
        at the starting date or later. This means that the initial submission
        might be earlier than the starting date.
        '''
        for platform in platforms:
            MetaCollector.collect_data(platform,start_date)

        ''' There are no abstracts attached to the bioRxiv and medRxiv
        metadata. We need to grab this information on each page individually.
        This function uses the metadata files and will try to collect the 
        abstract that haven't been collected previously.'
        '''
        for platform in ['medrxiv','biorxiv']:
            MetaCollector.collect_abs(platform)            
        
        '''
        Tag the submissions as COVID related based on a regex match in the title
        and in the abstract.
        '''
        #keywords = ['covid','corona','sars-cov-2','ncov']
        regex_search = "(\\s|\\b)(ncov)([^a-z]|\\b)|(\\s|\\b)(corona)[\\s-]?(virus)([^a-z]|\\b)|(\\s|\\b)(sars-cov-2)([^a-z]|\\b)|(\\s|\\b)(covid)([^a-z]|\\b)"
        for platform in platforms:
            MetaCollector.tag_keywords(platform,regex_search)      

    if mode == "pdf" or mode == "all":
        for platform in platforms:
            out_path = os.path.join("data","pdf",platform)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            pdfCollector.get_pdfs(platform,out_path)
        
        '''
        Parse the pdfs with cermine. 
        '''
        for platform in platforms:
            out_path = os.path.join("data","json",platform)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            pdfCollector.parse_pdfs(platform)
            
    if mode == "refs" or mode == "all":
        for platform in platforms:
            out_path = os.path.join("data","refs",platform)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            refsCollector.match_refs(platform,out_path)