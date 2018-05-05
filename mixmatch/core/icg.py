from datetime import datetime, timedelta
from json import dumps
from logging import getLogger
from os import path, remove
from xml.etree import ElementTree

from pypyodbc import connect

from mixmatch.core.exceptions import DatabaseConnectionException


class ICGExtend(object):
    def __init__(self, constructor=()):
        self.logger = getLogger(self.__class__.__module__)
        self.values = list(constructor)
        self.properties = dict(self.values)
        self.__read_file__()

    def __read_file__(self):
        icg_file = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.filename'))
        if path.isfile(icg_file):
            self.element_tree = ElementTree.parse(path.abspath(icg_file))
            self.root = self.element_tree.getroot()
        else:
            raise Exception('ICG Exchange file %s does not exist' % icg_file)

    def get_barcode(self):
        if self.root is not None:
            return self.root.find('identificador').text
        else:
            return

    def get_promotion(self):
        if self.root is not None:
            return int(self.root.find('idpromocion').text)
        else:
            return

    def connect(self):
        try:
            connection_string = 'Driver={SQL Server};Server=%s;port=1433;Database=%s;uid=%s;pwd=%s' % (
                self.properties.get('manager.srv'), self.properties.get('manager.db'),
                self.properties.get('manager.db.uid'), self.properties.get('manager.db.pwd'))
            self.logger.info('Connection string: %s', connection_string)
            return connect(connection_string)
        except Exception as e:
            raise DatabaseConnectionException('Error connecting to %s', connection_string)

    def get_mix_and_match(self):
        if self.root is not None:
            return int(self.root.find('aplicarmm').text)
        else:
            return

    def set_mix_and_match(self, promotion_id=None):
        icg_file = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.filename'))
        mix_and_match = self.root.find('aplicarmm')
        mix_and_match.text = self.properties.get('manager.promotion.id') if promotion_id is None else promotion_id
        self.element_tree.write(path.abspath(icg_file))

    def cancel_mix_and_match(self):
        icg_file = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.filename'))
        mix_and_match = self.root.find('aplicarmm')
        mix_and_match.text = '0'
        self.element_tree.write(path.abspath(icg_file))

    def set_mix_and_match_status(self, message):
        icg_file = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.filename'))
        mix_and_match = self.root.find('estadomm')
        mix_and_match.text = message
        self.element_tree.write(path.abspath(icg_file))

    def update_db_promotion(self, new_value, promotion_id=None):
        select_sql = r'SELECT VALOR FROM ACCIONESPROMOCION WHERE IDPROMOCION = ?'
        connection = self.connect()
        cursor = connection.cursor()
        promotion = self.properties.get('manager.promotion.id') if promotion_id is None else promotion_id
        cursor.execute(select_sql, [promotion])
        results = cursor.fetchone()
        self.logger.debug('Original results %s', results)
        values = results[0].split('|')
        self.logger.debug('Results from executed query: %s', values)
        self.logger.debug('New value %s', new_value)
        values[0] = '%10.18f' % new_value
        values[0] = values[0].replace('.', ',')
        promotion = '|'.join(str(value) for value in values)
        self.logger.info('New value to be updated %s', promotion)
        update_sql = 'UPDATE ACCIONESPROMOCION SET VALOR = ? WHERE IDPROMOCION = ?'
        cursor.execute(update_sql, [promotion, self.properties.get('manager.promotion.id')])
        connection.commit()

    def activate_mix_and_match(self, promotions: list):
        """
        Updates validity dates of the promotion so that it can be applied.
        :param promotions: List of promotions to be activated
        """
        self.logger.debug('Activating M&M with code %s', promotions)
        connection = self.connect()
        cursor = connection.cursor()
        start_date = datetime.now()
        end_date = start_date + timedelta(days=1)
        update_sql = r'UPDATE PROMOCIONES SET FECHAINICIAL = ?, FECHAFINAL = ? WHERE IDPROMOCION = ?'
        self.logger.debug('SQL sentence to be executed: %s', update_sql)
        self.logger.debug('Promotions: %s', promotions)
        self.logger.debug('Start date: %s', start_date.strftime('%Y-%m-%d'))
        self.logger.debug('End date: %s', end_date.strftime('%Y-%m-%d'))
        for promo in promotions:
            cursor.execute(update_sql, [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), promo])
            connection.commit()

    def save_coupon(self, promotion, coupon):
        coupon_filename = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.validation'))
        coupon_file = open(path.abspath(coupon_filename), 'w+')
        self.logger.debug('Saving %s coupon %s ', promotion, coupon)
        coupon_info = dumps(dict(promotion=promotion, coupon=coupon), default=lambda c: c.__dict__)
        coupon_file.write(str(coupon_info))

    def cancel_coupon(self):
        coupon_filename = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.validation'))
        if path.isfile(path.abspath(coupon_filename)):
            self.logger.info('Cancelling coupon %s', path.abspath(coupon_filename))
            remove(path.abspath(coupon_filename))
