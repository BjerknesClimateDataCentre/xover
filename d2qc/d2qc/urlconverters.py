class DataTypeConverter:
    regex = '[a-zA-Z0-9\_\-,]+'

    def to_python(self, value):
        return value.split(",")

    def to_url(self, value):
        return ','.join(value)


class NumberListConverter:
    regex = '[0-9,\.]+'

    def to_python(self, value):
        return [int(i) for i in value.split(",")]

    def to_url(self, value):
        return ','.join(str(v) for v in value)

class LatLonBoundsConverter:
    regex = '[0-9\.]+,[0-9\.]+,[0-9\.]+,[0-9\.]+'

    def to_python(self, value):
        return [int(i) for i in value.split(",")]

    def to_url(self, value):
        return ','.join(str(v) for v in value)
