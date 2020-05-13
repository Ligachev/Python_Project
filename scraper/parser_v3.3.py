"""Module documentation parser

class Hello - принимает данные от пользователя.
class AirblueParser парсер данных.
class Print_info вывод информации в stdout.

"""

import sys
import re
import datetime
from itertools import product
import requests
import lxml.html
from prettytable import PrettyTable


# public symbols
__all__ = [
    "cycle", "Hello", "AirBlueParser", "PrintInfo",
]

__version__ = "3.3."


def cycle(method):
    """Декоратор

    Зациклить выполнение метода.
    Вернуть валидный результат.
    """
    def wrap(self, value):
        while True:
            result = method(self, value)
            if result != 'Incorrect value':
                return result
    return wrap


CITIES = {'AUH': 'Abu Dhabi', 'DMM': 'Dammam', 'DXB': 'Dubai',
          'ISB': 'Islamabad', 'JED': 'Jeddah', 'KHI': 'Karachi',
          'LHE': 'Lahore', 'MCT': 'Muscat', 'MED': 'Medina',
          'MUX': 'Multan', 'PEW': 'Peshawar', 'RUH': 'Riyadh',
          'RYK': 'Rahim Yar Khan', 'SHJ': 'Sharjah', 'SKT': 'Sialkot',
          'UET': 'Quetta'}


class Hello:
    """

    Получить данные от пользователя, проверить на валидность.

    __init__ - конструктор.
    into_iata - передать iata код.
    into_day - передать число.
    info - получить список iata кодов.

    """

    def __init__(self):
        """Конструктор

        cities - список iata кодов.
        departure - пункт отправления.
        destination - пункт назначения.
        dep_date - дата отправления
        arr_date - дата прибытия
        """

        print('\nWelcome to AirBlue!\n')
        self.departure = self.into_iata('departure')
        self.destination = self.into_iata('destination')
        self.dep_date = self.into_day('departure')
        self.arr_date = self.into_day('return trip')

    @cycle
    def into_iata(self, place_name):
        """Обработать переданную строку.

        Принять от пользователя строку.
        Проверить строку на соответствие шаблону.
        Вернуть валидное значение.
        """
        Hello.info()
        iata = (input('\nEnter the IATA code for {}:'.format(place_name))).strip()

        if re.match('[A-Z]{3}', iata) and iata in CITIES:
            if place_name == 'destination' and iata == self.departure:
                print("Invalid value entered:"
                      "\nThe departure and destination codes are the same!")
                return 'Incorrect value'
            return iata
        print('Invalid value entered!\nEnter the correctly code IATA:\n')
        return 'Incorrect value'

    @cycle
    def into_day(self, departures):
        """Обработать переданную строку.

        Принять от пользователя строку.
        Устоновить максимально допустимые значения даты 'present' и 'max'.
        Преобразовать число из type <str> => <datatime>.
        Обработать исключение ValueError.
        Выполнить проверку вхождения даты в диапазон 'present' и 'max'.
        Вернуть валидное значение.
        """
        date_str = (input('\nIndicate the desired {} date in the format YYYY/MM/DD:'
                          .format(departures))).strip()
        present = datetime.date.today()
        max_day = present + datetime.timedelta(128)

        if not date_str and departures == 'return trip':
            return None

        try:
            date = datetime.datetime.strptime(date_str, '%Y/%m/%d').date()
            if departures == 'return trip':
                if self.dep_date > date:
                    print('Return date cannot be earlier than arrival date!')
                    return 'Incorrect value'

            if date >= max_day or date < present:
                print('Incorrect data!\n'
                      'Date must be between {} and {}'.format(present, max_day))
                return 'Incorrect value'
            return date
        except ValueError:
            print('Incorrect data format, should be YYYY/MM/DD!')
            return 'Incorrect value'

    @staticmethod
    def info():
        """Печать справки

        Вывести в stdout dict{'iata код': 'название города'.
        """
        j = 0
        for i in CITIES:
            print(("{}".format(i)).ljust(10, '.') +
                  ("{}".format(CITIES[i])).rjust(15, '.'), end='\t')
            j += 1
            if j == 4:
                print('\r')
                j = 0


