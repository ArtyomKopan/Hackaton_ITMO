import os
import pandas as pd
from parsing_pdf import parse

base_directory = 'C:/Users/kopan/Programming/Hackatn_ITMO'

for file in os.listdir(f'{base_directory}/data'):
    if file.endswith('.pdf'):
        input_file_path = f'{base_directory}/data/{file}'
        output_file_path = f'{base_directory}/data/{file[:-4]}.txt'
        parse(input_file_path, output_file_path)
