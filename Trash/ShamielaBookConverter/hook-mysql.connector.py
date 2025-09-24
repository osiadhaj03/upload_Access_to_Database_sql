"""
PyInstaller hook لمكتبة mysql.connector
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# جمع جميع الوحدات الفرعية
hiddenimports = collect_submodules('mysql.connector')

# إضافة وحدات مخفية إضافية
hiddenimports += [
    'mysql.connector.locales.eng.client_error',
    'mysql.connector.constants',
    'mysql.connector.conversion', 
    'mysql.connector.cursor',
    'mysql.connector.errors',
    'mysql.connector.network',
    'mysql.connector.protocol',
    'mysql.connector.utils',
    'mysql.connector.abstracts',
    'mysql.connector.pooling',
    'mysql.connector.authentication',
    'mysql.connector.charsets',
    'mysql.connector.custom_types',
    'mysql.connector.dbapi',
    'mysql.connector.fabric',
    'mysql.connector.optionfiles',
]

# جمع جميع البيانات
datas, binaries, hiddenimports_collected = collect_all('mysql.connector')
hiddenimports += hiddenimports_collected
