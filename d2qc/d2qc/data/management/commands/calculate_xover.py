# Import some test data to the database

from django.core.management.base import BaseCommand
from d2qc.data.glodap.glodap import Glodap
import d2qc.data.models as models
import os
import hashlib
from django.core.cache import cache
import json


class Command(BaseCommand):
    """
    This command is mainly used internally to calculate crossovers for a dataset
    in the background.
    """
    def add_arguments(self, parser):
        parser.add_argument('data_set_id', nargs='+', type=int)
        parser.add_argument('parameter_id', nargs='+', type=int)
        parser.add_argument('radius', nargs='+', type=int)
        parser.add_argument('min_depth', nargs='+', type=int)

    def handle(self, *args, **options):
        data_set_id = options['data_set_id'][0]
        parameter_id = options['parameter_id'][0]
        radius = options['radius'][0]
        min_depth = options['min_depth'][0]

        # Return cached value if exists
        cache_key = "calculate_xover-{}-{}-{}-{}".format(
            data_set_id,
            parameter_id,
            radius,
            min_depth,
        )
        cache_key = hashlib.md5(cache_key.encode('utf-8')).hexdigest()
        value = cache.get(cache_key, False)
        if value is not False:
            return value


        data_set = models.DataSet.objects.get(pk=data_set_id)
        data_set_stations = data_set.get_stations(
            parameter_id=parameter_id
        )
        data_sets = data_set.get_station_data_sets(
            data_set.get_crossover_stations(
                stations=data_set_stations,
                parameter_id=parameter_id,
                min_depth=min_depth,
            )
        )
        data = {
            'w_mean': [],
            'w_stdev': [],
            'expocode': [],
            'data_set_id': [],
            'date': [],
        }
        for ds in data_sets:
            crossover_stations = data_set.get_crossover_stations(
                stations=data_set_stations,
                parameter_id=parameter_id,
                crossover_data_set_id=ds[0],
                min_depth=min_depth,
            )
            crossed_data_set_stations = data_set.get_crossover_stations(
                data_set_id=ds[0],
                stations=crossover_stations,
                parameter_id=parameter_id,
                crossover_data_set_id=data_set_id,
                min_depth=min_depth,
            )
            stats = data_set.get_profiles_stats(
                crossed_data_set_stations,
                crossover_stations,
                parameter_id,
            )
            if stats['w_mean']:
                data['w_mean'].append(float(stats['w_mean']))
                data['w_stdev'].append(float(stats['w_stdev']))
                data['expocode'].append(stats['expocode'])
                data['data_set_id'].append(int(stats['data_set_id']))
                _date = models.DataSet.objects.get(pk=ds[0]).get_timespan(
                    stations=crossover_stations
                )[0]
                data['date'].append(_date.strftime("%Y-%m-%dT00:00:00.0Z"))

        mean = sum([ 0 if not s else m/pow(s, 2) for m, s in zip(data['w_mean'], data['w_stdev'])])
        mean = mean / sum([ 0 if not s else 1/pow(s, 2) for s in data['w_stdev']])
        stdev = sum([ 0 if not s else pow(s, -2) for s in data['w_stdev']])
        stdev = pow(1/stdev, 1/2)

        # Sort by date
        zipped = sorted(zip(
            data['date'],
            data['data_set_id'],
            data['expocode'],
            data['w_stdev'],
            data['w_mean']
        ))
        # and unzip
        (
            data['date'],
            data['data_set_id'],
            data['expocode'],
            data['w_stdev'],
            data['w_mean']
        ) = zip(*zipped)
        data['stdev'] = [stdev] * len(data['date'])
        data['mean'] = [mean] * len(data['date'])

        data = json.dumps(data)
        cache.set(cache_key, data)
        return data
