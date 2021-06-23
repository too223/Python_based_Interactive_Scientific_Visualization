from bokeh.core.enums import SizingMode
import numpy as np
import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row, gridplot
from bokeh.models import ColumnDataSource, Div, Select, Slider, TextInput, BoxSelectTool, LassoSelectTool, Tabs, Panel, LinearColorMapper, ColorBar, BasicTicker, PrintfTickFormatter
from bokeh.plotting import figure, curdoc
from bokeh.palettes import inferno, magma, viridis, gray, cividis, turbo
from bokeh.models.callbacks import CustomJS


# Import dataset
df_catalysis_dataset = pd.read_csv("data/OCM-data.csv", index_col=0, header=0)

# Removing the Blank names from the data
df_catalysis_dataset.set_index(df_catalysis_dataset.index)
df_catalysis_dataset.drop("Blank",axis=0)

# Calculating error percentage 

#Sum of columns to compare with CH4_conv
df_catalysis_dataset["Sum_y"]= df_catalysis_dataset.loc[:,"C2H6y":"CO2y"].sum(axis=1) 
df_catalysis_dataset["error_ch4_conv"]=abs((df_catalysis_dataset["Sum_y"]-df_catalysis_dataset["CH4_conv"])/
                                            df_catalysis_dataset["CH4_conv"])*100

# Determine key values for Select Tool. More details in the Notebook.

unique_temp = (df_catalysis_dataset['Temp']
               .sort_values()
               .astype(str)
               .unique()
               )
sorted_unique_temp = dict(zip(unique_temp, unique_temp))

unique_ch4_to_o2 = (df_catalysis_dataset['CH4/O2']
                    .sort_values()
                    .astype(str)
                    .unique()
                    )
sorted_unique_ch4_to_o2 = dict(zip(unique_ch4_to_o2, unique_ch4_to_o2))

axis_map_x = {
    "Argon Flow": "Ar_flow",
    "Methane Flow": "CH4_flow",
    "Oxygen Flow": "O2_flow",
    "Amount of Catalyst": "CT",
    "M2_mol": "M2_mol",
    "M3_mol": "M3_mol",
}

axis_map_y = {
    "Ethane_y": "C2H6y",
    "Ethylene_y": "C2H4y",
    "CarbonDiOxide_y": "CO2y",
    "CarbonMonoOxide_y": "COy",
    "DiCarbon_s": "C2s",
    "Ethane_s": "C2H6s",
    "Ethylene_s": "C2H4s",
    "CarbonDiOxide_s": "CO2s",
    "CarbonMonoOxide_s": "COs",
}

# Create Input controls
slider_methane_conversion = Slider(
    title="Minimum Methane conversion value", value=20, start=1, end=46, step=1)
slider_C2y = Slider(title="Minimum value of C2y",
                    start=0.06, end=21.03, value=4.0, step=0.1)
slider_temp = Slider(title="Minimum value of Temperature",
                     start=700.0, end=900.0, value=800.0, step=50.0)
slider_error = Slider(title="Maximum Error Permitted", 
                      start=0.0, end=100.0, step=0.5, value=37.0)
select_ch4_to_o2 = Select(title="CH4 to O2", options=sorted(
    sorted_unique_ch4_to_o2.keys()), value="6")
select_x_axis = Select(title="X Axis", options=sorted(
    axis_map_x.keys()), value="Argon Flow")
select_y_axis = Select(title="Y Axis", options=sorted(
    axis_map_y.keys()), value="CarbonDiOxide_y")

TOOLTIPS = [
    ("M1", "@M1"),
    ("M2", "@M2"),
    ("M3", "@M3"),
    ("Catalyst/Support", "@Name")
]

# tools in the toolbar
TOOLS = "pan,wheel_zoom,box_select,lasso_select,reset"

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(
    data=dict(x=[], y=[], M1=[], M2=[], M3=[], Name=[]))

p = figure(height=600, width=700, title="", tools=TOOLS,
           toolbar_location="above", tooltips=TOOLTIPS)
p.select(BoxSelectTool).select_every_mousemove = False
p.select(LassoSelectTool).select_every_mousemove = False
r = p.circle(x="x", y="y", source=source, size=7,
             color='mediumblue', line_color=None, fill_alpha=0.6)
# r = p.scatter(x = "x",y="y",alpha=0.3)