class AirBlueParser:
    """

    Парсер для получения информации о полётах.

    __init__ - конструктор.
    get_req - GET запрос.
    parser - сформировать запрос на рейсы.
    parse_quotas - извлечь информацию о рейсе.
    travel_time - посчитать время в пути.
    cost - определить класс обслуживания.
    price - сформировать цену.
    combine_quotas - объеденить рейсы по парно.

    """

    def __init__(self, departure, destination, dep_date, arr_date=None):
        """Конструируктор.

        items - хранилище данных.
        """
        self.departure = departure
        self.destination = destination
        self.dep_date = dep_date
        self.arr_date = arr_date
        self.printer = PrintInfo()

    def get_search_params(self):
        """Сформировать словарь для выполнения GET запроса."""
        data = {
            'DC': self.departure,
            'AC': self.destination,
            'AM': self.dep_date.strftime('%Y-%m'),
            'AD': self.dep_date.strftime('%d'),
            'TT': 'OW',
            'FL': 'on',
            'CC': 'Y',
            'CD': '',
            'PA': '1',
            'PC': '',
            'PI': '',
        }

        if self.arr_date:
            data.update({
                'RM': self.arr_date.strftime('%Y-%m'),
                'RD': self.arr_date.strftime('%d'),
                'TT': 'RT'
            })

        return data

    def get_req(self):
        """Выполнить GET запрос.

        Выполнить GET запрос.
        Проверяет ответ с сервера.
        Обработать исключение requests.ConnectionError.
        Передать Html страницу в 'parser'.
        """
        print("Expect your request to be processed.\n")

        try:
            res = requests.get(
                url='https://www.airblue.com/bookings/flight_selection.aspx',
                params=self.get_search_params()
            )
            if res.status_code < 400:
                self.parser(res.content)
            else:
                print("Connection Error!")
                sys.exit()
        except requests.ConnectionError:
            print("Connection Error!")
            sys.exit()

    def parser(self, html):
        """Формирует html tree.

        Выполнить проверку на запрошенное колличество рейсов.
        Получить информацию по рейсам из 'parse_quotas'.
        Обработать квоты в 'combine_quotas' или 'price'.
        Отправить результат на вывод в 'PRINTER'.
        """
        html_tree = lxml.html.fromstring(html)
        outbound_list = AirBlueParser.parse_quotas(
            html_tree, self.departure, self.destination, self.dep_date, direction='1')

        if self.arr_date:
            inbound_list = AirBlueParser.parse_quotas(
                html_tree, self.destination, self.departure, self.arr_date, direction='2')
            quotas = AirBlueParser.combine_quotas(outbound_list, inbound_list)
            if quotas:
                self.printer.quotas(quotas, self.departure, self.destination,
                                    self.dep_date, self.arr_date)
            else:
                self.printer.info(outbound_list, self.departure, self.destination, self.dep_date)
                self.printer.info(inbound_list, self.destination, self.departure, self.arr_date)
        else:
            self.printer.info(outbound_list, self.departure, self.destination, self.dep_date)

    @staticmethod
    def parse_quotas(response, city_dep, city_dest, date, direction):
        """Парсинг данных.

        Выполнить парсинг данных.
        Проверить, что данные получены.
        Сохранить информацию в словаре 'quota' по ключам.
        Добавить все квоты в список.
        Вернуть список.
        """
        flights_info = response.xpath('/html/body/div[@id="content"]/div/form[2]'
                                      '/div[@id="trip_{0}"]/table[@id="trip_{0}_date_{1}_{2}_{3}"]'
                                      '/tbody[*]/tr'.format(direction,
                                                            date.strftime('%Y'),
                                                            date.strftime('%m'),
                                                            date.strftime('%d')))
        quotas = []
        if flights_info:
            currency = flights_info[0].xpath('//tr/td[6]/label/span/b/text()')[0]

            for trip in flights_info:
                flight = trip.xpath('./td[1]/text()')

                if 'not available' not in flight[0]:

                    flight = re.findall(r'[\S]+', trip.xpath('./td[1]/text()')[0])[0]
                    depart = trip.xpath('./td[2]/text()')[0]
                    route = trip.xpath('./td[3]/span[2]/text()')[0]
                    arrive = trip.xpath('./td[4]/text()')[0]
                    travel_time = AirBlueParser.travel_time(depart, arrive,
                                                            date, city_dep, city_dest)
                    price = {
                        'Standard (1 Bag)': trip.xpath(
                            './td[@class="family family-ES family-group-Y "]/label/span/text()'),
                        'Discount (No Bags)': trip.xpath(
                            './td[@class="family family-ED family-group-Y "]/label/span/text()'),
                    }

                    for key in price:
                        quota = {
                            'flight': flight,
                            'depart': depart,
                            'route': route,
                            'arrive': arrive,
                            'travel time': travel_time,
                        }
                        if price[key]:
                            quotas.append(AirBlueParser.cost(price[key], key, quota, currency))

        return quotas

    @staticmethod
    def timezone(city):
        """Определить часовой пояс"""

        time_zone = ''
        if city in ['DMM', 'JED', 'MED', 'RUH']:
            time_zone = 0
        if city in ['AUH', 'DXB', 'SHJ', 'MCT']:
            time_zone = 1
        if city in ['ISB', 'KHI', 'LHE', 'MUX', 'PEW', 'RYK', 'SKT', 'UET']:
            time_zone = 2
        return datetime.timedelta(hours=time_zone)

    @staticmethod
    def travel_time(time1, time2, date, city_dep, city_dest):
        """Выполнить расчет времени затраченного на перелет."""

        time_dep = datetime.datetime.strptime((date.strftime('%Y/%m/%d') + ' ' + time1),
                                              '%Y/%m/%d %I:%M %p')
        time_arr = datetime.datetime.strptime((date.strftime('%Y/%m/%d') + ' ' + time2),
                                              '%Y/%m/%d %I:%M %p')

        if time_arr < time_dep:
            time_arr = time_arr + datetime.timedelta(days=1)

        time_dep = time_dep - AirBlueParser.timezone(city_dep)
        time_arr = time_arr - AirBlueParser.timezone(city_dest)

        delta = time_arr - time_dep
        seconds = delta.total_seconds()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        total_time = (str(int(hours)) + ':' + str(int(minutes)))
        return total_time

    @staticmethod
    def cost(value, key, dictionary, currency):
        """Дополнить словарь quota ценной и классом обслуживания."""
        cost = float(re.sub(r'[,]', '', value[0]))
        price = '{}\n{} {}'.format(key, str(cost), currency)
        dictionary.update({
            'cost': cost,
            'class of service': key,
            'price': price,
            'currency': currency
        })
        return dictionary

    @staticmethod
    def combine_quotas(quotas_dep, quotas_ret):
        """Объеденить рейсы.

        Посчитать полную стоимость перелета в два конца.
        Объеденить класс обслуживания с ценой и валютой.
        Вернуть квоты.
        """
        quotas = []
        if quotas_dep and quotas_ret:

            for (dep, ret) in product(quotas_dep, quotas_ret):
                total_cost = str(dep['cost'] + ret['cost']) + ' ' + dep['currency']
                quotas.append([dep, ret, total_cost])

            quotas.sort(key=lambda i: i[2])
        return quotas


