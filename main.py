import streamlit as st
st.set_page_config(layout="wide") 

from streamlit_option_menu import option_menu
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from cv_extractor import cv_extractor
from home import home

EXAMPLE_NO = 1
def streamlit_menu(example=1):
   if example == 1:
       with st.sidebar:
           return option_menu(
               menu_title="Main Menu",
               options=["Home", "cv_assistant"],
               icons=["house", "file-earmark-text"],
               menu_icon="cast",
               default_index=0
           )
   
   if example == 2:
       return option_menu(
           menu_title=None,
        #    options=["Home", "Projects", "Contact"],
           options=["Home", "cv_extractor_assistant"],
           icons=["house", "book", "envelope"],
           menu_icon="cast",
           default_index=0,
           orientation="horizontal"
       )
   
   if example == 3:
       return option_menu(
           menu_title=None,
        #    options=["Home", "Projects", "Contact"],
           options=["Home", "cv_assistant"],
           icons=["house", "book", "envelope"],
           menu_icon="cast",
           default_index=0,
           orientation="horizontal",
           styles={
               "container": {"padding": "0", "background-color": "#fafafa"},
               "icon": {"color": "orange", "font-size": "25px"},
               "nav-link": {
                   "font-size": "25px",
                   "text-align": "left",
                   "margin": "0px",
                   "--hover-color": "#eee",
               },
               "nav-link-selected": {"background-color": "green"},
           }
       )

selected = streamlit_menu(example=EXAMPLE_NO)

if selected == "Home":
    home.app()
elif selected == "cv_assistant":
    cv_extractor.app()