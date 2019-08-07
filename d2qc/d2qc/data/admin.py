from django.contrib import admin
from d2qc.data.models import *
from django.contrib import admin

###########################################################
# extend classes below to modify django /admin behaviour  #
###########################################################

@admin.register(DataSet)
class DataSetAdmin(admin.ModelAdmin):
    pass

@admin.register(OffsetType)
class OffsetTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(DataType)
class DataTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(DataValue)
class DataValueAdmin(admin.ModelAdmin):
    pass

@admin.register(DataUnit)
class DataUnitAdmin(admin.ModelAdmin):
    pass

@admin.register(Depth)
class DepthAdmin(admin.ModelAdmin):
    pass

@admin.register(Cast)
class CastAdmin(admin.ModelAdmin):
    pass

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    pass

@admin.register(DataFile)
class DataFileAdmin(admin.ModelAdmin):
    pass
