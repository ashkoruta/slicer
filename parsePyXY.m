function data = parsePyXY(filename)
f = fopen(filename,'r');
data = [];
while ~feof(f)
    fgetl(f); % ignore line about the path num
    tmp = fscanf(f,"%d lines\n");
    fgetl(f); % ignore initial coord
    sz = [4 tmp];
    p = fscanf(f,"%d/%d [%f,%f]\n",sz);
    data = [data;p'];
end
fclose(f);
end