class PrintInfo:
    """

    Вывести итоговую информацию в stdout.

    __init__ - конструктор.
    info - вывод информации об одном рейсе.
    quotas - вывод информации о рейсах в оба конца.
    not_available - вывод информации об отсутствии рейса.
    not_carried -вывод информации об отсутствии перелетов.

    """

    def __init__(self):
        """Конструктор.

        Создать таблицу для отображения информации о перелетах.
        """
        self.table = PrettyTable()
        self.table.field_names = ['Flight(s)', 'Route', 'Depart', 'Arrive', 'Travel time',
                                  'Class of service']

    def info(self, quota, point_1, point_2, day):
        """Вывод информации об одном рейсе.

        Вывести в stdout пункты назначения.
        Вывести в stdout дату перелета.
        Добавить в таблицу информацию о рейсе.
        Вывести таблицу в stdout.
        """
        print('From {} ({})\nTo {} ({})'.format(
            CITIES[point_1], point_1,
            CITIES[point_2], point_2))
        print(day.strftime("%A %d. %B %Y"))

        if quota:
            for i in quota:
                self.table.add_row([i['flight'], i['route'], i['depart'], i['arrive'],
                                    i['travel time'], i['price']])

            print(self.table)
            self.table.clear_rows()
        else:
            self.not_available()

    @staticmethod
    def quotas(quotas, point_1, point_2, day_1, day_2):
        """Вывод информации о рейсах в оба конца.

        Вывести в stdout пункты назначения.
        Вывести в stdout даты перелета.
        Создать таблицу.
        Добавить в таблицу информацию о рейсах.
        Вывести таблицу в stdout.
        """

        print('From {} ({})'.format(CITIES[point_1], point_1).ljust(73),
              'From {} ({})'.format(CITIES[point_2], point_2).ljust(0))
        print('To {} ({})'.format(CITIES[point_2], point_2).ljust(73),
              'To {} ({})'.format(CITIES[point_1], point_1).ljust(0))

        print(day_1.strftime("%A %d. %B %Y").ljust(73),
              day_2.strftime("%A %d. %B %Y").ljust(0))

        table = PrettyTable()
        table.field_names = ['Flight(s)', 'Route', 'Depart', 'Arrive', 'Travel time',
                             'Class of service', 'Flight(s).', 'Route.', 'Depart.',
                             'Arrive.', 'Travel time.', 'Class of service.', 'Total cost']

        for quota in quotas:

            table.add_row([quota[0]['flight'], quota[0]['route'], quota[0]['depart'],
                           quota[0]['arrive'], quota[0]['travel time'], quota[0]['price'],
                           quota[1]['flight'], quota[1]['route'], quota[1]['depart'],
                           quota[1]['arrive'], quota[1]['travel time'], quota[1]['price'],
                           quota[2]])

        print(table)

    def not_available(self):
        """Вывети в stdout информацию об отсутствии рейса."""

        self.table.add_row(['', 'Flights are', 'available not', 'on the', 'dates selected!', ''])
        print(self.table)
        self.table.clear_rows()


if __name__ == '__main__':
    HELLO = Hello()
    PARSER = AirBlueParser(HELLO.departure, HELLO.destination, HELLO.dep_date, HELLO.arr_date)
    PARSER.get_req()