class DataTypeConverter:
    regex = '[a-zA-Z0-9\_\-,]+'

    def to_python(self, value):
        return value.split(",")

    def to_url(self, value):
        return ','.join(value)
