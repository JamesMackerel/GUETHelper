import requests
from bs4 import BeautifulSoup
from typing import *
import re


class GuetHelper:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.session = requests.session()
        self.student_info: Dict[str, str] = dict()
        self.login_status = False

    def login(self) -> Union[None, bool]:
        """登录教务系统

        在登录教务系统的同时还会获取学生信息。

        :return:
            登录成功则返回True，否则返回False
        """
        payload = {'username': self.username, 'passwd': self.password, 'login': '%B5%C7%A1%A1%C2%BC'}
        self.session.post('http://bkjw.guet.edu.cn/student/public/login.asp', data=payload)
        info_page = BeautifulSoup(self.session.get('http://bkjw.guet.edu.cn/student/Info.asp').content,
                                  'html.parser').find_all('p')

        # 判断是否登录成功。如果未成功，学号等信息是无法显示出来的
        self.student_info['id'] = info_page[0].string.split(':')[1]
        if self.student_info['id'] == '':
            print('[GuetHelper]Login failed.')
            return False
        self.login_status = True
        print('[GuetHelper]login successfully')

        self.student_info['name'] = info_page[1].string.split(':')[1]
        self.student_info['class'] = info_page[2].string.split(':')[1]
        self.student_info['grade'] = info_page[3].string.split(':')[1]
        self.student_info['term'] = info_page[4].string.split(':')[1]

    def logout(self) -> None:
        self.session.get('http://bkjw.guet.edu.cn/student/public/logout.asp')

    def get_selected_lesson(self, term: str) -> Union[None, Tuple[List[str], List[List[str]]]]:
        """
        获取已选课程列表
        :param term: 学期编号，格式如 2017-2018_1，意为2017-2018学年第一学期
        :return: 返回两个list，第一个保存表头，第二个保存表格数据。每一行数据又是一个list。
        """
        check_regex = re.compile('\d+-\d+_[12]')
        if check_regex.match(term) is None:
            raise ValueError('学期格式不正确，正确的示例：2017-2018_1，意为2017年到2018年上学期')

        if self.login_status is False:
            return None

        payload = {'term': term}
        page = self.session.post('http://bkjw.guet.edu.cn/student/Selected.asp', data=payload)
        table = BeautifulSoup(page.content, 'html.parser').find_all('tr')
        th = table[0]
        data = table[1:-1]

        selected_lesson_headers = list()
        selected_lesson_data = list()

        # get headers, and delete redundant characters from them.
        for h in th.find_all('th'):
            selected_lesson_headers.append(h.string.replace('\u3000', '').replace(' ', ''))
        tmp_data = list()
        for d in data:
            tmp_data.clear()
            for col in d.find_all("td"):
                tmp_data.append(col.string.encode().decode())
            selected_lesson_data.append(tmp_data.copy())

        return selected_lesson_headers, selected_lesson_data

    def get_score(self) -> Union[None, Tuple[List[str], List[List[str]], str]]:
        """对应“已学课程成绩”查询页面。

        使用示例：
        score_header, score_data, interest_credit = guethelper.get_score()

        :return:
            返回三个值：
            1. 一个list，保存了成绩单表头；
            2. 一个list，保存了成绩单的数据，每一条数据又是一个list，数据的各项对应表格的各列；
            3. 一个str，是当前获取的兴趣学分数。
            若未登录就调用，则返回None。
        """
        if self.login_status is False:
            return None

        score_headers: List[str] = list()
        score_data: List[List[str]] = list()
        interest_credit = 0

        payload = {'ckind': '', 'lwPageSize': 1000, 'lwBtnquery': '%B2%E9%D1%AF'}
        page = self.session.post('http://bkjw.guet.edu.cn/student/Score.asp', data=payload)
        table = BeautifulSoup(page.content, 'html.parser').find_all('tr')
        th = table[0]
        data = table[1:-1]

        # get headers, and delete redundant characters from them.
        for h in th.find_all('th'):
            score_headers.append(h.string.replace('\u3000', '').replace(' ', ''))

        tmp_data = list()
        for d in data:
            tmp_data.clear()
            for col in d.find_all("td"):
                tmp_data.append(col.string.encode().decode())
            score_data.append(tmp_data.copy())

        interest_credit: str = re.compile('\d+').findall(table[-1].string)[0]

        return score_headers, score_data, interest_credit


if __name__ == '__main__':
    pass
