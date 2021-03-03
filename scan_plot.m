close all
%%
base = "combined_xy";
%base = "fullplate_split";
for i = 1:4
    fname = base + sprintf("/layer%d.xy",i);
    fprintf(fname + "\n");
    fid = fopen(fname,'r');
    LayerXY = readXY(fid);
    for j = 1:length(LayerXY)
        data = LayerXY{j}{:,:};
        data = [0,0,0,0;data]; % add initial point
        for k = 2:size(data,1)
            if data(k,1) > 0
                c = 'r';
            else 
                c = 'b';
            end
            plot([data(k-1,3),data(k,3)],[data(k-1,4),data(k,4)],c);
            axis square
            xlim([-25 25])
            ylim([-25 25])
            pause(0.01)
            hold on
        end
    end
    hold off
    fclose(fid);
end