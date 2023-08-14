import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import bs4
import mecab_ko
import pandas as pd
import re
import random
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

requests.packages.urllib3.disable_warnings()
def Make_Workbook():
    df = pd.DataFrame(columns=['퀴즈번호', '퀴즈문제'])
    print('★☆문제 크롤링★☆')
    start_time = time.time()

    start_seq = 3123
    end_seq = 3671
    for seq in range(start_seq, end_seq + 1):
        url = f'https://www.nis.go.kr:4016/CM/1_5_1/view.do?seq={seq}&currentPage=1&selectBox=&searchKeyword=&fromDate=&toDate='
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        target_div = soup.find('div', class_='board-content txt-spo-body-2-400 font-gray01')
        extracted_text = soup.find_all('p', class_='label-text txt-spo-body-2-400 font-gray01')
        a = extracted_text[1].text
        b = a.split()[1][:-1]
        if b == '':
            continue
        c= int(b)

        if target_div and b:
            value = target_div.text.strip()
            new_row = {'퀴즈번호': c, '퀴즈문제': value}
            df.loc[len(df)] = new_row
            print('퀴즈번호: ', c , '문제 크롤링 완료')

        else:
            print(f"Seq {b}: 해당하는 div 태그를 찾을 수 없습니다.")
    df = df.sort_values(by='퀴즈번호', ascending=True)

    end_time = time.time()
    execution_time = end_time - start_time
    print("코드 실행 시간:", execution_time, "초")
    print('★☆정답 크롤링★☆')
    start_time = time.time()

    a_list = []
    b_list = []

    for i in range(51):
        n = i+1
        url = "https://www.nis.go.kr:4016/CM/1_5_2/list.do?selectBox=0&fromDate=&toDate=&searchKeyword=&currentPage={}".format(n)

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(service=Service(), options=chrome_options)

        driver.get(url)
        time.sleep(1)
        bsObj = bs4.BeautifulSoup(driver.page_source, "html.parser")
        bslist = bsObj.find('tbody', {'class':'txt-spo-body-2-400 font-gray01'}).find_all("tr")
        for key, value in enumerate(bslist):
            seq = value.attrs['id']
            onclick = value.find('a', {'class':'font-gray01 text-table-ellipsis'}).attrs['onclick']
            onclick = onclick.replace('$.view(', '')
            onclick = onclick.split(",")[0]
            url = 'https://www.nis.go.kr:4016/CM/1_5_2/view.do?seq={}&currentPage=1&quizNum={}&selectBox=0&searchKeyword=&fromDate=&toDate='.format(seq, onclick)
            driver.get(url)

            xpath = '//*[@id="selectListForm"]/div/div[1]/div[1]'
            answer_xpath = driver.find_element(By.XPATH, xpath)
            answer = answer_xpath.text

            xpath2 = '//*[@id="selectListForm"]/div/div[1]/ul/li[2]/p/span'
            num_xpath = driver.find_element(By.XPATH, xpath2)
            num = num_xpath.text

            match = re.search(r'제 (\d+)회', num)
            if match:
                extracted_number = match.group(1)
                if extracted_number == '101':
                    break
            else:
                print("숫자를 찾을 수 없습니다.")

            index_start =answer.find("정답 및 해설")
            if index_start != -1:
                answer = answer[index_start + 8:]

            index_end = answer.find("당첨자 명단")
            if index_end != -1:
                answer = answer[:index_end]
            a_list.append(int(extracted_number))
            b_list.append(answer)
            print('퀴즈번호: ', extracted_number, '정답 크롤링 완료')

    data = {
        '퀴즈번호':a_list,
        '정답': b_list
    }

    df2 = pd.DataFrame(data)
    df2 = df2.set_index('퀴즈번호')
    df2 = df2.sort_values('퀴즈번호', ascending=True)
    df2['정답'] = df2['정답'].str.lstrip()

    df_final = pd.merge(df, df2, on='퀴즈번호', how='inner')
    df_final.to_excel('NIS_Workbook.xlsx', index=False)

    end_time = time.time()
    execution_time = end_time - start_time
    print("코드 실행 시간:", execution_time, "초")

def problem_solving():
    print('★☆문제 출력★☆')
    start_time = time.time()

    file_path = 'NIS_Workbook.xlsx'
    df = pd.read_excel(file_path)

    random_index = random.randint(0, len(df['퀴즈문제']) - 1)
    random_item = df['퀴즈문제'][random_index-1]
    print("무작위 선택된 문제:", random_item)

    df = pd.read_excel(file_path)
    m = mecab_ko.Tagger()
    NG_WORDS = ['은', '는', '이', '가', '의', '습니다', '을', '를', '와', '과', '에']

    cleaned_text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', df['정답'][random_index-1])
    result = m.parse(cleaned_text)
    lines = result.split('\n')

    tokens1 = []
    for line in lines:
        if line == 'EOS':
            break
        parts = line.split('\t')
        if len(parts) > 1:
            if parts[0] not in NG_WORDS:
                tokens1.append(parts[0])

    user_input = input("정답을 입력하세요: ")
    print("입력값:", user_input)

    NG_WORDS = ['은','는','이','가','의','습니다','을','를','와','과','에']
    m = mecab_ko.Tagger()
    asdf = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', user_input)

    result = m.parse(asdf)
    lines = result.split('\n')

    tokens2 = []
    for line in lines:
        if line == 'EOS':
            break
        parts = line.split('\t')
        if len(parts) > 1:
            if parts[0] not in NG_WORDS:
                tokens2.append(parts[0])

    similarity_ratio = cosine_similarity_score(tokens1,tokens2)

    if similarity_ratio > 0.75:
        print('정답!')
    else: print('오답!')

    end_time = time.time()
    execution_time = end_time - start_time
    print("코드 실행 시간:", execution_time, "초")

def cosine_similarity_score(list1, list2):
    set1 = set(list1)
    set2 = set(list2)

    all_words = list(set1.union(set2))

    vector1 = [1 if word in set1 else 0 for word in all_words]
    vector2 = [1 if word in set2 else 0 for word in all_words]

    vector1 = np.array(vector1)
    vector2 = np.array(vector2)

    similarity_score = cosine_similarity([vector1], [vector2])[0][0]

    return similarity_score

# Make_Workbook()
problem_solving()
