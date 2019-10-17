import re
import math
import numpy
import gsw
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
import os.path
from d2qc.data.models import DataSet
from d2qc.data.models import DataType
from d2qc.data.models import DataTypeName
from d2qc.data.models import Station
from d2qc.data.models import Cast
from d2qc.data.models import Depth
from d2qc.data.models import DataValue
from django.conf import settings
import glodap.util.excread as excread
from django.utils import timezone

class DataFile(models.Model):
    class Meta:
        db_table = 'd2qc_data_files'

    # Make sure files get unique filenames
    def file_store_path(self, filename):
        # clear filename of illegal characters
        filename = re.sub('[^a-zA-Z0-9\.\-\_]', '', filename)
        id = self.owner.id
        path = os.path.join(
                settings.DATA_FOLDER,
                'UID_{}'.format(id)
        )
        i = 0
        name = '{}__{}'.format(i, filename)
        while os.path.isfile(os.path.join(path, name)):
            i += 1
            name = '{}__{}'.format(i, filename)
        return os.path.join(path, name)

    id = models.AutoField(primary_key=True)
    filepath = models.FileField(
            upload_to=file_store_path,
            null=True
    )
    name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    headers = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
            User,
            on_delete = models.PROTECT,
            blank=True,
            null=True,
            editable=False
    )
    import_errors = models.TextField(blank=True)
    import_started = models.DateTimeField(null=True)
    import_finnished = models.DateTimeField(null=True)

    # Messages reported while importing data
    _messages = []

    def __str__(self):
        return self.name if self.name else self.filepath

    # Delete files as object is deleted
    def delete(self):
        # Dont delete file if file has related data set(s)
        if not DataSet.objects.filter(data_file_id=self.id).exists():
            self.filepath.delete()
        super().delete()

    def read_file(self):
        filearray = []
        if self.filepath:
            path = os.path.join(
                settings.BASE_DIR,
                str(self.filepath),
            )
            try:
                with open(path, encoding="utf-8") as excfile:
                    filearray = excfile.readlines()
            except:
                with open(path, encoding="iso-8859-1") as excfile:
                    filearray = excfile.readlines()
        return filearray

    def _write_messages(self, append = False, save = False):
        if append:
            self.import_errors += '\n'.join(self._messages)
        else:
            self.import_errors = '\n'.join(self._messages)
        if save:
            self.save()

    def import_data(self):
        """
        Import data from this data file. Abort if data existsself. Import errors
        are appended to the import_errors field.

        return True if data was imported, else return False
        """
        if self.import_started:
            self._messages = ["File data already beeing imported"]
            self._write_messages(append = True, save = True)
            return False

        self.import_started = timezone.now()
        self.save()

        datagrid = excread.excread(str(self.filepath))

        MANDATORY_VARS = (
            'EXPOCODE', 'EXC_DATETIME', 'EXC_CTDDEPTH', 'STNNBR', 'LATITUDE',
            'LONGITUDE',
        )

        # Variables not to be treated as data variables
        IGNORE = (
            'EXPOCODE', 'EXC_DATETIME', 'EXC_CTDDEPTH', 'STNNBR', 'SECT_ID', 'DATE',
            'TIME', 'LATITUDE', 'LONGITUDE', 'BTLNBR', 'BTLNBR_FLAG_W',
            'SAMPNO', 'CASTNO', 'CTDDEPTH', 'CTDDEP', 'HOUR', 'MINUTE', 'DEPTH',
            'HOUR','MINUTE',
        )

        QC_SUFFIX = '_FLAG_W'


        # Check all mandatory variables are there
        depth = ''
        stnnbr = ''
        castno = ''
        data_set = None
        station = None
        cast = None
        depth = None
        # Raise an exception if mandatory columns are missing
        if not all(key in datagrid.columns for key in MANDATORY_VARS):
            message = "Data file missing some mandatory column: {}".format(
                ', '.join(MANDATORY_VARS)
            )
            self._messages.append(message)
            self._write_messages()
            self.import_finnished = timezone.now()
            self.save()
            return False

        # Import data types
        missing_vars = []
        data_type_names = {
            str(type_):type_ for type_ in DataTypeName.objects.all()
        }
        for var in datagrid.columns:
            if var in IGNORE:
                continue
            if var.endswith(QC_SUFFIX):
                continue
            if var not in data_type_names:
                missing_vars.append(var)

        if missing_vars:
            message = """There where variables in the dataset that are not defined in
            the system. These cannot be handled. An administrator has to add
            the variables as data types for them to be treated. Unhandled
            variables in the data set: {}
            """.format(
                ', '.join(missing_vars)
            )
            self._messages.append(message)

        missing_depth_warning = False # Indicate missing depth already warned
        missing_position_warning = False

        # (Hopefully sensible) defaults for authoritative temp, salin, pressure
        temp_aut = DataTypeName.objects.filter(name="CTDTMP").first()
        salin_aut = DataTypeName.objects.filter(name="CTDSAL").first()
        press_aut = DataTypeName.objects.filter(name="CTDPRS").first()
        value_list = []
        line_no = 0
        for i, expo in enumerate(datagrid['EXPOCODE']):
            line_no += 1
            if not data_set or expo != data_set.expocode:
                # Add new dataset
                data_set = DataSet(
                    expocode=expo,
                    is_reference = False,
                    data_file = self,
                    owner = self.owner,
                    temp_aut = temp_aut,
                    salin_aut = salin_aut,
                    press_aut = press_aut,
                )
                if DataSet.objects.filter(
                            expocode=expo,
                            owner=self.owner
                ).exists():
                    # TODO Support files with multiple datasets, where one or
                    # more might already exist in database, but not all.
                    message = 'Dataset {} already exists for this user'. format(
                        expo
                    )
                    self._messages = [message]
                    self._write_messages()
                    self.import_finnished = timezone.now()
                    self.save()
                    return False

                data_set.save()
                station = None
                cast = None
                depth = None
            if not station or datagrid['STNNBR'][i] != station.station_number:
                longitude = datagrid['LONGITUDE'][i]
                latitude = datagrid['LATITUDE'][i]
                if math.isnan(longitude) or math.isnan(latitude):
                    if missing_position_warning:
                        continue
                    # Warning and dont insert if depth is NaN
                    message = """Latitude or longitude is nan on line {}.
                    Station will not be added when position is missing.
                    Subsequent missing position errors are supressed for this
                    file.
                    """.format(i)
                    self._messages.append(message)
                    missing_position_warning = True
                    continue
                # Add new station
                station = Station(
                        data_set = data_set,
                        position = Point(longitude, latitude),
                        station_number = int(datagrid['STNNBR'][i])
                )
                station.save()
                cast = None
                depth = None
            if (
                    not cast or
                    ('CASTNO' in datagrid and datagrid['CASTNO'][i] != cast.cast)
            ):
                # Add new cast
                cast_ = 1
                if 'CASTNO' in datagrid:
                    cast_ = int(datagrid['CASTNO'][i])
                cast = Cast(
                        station = station,
                        cast = cast_
                )
                cast.save()
                depth = None

            if (
                    not depth
                    or depth.depth != datagrid['EXC_CTDDEPTH'][i]
                    or (
                        'BTLNBR' in datagrid
                        and depth.bottle != datagrid['BTLNBR'][i]
                    )
            ):
                if math.isnan(datagrid['EXC_CTDDEPTH'][i]):
                    if missing_depth_warning:
                        continue
                    # Warning and dont insert if depth is NaN
                    message = """Depth is nan on line {}. Data will not be added when
                            depth is nan. Subsequent missing depth errors are
                            supressed for this file.
                            """.format(i)
                    self._messages.append(message)
                    missing_depth_warning = True
                    continue

                # Add new depth
                btlnbr = datagrid.get('BTLNBR', False)
                depth = Depth(
                        cast = cast,
                        depth = float(datagrid['EXC_CTDDEPTH'][i]),
                        bottle = 1 if btlnbr is False else btlnbr[i],
                        date_and_time = datagrid['EXC_DATETIME'][i],
                )
                try:
                    depth.save()
                except Exception as e:
                    m = "Line {}, Error {}".format(i, str(e), )
                    self._messages = [m]
                    self._write_messages(append=True,save=True)
                    raise e
            elif (
                    depth.depth == datagrid['EXC_CTDDEPTH'][i]
                    and datagrid['CASTNO'][i] == cast.cast
                    and datagrid['STNNBR'][i] == station.station_number
                    and expo == data_set.expocode
            ):
                # Implies duplicate line. Skip this line with a warning
                m = "Line {}, Error {}".format(i, "Duplicate, ignores line")
                self._messages = [m]
                self._write_messages(append=True,save=True)
                continue

            temp_val = salin_val = press_val = None
            for key in datagrid.columns:
                if key in IGNORE:
                    continue
                if not key in data_type_names:
                    # Variable not found in database. Already reported.
                    continue
                v = datagrid[key][i].item()
                # collect temp, press, salin values
                if key == temp_aut.name:
                    temp_val = v
                if key == salin_aut.name:
                    salin_val = v
                if key == press_aut.name:
                    press_val = v
                # Don't import missing values:
                if numpy.isnan(v) or v < -10:
                    continue
                qc_flag = None
                if (
                        key + QC_SUFFIX in datagrid
                        and not numpy.isnan(datagrid[key + QC_SUFFIX][i])
                ):
                    qc_flag = int(datagrid[key + QC_SUFFIX][i])
                value = DataValue(
                        depth = depth,
                        value = v,
                        qc_flag = qc_flag,
                        data_type_name = data_type_names[key]
                )
                value_list.append(value)

            # If all are set, we can calculate sigma4
            if not None in [temp_val, salin_val, press_val]:
                try:
                    sigma4 = gsw.density.sigma4(
                        gsw.conversions.SA_from_SP(
                            salin_val,
                            press_val,
                            longitude,
                            latitude,
                        ),
                        temp_val,
                    )
                    depth.sigma4 = sigma4
                    depth.save()
                except Exception as e:
                    m = "Line {}, Error {}".format(i, str(e), )
                    self._messages = [m]
                    self._write_messages(append=True,save=True)
                    raise e

            # Apply sql on every 500 line, so memory is not exhausted
            if line_no % 500 == 0 and value_list:
                DataValue.objects.bulk_create(value_list)
                value_list = []

        # Save data values
        if value_list:
            DataValue.objects.bulk_create(value_list)
        self._write_messages()
        self.import_finnished = timezone.now()
        self.save()
        return True
