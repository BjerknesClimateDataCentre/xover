--------------------------------------------------------------------------------
-- Initial update of existing data
-- Run this sql after inserting data
--------------------------------------------------------------------------------
delete from d2qc_data_sets_data_types;

insert into d2qc_data_sets_data_types (dataset_id, datatype_id)
select distinct ds.id as data_set_id,
dv.data_type_id from d2qc_data_sets ds
inner join d2qc_stations s on (ds.id=s.data_set_id)
inner join d2qc_casts c on (s.id=c.station_id)
inner join d2qc_depths d on (c.id=d.cast_id)
inner join d2qc_data_values dv on (d.id=dv.depth_id);