def select_data():
    temp_val = slider_temp.value
    select_ch4_to_o2_val = select_ch4_to_o2.value
    selected = df_catalysis_dataset[
        (df_catalysis_dataset.CH4_conv >= slider_methane_conversion.value) &
        (df_catalysis_dataset.C2y >= slider_C2y.value) &
        (df_catalysis_dataset.Temp >= float(slider_temp.value)) &
        (df_catalysis_dataset.error_ch4_conv <= float(slider_error.value)) &
        (df_catalysis_dataset['CH4/O2'] == float(select_ch4_to_o2.value))
    ]
    return selected


# Repositioned the todo so that the select_data() function could be used by methods
# the horizontal histogram
hhist, hedges = np.histogram(
    select_data()[axis_map_x[select_x_axis.value]], bins=10)
hzeros = np.zeros(len(hedges)-1)

LINE_ARGS = dict(color="#3A5785", line_color=None)

ph = figure(toolbar_location=None, width=p.width, height=100, x_range=p.x_range, y_range=(
    0, (max(hhist)*1.1)), min_border=10, min_border_left=50, y_axis_location="right")
ph.xgrid.grid_line_color = None
ph.yaxis.major_label_orientation = np.pi/4
ph.background_fill_color = "#fafafa"

# histogram to reflect the data points
hh = ph.quad(bottom=0, left=hedges[:-1], right=hedges[1:],
             top=hhist, color="white", line_color="#3A5785")
# histograms highlight on top of the original histogram
hh1 = ph.quad(
    bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, alpha=0.5, **LINE_ARGS)
hh2 = ph.quad(
    bottom=0, left=hedges[:-1], right=hedges[1:], top=hzeros, alpha=0.1, **LINE_ARGS)

# the vertical histogram
vhist, vedges = np.histogram(
    select_data()[axis_map_y[select_y_axis.value]], bins=10)
vzeros = np.zeros(len(vedges)-1)

pv = figure(toolbar_location=None, width=100, height=p.height, x_range=(
    0, (max(vhist)*1.1)), y_range=p.y_range, min_border=10, y_axis_location="right")
pv.ygrid.grid_line_color = None
pv.xaxis.major_label_orientation = np.pi/4
pv.background_fill_color = "#fafafa"

# histogram to reflect the data points
vv = pv.quad(left=0, bottom=vedges[:-1], top=vedges[1:],
             right=vhist, color="white", line_color="#3A5785")
# histograms highlight on top of the original histogram
vh1 = pv.quad(
    left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.5, **LINE_ARGS)
vh2 = pv.quad(
    left=0, bottom=vedges[:-1], top=vedges[1:], right=vzeros, alpha=0.1, **LINE_ARGS)

layout = gridplot([[p, pv], [ph, None]], merge_tools=False)


# Brought in update for the histogram selections attempt
def update():
    df = select_data()
    x_name = axis_map_x[select_x_axis.value]
    y_name = axis_map_y[select_y_axis.value]

    p.xaxis.axis_label = select_x_axis.value
    p.yaxis.axis_label = select_y_axis.value
    p.title.text = 'Data Exploration'
    source.data = dict(
        x=df[x_name],
        y=df[y_name],
        M1=df['M1'],
        M2=df['M2'],
        M3=df['M3'],
        Name=df.index
    )

    # also update both histograms
    global hhist, hedges, vhist, vedges
    if len(df) == 0:
        hhist, hedges = hzeros, hzeros
        vedges, vhist = vzeros, vzeros
        hh.data_source.data["top"] = hzeros
        vv.data_source.data["right"] = vzeros
    else:
        hhist, hedges = np.histogram(
            df[axis_map_x[select_x_axis.value]], bins=10)
        vhist, vedges = np.histogram(
            df[axis_map_y[select_y_axis.value]], bins=10)
        ph.y_range.end = max(hhist)*1.1
        pv.x_range.end = max(vhist)*1.1
        hh.data_source.data["top"] = hhist
        hh.data_source.data["right"] = hedges[1:]
        hh1.data_source.data["right"] = hedges[1:]
        # hh2.data_source.data["right"] = hedges[1:]
        hh.data_source.data["left"] = hedges[:-1]
        hh1.data_source.data["left"] = hedges[:-1]
        # hh2.data_source.data["left"] = hedges[:-1]
        vv.data_source.data["right"] = vhist
        vv.data_source.data["bottom"] = vedges[:-1]
        vh1.data_source.data["bottom"] = vedges[:-1]
        # vh2.data_source.data["bottom"] = vedges[:-1]
        vv.data_source.data["top"] = vedges[1:]
        vh1.data_source.data["top"] = vedges[1:]
        # vh2.data_source.data["top"] = vedges[1:]


