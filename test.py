import os
from enum import Enum, unique
from zipfile import ZipFile, BadZipFile
import requests


def download_url_unzip(url, chunk_size=128):
    save_path = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
    nested_file = save_path.replace('zip', 'csv')
    with ZipFile(save_path, 'r') as loaded_zip:
        loaded_zip.extract(nested_file)
    return nested_file


@unique
class AnswerOptions(Enum):
    def __str__(self):
        return self.name.lower()


class Deal(AnswerOptions):
    FUTURES = 0
    SPOT = 1


class FuturesChoice(AnswerOptions):
    CM = 0
    UM = 1


class DataType(AnswerOptions):
    KLINES = 0
    TRADES = 1


def check_answer(enum_class):
    answers = dict()
    for item in enum_class:
        answers[item] = [str(item), str(item)[0], str(item.value)]
    question = f'{" or ".join([enum_field.name for enum_field in answers.keys()])}?\n'
    for answer, corresponding_answers in answers.items():
        question += f'{answer.name}: input {" or ".join(corresponding_answers)}\n'
    while True:
        given_answer = input(question)
        for answer, corresponding_answers in answers.items():
            if given_answer in corresponding_answers:
                return answer
        print('Error: Invalid answer')


base_url = ['https://data.binance.vision/data', ]

deal = check_answer(Deal)
base_url.append(str(deal))

if deal is Deal.FUTURES:
    base_url.append(str(check_answer(FuturesChoice)))

base_url.append('monthly')

data_type = check_answer(DataType)
base_url.append(str(data_type))

# Symbol input
filename_components = list()
value = input('Input Value: ')
filename_components.append(value)
base_url.append(value)

# Timeframe input
if data_type is DataType.KLINES:
    timeframe = input('Input timeframe: ')
    filename_components.append(timeframe)
    base_url.append(timeframe)
elif data_type is DataType.TRADES:
    filename_components.append('trades')

# Years input
while True:
    try:
        years = tuple(map(int, input('Input first and last years or one year: ').strip().split()))
        first_year = years[0]
        last_year = first_year if len(years) == 1 else years[1]
        break
    except:
        print('Error: Invalid year(s)')

# Loading and unpacking
for year in range(first_year, last_year + 1):
    for month in range(1, 12 + 1):
        month = f'{year}-{month:02}'
        filename = '-'.join(filename_components) + f'-{month}.zip'
        url = '/'.join(base_url) + f'/{filename}'
        try:
            print(f'Requesting URL: {url}')
            print(f'Loaded file: {download_url_unzip(url)}')
        except BadZipFile:
            print(f'File {filename} not found')

# Cleaning up all the archives
for file in os.listdir(os.getcwd()):
    if file.endswith('.zip'):
        os.remove(os.path.abspath(file))
