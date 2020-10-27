close all
%%
LayerXY = cell(1,175);
base = "combined_xy";
%base = "ilc_new_sw_split";
for i = 1:5
    fname = base + sprintf("/layer%d.xy",i);
    fprintf(fname + "\n");
    data = parsePyXY(fname);
    LayerXY{i} = data;
    %continue;
    data = [0,0,0,0;data]; % add initial point
    for j = 2:size(data,1)
        if data(j,1) > 0
            c = 'r';
        else 
            c = 'b';
        end
        plot([data(j-1,3),data(j,3)],[data(j-1,4),data(j,4)],c);
        axis square
        pause(0.01)
        hold on
    end
    hold off
end