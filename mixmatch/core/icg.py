from logging import getLogger
from os import path, remove
from xml.etree import ElementTree

from pypyodbc import connect


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
            self.logger.error("Connection error: %s", e.message)

    def get_mix_and_match(self):
        if self.root is not None:
            return int(self.root.find('aplicarmm').text)
        else:
            return

    def set_mix_and_match(self):
        icg_file = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.filename'))
        mix_and_match = self.root.find('aplicarmm')
        mix_and_match.text = self.properties.get('manager.promotion.id')
        self.element_tree.write(path.abspath(icg_file))

    def set_mix_and_match_value(self, value):
        icg_file = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.filename'))
        mix_and_match = self.root.find('aplicarmm')
        mix_and_match.text = value
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

    def update_db_promotion(self, new_value):
        select_sql = r'SELECT VALOR FROM ACCIONESPROMOCION WHERE IDPROMOCION = ?'
        connection = self.connect()
        cursor = connection.cursor()
        cursor.execute(select_sql, [self.properties.get('manager.promotion.id')])
        results = cursor.fetchone()
        self.logger.info('Original results %s', results)
        values = results[0].split('|')
        self.logger.info('Results from executed query: %s', values)
        self.logger.info('New value %s', new_value)
        values[0] = '%10.18f' % new_value
        values[0] = values[0].replace('.', ',')
        promotion = '|'.join(str(value) for value in values)
        self.logger.info('New value to be updated %s', promotion)
        update_sql = 'UPDATE ACCIONESPROMOCION SET VALOR = ? WHERE IDPROMOCION = ?'
        cursor.execute(update_sql, [promotion, self.properties.get('manager.promotion.id')])
        connection.commit()

    def save_coupon(self, coupon):
        coupon_filename = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.validation'))
        coupon_file = open(path.abspath(coupon_filename), 'w+')
        self.logger.info('Save coupon %s', coupon)
        coupon_file.write(str(coupon))

    def cancel_coupon(self):
        coupon_filename = path.join(self.properties.get('exchange.path'), self.properties.get('exchange.validation'))
        if path.isfile(path.abspath(coupon_filename)):
            self.logger.info('Cancelling coupon %s', path.abspath(coupon_filename))
            remove(path.abspath(coupon_filename))
