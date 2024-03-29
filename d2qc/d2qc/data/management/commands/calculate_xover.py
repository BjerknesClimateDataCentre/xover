from d2qc.data.management.newline_command import NewlineCommand
from d2qc.data.glodap.glodap import Glodap
import d2qc.data.models as models
import os
from django.core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)

class Command(NewlineCommand):
    help = """
        This command is mainly used internally to calculate crossovers for a dataset
        in the background.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            'data_set_id',
            nargs='+',
            type=int,
            help='Calculate for this data set',
        )
        parser.add_argument(
            'parameter_id',
            nargs='+',
            type=int,
            help='Calculate for this parameter',
        )
        parser.add_argument(
            'crossover_radius',
            nargs='+',
            type=int,
            help='Select stations within this radius, in meters',
        )
        parser.add_argument(
            'min_depth',
            nargs='+',
            type=int,
            help='Use this minimum depth for calculations',
        )
        parser.add_argument(
            'xtype',
            nargs = '+',
            type=str,
            help = 'Use this as independent variable. Either depth or sigma4',
        )
        parser.add_argument(
            '--only_qc_controlled_data',
            action='store_true',
            help = 'Only use quality controlled data',
        )
        parser.add_argument(
            '--minimum_num_stations',
            type=int,
            help='Only calculate if dataset has minimum_num_stations stations',
            default=0,
        )
        parser.add_argument(
            '-d',
            '--data_return',
            help='Return the data (normally data is simply cached)',
        )

    def handle(self, *args, **options):
        data_set_id = options['data_set_id'][0]
        parameter_id = options['parameter_id'][0]
        crossover_radius = options['crossover_radius'][0]
        min_depth = options['min_depth'][0]
        data_return = options['data_return']
        xtype = options['xtype'][0]
        only_qc_controlled_data = options['only_qc_controlled_data']
        minimum_num_stations = options['minimum_num_stations']


        # Return cached value if exists
        cache_key = "calculate_xover-{}-{}-{}-{}-{}-{}-{}".format(
            data_set_id,
            parameter_id,
            crossover_radius,
            min_depth,
            minimum_num_stations,
            xtype,
            only_qc_controlled_data,
        )
        value = cache.get(cache_key, False)
        if value is not False:
            return value


        try:
            
            data_set = models.DataSet.objects.get(pk=data_set_id)
            data_set_stations = data_set.get_stations(
                parameter_id = parameter_id,
                crossover_radius = crossover_radius,
                min_depth = min_depth,
            )
            data_sets = data_set.get_station_data_sets(
                data_set.get_crossover_stations(
                    stations = data_set_stations,
                    parameter_id = parameter_id,
                    min_depth = min_depth,
                    minimum_num_stations = 3,
                    crossover_radius = crossover_radius,
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
                # Get stations from this data set that falls within the crossover
                # radius of the original data set
                logging.info(f'Processing {data_sets.index(ds)} / {len(data_sets)}  Dataset: {ds[1]}')

                crossover_stations = data_set.get_crossover_stations(
                    stations = data_set_stations,
                    parameter_id = parameter_id,
                    crossover_data_set_id = ds[0],
                    min_depth = min_depth,
                    minimum_num_stations = minimum_num_stations,
                    crossover_radius = crossover_radius,
                )
                # Get stations from the original data set that match this data set
                crossed_data_set_stations = data_set.get_crossover_stations(
                    stations = crossover_stations,
                    parameter_id = parameter_id,
                    crossover_data_set_id = data_set_id,
                    min_depth = min_depth,
                    crossover_radius = crossover_radius,
                )
                if (
                        len(crossover_stations) == 0
                        or len(crossed_data_set_stations) == 0
                ):
                    continue
                stats = data_set.get_profiles_stats(
                    crossed_data_set_stations,
                    crossover_stations,
                    parameter_id,
                    min_depth = min_depth,
                    crossover_radius = crossover_radius,
                    xtype = xtype,
                    only_qc_controlled_data = only_qc_controlled_data,
                )
                if (
                        stats is not None
                        and 'w_mean' in stats
                        and stats['w_mean']
                        and 'w_stdev' in stats
                        and stats['w_stdev']
                ):
                    data['w_mean'].append(float(stats['w_mean']))
                    data['w_stdev'].append(float(stats['w_stdev']))
                    data['expocode'].append(stats['expocode'])
                    data['data_set_id'].append(int(stats['data_set_id']))
                    _date = models.DataSet.objects.get(pk=ds[0]).get_timespan(
                        stations=crossover_stations
                    )[0]
                    data['date'].append(_date.strftime("%Y-%m-%dT00:00:00.0Z"))

            logging.debug('calculating statistics')

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
            _date = models.DataSet.objects.get(pk=data_set_id).get_timespan(
                stations=data_set_stations
            )[0]
            data['eval_dataset_date'] = _date.strftime("%Y-%m-%dT00:00:00.0Z")

            data = json.dumps(data)
            cache.set(cache_key, data)
            logging.debug('finished with calculations, building plot...')

        except Exception as e:
            cache.set(cache_key,f'calculation failed, {e}')


        if data_return:
            return data