controls = [slider_methane_conversion, slider_C2y, slider_temp,
            slider_error,select_ch4_to_o2, select_x_axis, select_y_axis]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = column(*controls, width=320)


def update_histogram(attr, old, new):
    inds = new
    if len(inds) == 0 or len(inds) == len(select_data()[axis_map_x[select_x_axis.value]]):
        hhist1, hhist2 = hzeros, hzeros
        vhist1, vhist2 = vzeros, vzeros
    else:
        neg_inds = np.ones_like(
            select_data()[axis_map_x[select_x_axis.value]], dtype=np.bool)
        neg_inds[inds] = False
        hhist1, _ = np.histogram(
            select_data()[axis_map_x[select_x_axis.value]][inds], bins=hedges)
        vhist1, _ = np.histogram(
            select_data()[axis_map_y[select_y_axis.value]][inds], bins=vedges)
        # hhist2, _ = np.histogram(
        #     select_data()[axis_map_x[select_x_axis.value]][neg_inds], bins=hedges)
        # vhist2, _ = np.histogram(
        #     select_data()[axis_map_y[select_y_axis.value]][neg_inds], bins=vedges)

    hh1.data_source.data["top"] = hhist1
    # hh2.data_source.data["top"] = -hhist2
    vh1.data_source.data["right"] = vhist1
    # vh2.data_source.data["right"] = -vhist2


l = column([row(inputs, layout)], sizing_mode="scale_both")

## Adding the correlation matrix
# Copy x-axis values into new df
df_corr = df_catalysis_dataset[
    ["CT","Ar_flow","CH4_flow","O2_flow","Total_flow","Support_ID",
    "M2_mol","M3_mol","M1_atom_number","M2_atom_number","M3_atom_number",
    "M1_mol_percentage","M2_mol_percentage","M3_mol_percentage"]
    ]
corr_matrix = df_corr.corr()

## AXIS LABELS FOR PLOT
df = pd.DataFrame(corr_matrix)
df = df.set_index(df.columns).rename_axis('parameters', axis=1)
df.index.name = 'level_0'
common_axes_val = list(df.index)
df = pd.DataFrame(df.stack(), columns=['correlation']).reset_index()
source_corr = ColumnDataSource(df)

## FINDING LOWEST AND HIGHEST OF CORRELATION VALUES
low_df_corr_min = df.correlation.min()
high_df_corr_min = df.correlation.max()
no_of_colors = 7

### PLOT PARTICULARS
## CHOOSING DEFAULT COLORS
COLOR_SCHEME = {
    'Cividis':cividis(no_of_colors),
    'Gray':gray(no_of_colors),
    'Inferno':inferno(no_of_colors),
    'Magma':magma(no_of_colors),
    'Viridis':viridis(no_of_colors),
    'Turbo':turbo(no_of_colors),
}

select_color = Select(title='Color Palette',value='Magma', options=list(COLOR_SCHEME.keys()), width=200, height=50)

mapper = LinearColorMapper(palette= magma(no_of_colors), low=low_df_corr_min, high=high_df_corr_min)

## SETTING UP THE PLOT
c = figure(title="Correlation Matrix",x_range=common_axes_val, y_range=list((common_axes_val)),x_axis_location="below",toolbar_location=None,
            plot_width=700, plot_height=600, tooltips=[('Parameters', '@level_0 - @parameters'), ('Correlation', '@correlation')])


## SETTING UP PLOT PROPERTIES
c.grid.grid_line_color = None
c.axis.axis_line_color = None
c.axis.major_tick_line_color = None
c.axis.major_label_text_font_size = "10pt"
c.xaxis.major_label_orientation = np.pi/2

## SETTING UP HEATMAP RECTANGLES
cir = c.rect(x="level_0", y="parameters", width=1, height=1,source=source_corr,fill_color={'field': 'correlation', 'transform': mapper},line_color=None)

## SETTING UP COLOR BAR
color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="5pt",ticker=BasicTicker(desired_num_ticks=10),formatter=PrintfTickFormatter(format="%.1f"),label_standoff=6, border_line_color=None, location=(0, 0))
c.add_layout(color_bar, 'right')

#organizing panels of diaply
tab1=Panel(child = l, title="Data Exploration")
tab2 = Panel(child=column(select_color,c),title = "Correlation Matrix")
tabs=Tabs(tabs=[tab1,tab2])

update()  # initial load of the data
curdoc().add_root(tabs)
curdoc().title = "Catalysis Data"
r.data_source.selected.on_change('indices', update_histogram)
