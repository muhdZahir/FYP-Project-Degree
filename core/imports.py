# pip install streamlit | streamlit is use to create the UI.
import streamlit as st
import pandas as pd  # pip install pandas | pandas is use to analyze data from csv/xlsx
import numpy as np # pip install numpy | numpy is use to handle array and do mathematical operation
import calendar # to handle month name and month number conversion
import time # to handle time delay
import os # to handle file path
import re # to handle naming convention
from datetime import datetime # to handle date and time

import sqlite3  # For database operations, using SQLite for simplicity
from sqlalchemy import create_engine # For PostgreSQL connection
import psycopg2 # For PostgreSQL connection
import core.database as db  # Importing your database.py

import plotly.express as px # pip install plotly | plotly is use to create interactive visualization/chart
from sklearn.linear_model import LinearRegression # pip install scikit-learn | LinearRegression is use to do linear regression analysis