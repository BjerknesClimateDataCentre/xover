%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% m-file for use in matlab.
% exports refdata from mat-file in 2QC toolbox
% Creates a folder named output, with folder named after cruise expo-codes
% in the reference-data for the 2QC toolbox
% Path to the reference-data is hardcoded in this script, so it needs to
% run from the 2QC - toolbox folder
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Path to reference data mat file
load reference_data/2ndQC_ReferenceData.mat


[len, cols] = size(ref_data);

out = 'output'

for i = 1:size(ref_expocodes)
    expo = ref_expocodes(i);
    expo = expo{1};

    % Some pure number-expocodes have been translated to scientific
    % notation by matlab at some point. Fix this:
    if ~isnan(str2double(ref_expocodes(i)))
        expo = sprintf('%12.0f', str2double(ref_expocodes(i)));
    end

    dir = strcat(out, '/', expo);
    file = strcat(dir, '/', expo, '.exc.csv')
    file_exists = exist(file, 'file');
    dir_exists = exist(dir, 'dir');
    if ~dir_exists
        mkdir(dir);
    end

    % Open file in append mode, and write headers if the file did not
    % exists from before.
    fid = fopen(file, 'a+');
    if ~file_exists
        fprintf(fid, '# REFDATA\n');
        fprintf(fid, '# This data is reference data for 2QC\n');
        fprintf(fid, strcat(strjoin(ref_vars, ','), '\n\n'));
    end

    % Get the right data slice from the huge ref_data matrix
    data = ref_data(find(ref_data(:,1) == i), :);
    [len, cols] = size(data);
    for j = 1:len
        % Print each line as commaseparated values
        line = sprintf('%d,', data(j, :));
        fprintf(fid, strcat(line(1:end-1), '\n'));
    end
    fclose(fid);
end

