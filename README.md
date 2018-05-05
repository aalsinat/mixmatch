### One trigger dispatcher
In order to manage all possible incoming barcode, we will use regular expression to decide which action will take place in every situation.
For example, in the case of Iberia vouchers, the following pattern will be used.

#### Iberia example
```
>>> import re
>>> voucher = re.compile('^(cvou:)?((0002\d{2})(\d{7}))(e)?')
>>> ticket = re.compile('^\d{13}$')
>>> result = voucher.match('cvou:0002001479045e')
>>> print(result.groups())
('cvou:', '0002001479045', '000200', '1479045', 'e')
>>> result2 = voucher.match('0002001479045')
>>> print(result2.groups())
(None, '0002001479045', '000200', '1479045', None)
>>> result3 = voucher.split('0002001479045')
>>> print(result3)
['', None, '0002001479045', '000200', '1479045', None, '']
>>> result4 = ticket.match('0755965622000')
>>> print(result4.groups())
('0755965622000',)
```
#### Hybris example
As for Hybris, this is the pattern that wil be used.
```
>>> pattern = re.compile(r'^(AREAS-TIP:)(\d{2})(-COD:)(\d{9})(-.+)?$')
```
