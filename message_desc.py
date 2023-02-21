messages = {
    "compass": {
        "desc": "Репитер КФ1",
        "fields": (
            ('id', 'индефикатор', ['HCHDT']),
            ('heading', 'курс, град.', (0.0, 359.9)),
            ('power', 'питание', ['T', 'N'])
        )
    },
    "sonar": {
        "desc": "Репитер НЭЛ",
        "fields": (
            ('id', 'индефикатор', ['SDDBT']),
            ('depth', 'глубина, М', (0.0, 9999.9)),
            ('danger', 'Оп. глубина, М', (0, 99)),
            ('accuracy', 'Исправность', ('V', 'A'))
        )},
    "sensor": {
        "desc": "Датчик HMR",
        "fields": (
            ('roll', 'крен', [-90.0, 90.0]),
            ('pitch', 'дифф.', [-90.0, 90.0]),
            ('heading', 'курс', [0.0, 359.9]),
            ('magc', 'C', [-75.0, 75.0]),
            ('magb', 'B', [-75.0, 75.0]),
            ('magz', 'Z', [-75.0, 75.0])
        )
    }
}
