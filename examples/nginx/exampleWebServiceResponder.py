from flask import Flask,redirect, url_for, request
import requests
import os
import sys
import json
import typesense
import math
import string
import re
import logging
import numpy as np
from numpy import sin, cos, pi, linspace
import time
import urllib.parse
from bs4 import BeautifulSoup

search_service_url = 'http://127.0.0.1:5002/aiwhispr'
top_level_domain='ZZZ.ZZZZ.COM'

def get_html_head():

    return '<html lang="en"><head><meta charset="utf-8"> <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"> <meta name="theme-color" content="#000000"> <link rel="manifest" href="./manifest.webmanifest"> <link rel="shortcut icon" href="./favicon.png"><link rel="stylesheet" href="index.css"><title>Whispr Search </title></head>'

def start_html_body():
    return '<body>'

def end_html_body():
    return '</body>'

def get_html_header():
    return '<header class="header"> <h2 style="display:flex;text-align:left;align-items:left"> <img src="http://demo.aiwhispr.com/aiwhispr_results.jpg"/> <a href="/" style="padding:10px;font-size:1.2rem""> AIWhispr Semantic Search</a> </h2> <p style="background-image:linear-gradient(284deg, #fedd4e, #fcb43a)"> <a> AIWhispr search results</a> </p></header>'

def get_html_style():
#    return '<style>.column{float:left;width:calc(25% - 1rem);margin-top:1rem;margin-left:1 rem;box-sizing:border-box;-moz-box-sizing:border-box;-webkit-box-sizing:border-box;border:1px solid black;padding:10px;margin:5px;border-radius:10px} .row:after{content:"";display:table;clear:both;} @media screen and (max-width:1000px){ .column{ width:100%;display:block;margin-bottom:20px;}} </style>'
    return '<style>.body{background-color:#eee} .column{float:left;width:calc(49% - 1rem);margin-top:1rem;margin-left:1 rem;box-sizing:border-box;-moz-box-sizing:border-box;-webkit-box-sizing:border-box;border:0px solid black;padding:10px;margin:5px;border-radius:10px;}  @media screen and (max-width:1000px){ .column{ width:100%;display:block;margin-bottom:20px;}} .linktopost{font-size:0.8rem;word-wrap:break-word} .numberofanswers{text-align:center;font-size:1.0rem;border-width:1px;border-radius:10px;border-style:solid;border-color:solid black;border-padding:1em;background-image: linear-gradient(284deg, #fedd4e, #fcb43a)} .posttitle{font-size:1.1rem;font-weight:bold;margin-top:10px} .question{word-wrap:break-word} .postcard{box-sizing:border-box;-moz-box-sizing:border-box;-webkit-box-sizing:border-box;border:1px solid black;padding:2px;margin:2px;border-radius:10px;font-size:16px;background-color:#FFFFFF} </style>'

###Remeber to change the log file path before running this in production
logging.basicConfig(filename='exampleWebServiceResponder.log', level=logging.DEBUG)
app = Flask(__name__)

#This is the search function that does a semantic vector search
@app.route('/search',methods = ['POST', 'GET'])
def semantic_search():
   if request.method == 'POST':
      input_query = request.form['query']
   else:
      input_query = request.args.get('query')
   app.logger.debug('INPUT_QUERY:' + input_query + '\n')    

   html_output = get_html_head() + get_html_header() + start_html_body()
   html_output = html_output + get_html_style() 
   html_output = html_output + '<div class="row">'

   query_url=search_service_url + '?query='+ urllib.parse.quote(input_query) + '&resultformat=html&withtextsearch=Y'
   r = requests.get(query_url)
 
   soup = BeautifulSoup(r.text, 'lxml')
   semantic_match_results = str(soup.find_all("div", class_="aiwhisprSemanticSearchResults")[0])
   app.logger.debug("Found semantic search results: %s ", semantic_match_results)
   text_match_results = str(soup.find_all("div", class_="aiwhisprTextSearchResults")[0])
   app.logger.debug("Found text search results: %s ", text_match_results)

   html_output = html_output + ' <div class="column">' + '<p><b>Semantic Search Results</b></p><br>' + str(semantic_match_results) + '</div>'
   html_output = html_output + ' <div class="column">' + '<p><b>Text Search Results</b></p><br>' + str(text_match_results) + '</div>'   
   html_output = html_output + '</div>'  # End of div row
   html_output = html_output + end_html_body() + '</html>'

   #html_output = html_output + r.text + '</div>' + end_html_body() + '</html>'

   return html_output

### END OF FUNCTION SEARCH MASFAQ

if __name__ == '__main__':
   #Start Flask App on default port 5000
   app.run(debug=True,host='0.0.0.0')

