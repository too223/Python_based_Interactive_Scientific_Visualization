#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 09:12:58 2020

@author: annamoragne
"""

import networkx as nx
import numpy as np
from bokeh.io import  show, output_file, curdoc
from bokeh.models import (BoxSelectTool, Circle, EdgesAndLinkedNodes, HoverTool,
                         MultiLine, NodesAndLinkedEdges, Plot, Range1d, TapTool, ResetTool)
from bokeh.models import ColumnDataSource, GraphRenderer, Arrow, OpenHead, Slider, Button
from bokeh.palettes import Spectral4, RdYlBu8
from bokeh.models.graphs import from_networkx
from bokeh.transform import transform
from bokeh.models.transforms import CustomJSTransform
from bokeh.models.annotations import LabelSet
from bokeh.plotting import figure
from scipy.integrate import odeint, solve_ivp
from bokeh.layouts import row, column


class_names=['Susceptible', 'Exposed', 'Unknown Asymptomatic Infected', 'Known Asymptomatic Infected', 'Non-Hospitalized Symptomatic Infected', 'Hospitalized Symptomatic Infected', 'Recovered', 'Dead']
needed_edges=[(0, 1), (0, 7), (0, 6), (1, 2), (1,4), (2, 3), (2,6), (2,7), (3, 6), (3,7), (4,5), (4,6), (4,7), (5,6), (5,7), (6,7), (6,0)]
practice_sizes=[5, 10, 15, 20, 25, 30, 35, 40]

G=nx.DiGraph()
G.add_nodes_from(range(8), name=class_names)
G.add_edges_from(needed_edges)

plot = Plot(plot_width=800, plot_height=800,
            x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
plot.title.text = "Class Populations for Infectious Disease Outbreak"

graph_renderer = from_networkx(G, nx.circular_layout, scale=1, center=(0,0))

graph_renderer.node_renderer.data_source.add(RdYlBu8, 'color')
graph_renderer.node_renderer.data_source.add(practice_sizes, 'size')
graph_renderer.node_renderer.glyph = Circle(size='size', fill_color='color')
graph_renderer.node_renderer.data_source.data['name'] =['Susceptible', 'Exposed', 'Unknown Asymptomatic Infected', 'Known Asymptomatic Infected', 'Non-Hospitalized Symptomatic Infected', 'Hospitalized Symptomatic Infected', 'Recovered', 'Dead']
graph_renderer.node_renderer.selection_glyph = Circle(size=30, fill_color=Spectral4[2])
graph_renderer.node_renderer.hover_glyph = Circle(size=30, fill_color=Spectral4[1])
graph_renderer.node_renderer.data_source

graph_renderer.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=0.8, line_width=4)
graph_renderer.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2], line_width=4)
graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1], line_width=6)

graph_renderer.selection_policy = NodesAndLinkedEdges()
graph_renderer.inspection_policy = EdgesAndLinkedNodes()

#trying to add arrows to directed graph
pos = nx.layout.spring_layout(G)
what=nx.draw_networkx_edges(G, pos=pos, edge_color='black', alpha=0.5, arrows=True, arrowstyle='->',rrowsize=10, width=2)
#plot.add_layout(what)
# add the labels to the node renderer data source
source = graph_renderer.node_renderer.data_source
source.data['names'] = class_names

# create a transform that can extract the actual x,y positions
code = """
    var result = new Float64Array(xs.length)
    for (var i = 0; i < xs.length; i++) {
        result[i] = provider.graph_layout[xs[i]][%s]
    }
    return result
"""
xcoord = CustomJSTransform(v_func=code % "0", args=dict(provider=graph_renderer.layout_provider))
ycoord = CustomJSTransform(v_func=code % "1", args=dict(provider=graph_renderer.layout_provider))

# Use the transforms to supply coords to a LabelSet 
labels = LabelSet(x=transform('index', xcoord),
                  y=transform('index', ycoord),
                  text='names', text_font_size="12px",
                  x_offset=0, y_offset=15,
                  source=source, render_mode='canvas')

plot.add_layout(labels)


plot.add_tools(HoverTool(tooltips=None), TapTool(), BoxSelectTool(), ResetTool())
plot.renderers.append(graph_renderer)


####   SEIR DIFFERENTIAL EQUATIONS ###
# Total population, N.
N = 1000 #starting total population
# Initial number of infected and recovered individuals, I0 and R0.
Is_nh0 = 1 #initial number of symptomatic infected individuals that are not hospitalized
Is_h0=0 #initial number of symptomatic infected individuals that are hospitalized
Ia_uk0=1 #initial number of asymptomatic infected individuals that are unaware they are infected
Ia_k0=0 #initial number of asymptomatic infected individuals that are aware they are infected
R0 = 0 #intial number of recovered individuals
D0=0 # initial number of dead individuls
E0=0 # initial number of people exposed to the virus but not yet transmitable
# Everyone else, S0, is susceptible to infection initially.
S0 = N - Is_nh0 - Is_h0 - Ia_uk0 - Ia_k0 - R0 - D0 - E0
# Contact rate, beta, and mean recovery rate, gamma, (in 1/days).
beta_S_h=0.001 #the contact/infection rate per day for hospitalized symptomatic infecteds
beta_S_nh=0.1 #the contact/infection rate per day for non-hospitalized symptomatic infecteds
beta_A_uk=0.35 #the contact/infection rate per day for unknown asymptomatic infecteds
beta_A_k=0.1 #the contact/infection rate per day for known symptomatic infecteds
gamma = 0.04  #the recovery rate per day
gamma_hosp=1/25
death_rate_S=0.004 #death rate for symptomatic infecteds
death_rate_hosp=0.008
nat_death=0.0002
nat_birth=0.001
E_to_I_forS=0.5 #rate at which individuals from the exposed class become symptomatic infecteds
E_to_I_forA=0.1 #rate at which as individuals from the exposed class become asymptomatic infecteds
return_rate=0.00002 #rate at which recovered people once again become susceptible
sd=1 # if social distancing is put into effect, the rate at which contact rates will decrease
v_freq=0 #frequency of people getting vaccinated
v_eff=0.98 #how effective the vaccine is 
test_rate_inc=1 #rate at which testing increases over time
hosp=0.1
health_capacity=150
hcd=1 #health capacity effecting the death rate
hcr=1 #health capacity effecting the recovery rate
# A grid of time points (in days)
t = np.linspace(0, 365, 365) #160 days
t_vac=200 #time at which vaccine is introduced

def vac_freq(t_vac, total_time): #function that gives the vaccine rate, it will be 0 before the vaccine is introduced and 0.01 after the vaccine is introduced
    vac_f=0
    if total_time<t_vac:
        vac_f=0
    elif total_time>=t_vac:
        vac_f=0.01
    return vac_f
    
def health_cap_effect(health_capacity, Is_h): #function adjusts hospitalized infecteds' death and recovery rates if health capacity is surpassed
    if Is_h<health_capacity:
        hcd=1
        hcr=1
    elif Is_h>health_capacity:
        hcd=1.5
        hcr=0.7
    health_effect=[hcd, hcr]
    return health_effect
        

# The SIR model differential equations.
def deriv(t, y, N, beta_A_uk, beta_A_k, beta_S_nh, beta_S_h, gamma, gamma_hosp, nat_death, death_rate_S, death_rate_hosp, E_to_I_forA, E_to_I_forS, return_rate, sd, test_rate_inc, t_vac, health_capacity):
    S, E, Ia_uk, Ia_k, Is_nh, Is_h, R, D = y
    v_freq=vac_freq(t_vac, t)
    test_rate=.001*t*test_rate_inc
    hce=health_cap_effect(health_capacity, Is_h)
    dSdt = (-beta_S_nh * sd* S * Is_nh / N)-(beta_S_h * S * Is_h / N)-(beta_A_uk * sd * S * Ia_uk / N)-(beta_A_k * sd * S * Ia_k / N)-(nat_death*S)+(nat_birth*(N-D))+(return_rate*R)-(v_freq*v_eff*S)
    dEdt = (beta_S_nh * sd* S * Is_nh / N)+(beta_S_h * S * Is_h / N)+(beta_A_uk * sd * S * Ia_uk / N)+(beta_A_k * sd * S * Ia_k / N) - (E_to_I_forA * E)-(E_to_I_forS*E)-(nat_death*E)
    dIa_uk_dt= (E_to_I_forA*E)-(nat_death*Ia_uk)-(gamma*Ia_uk)-(test_rate*Ia_uk)
    dIa_k_dt =(test_rate*Ia_uk)-(nat_death*Ia_k)-(gamma*Ia_k)
    dIs_nh_dt = (E_to_I_forS*E)-(nat_death*Is_nh)-(death_rate_S*Is_nh)-(gamma*Is_nh)-(hosp*Is_nh)
    dIs_h_dt = (hosp*Is_nh)-(hce[0]*nat_death*Is_h)-(hce[1]*death_rate_hosp*Is_h)-(gamma_hosp*Is_h)
    dRdt = (gamma * (Ia_uk+Ia_k+Is_nh))+(gamma_hosp*Is_h)-(nat_death*R)-(return_rate*R)+(v_freq*v_eff*S)
    dDdt=nat_death*(S+E+Ia_uk+Ia_k+Is_nh+Is_h+R)+(death_rate_S*Is_nh)+(death_rate_hosp*Is_h)
    return dSdt, dEdt, dIa_uk_dt, dIa_k_dt, dIs_nh_dt, dIs_h_dt, dRdt, dDdt

# Initial conditions vector
y0 = S0, E0, Ia_uk0, Ia_k0, Is_nh0, Is_h0, R0, D0
# Integrate the SIR equations over the time grid, t.
#ret = solve_ivp(deriv, y0, t, args=(N, beta_A_uk, beta_A_k, beta_S_nh, beta_S_h,  gamma, gamma_hosp, nat_death, death_rate_S, death_rate_hosp, E_to_I_forA, E_to_I_forS, return_rate, sd, test_rate_inc, t_vac, health_capacity))
ret = solve_ivp(deriv, t_span=(0,365), y0=y0, t_eval=t, args=(N, beta_A_uk, beta_A_k, beta_S_nh, beta_S_h, gamma, gamma_hosp, nat_death, death_rate_S, death_rate_hosp, E_to_I_forA, E_to_I_forS, return_rate, sd, test_rate_inc, t_vac, health_capacity))
S, E, Ia_uk, Ia_k, Is_nh, Is_h, R, D = ret.y
#print(type(Ia_k))
big_array=[S, E, Ia_uk, Ia_k, Is_nh, Is_h, R, D]

time_slider=Slider(start=0, end=365, value=0, step=1, title="Time (in Days)")
start_vals=[S[0]/2, E[0], Ia_uk[0], Ia_k[0], Is_nh[0], Is_h[0], R[0]/2, D[0]]
current_source=ColumnDataSource(data=dict(sizes=start_vals))
graph_renderer.node_renderer.data_source.add(current_source.data['sizes'], 'size')
graph_renderer.node_renderer.glyph = Circle(size='size', fill_color='color')

    
def update_data(attr, old, new):
    t=time_slider.value
    newS=S[t]/2
    newE=E[t]
    newI1=Ia_uk[t]
    newI2=Ia_k[t]
    newI3=Is_nh[t]
    newI4=Is_h[t]
    newR=R[t]/2
    newD=D[t]
    new_dict=[newS, newE, newI1, newI2, newI3, newI4, newR, newD]
    current_source.data=dict(sizes=new_dict)
    graph_renderer.node_renderer.data_source.add(current_source.data['sizes'], 'size')
    graph_renderer.node_renderer.glyph = Circle(size='size', fill_color='color')
    
def animate_update(time):
    day = time
    if day > 365:
        new_dict=[S[day]/2, E[day], Ia_uk[day], Ia_k[day], Is_nh[day], Is_h[day], R[day]/2, D[day]]
        current_source.data=dict(sizes=new_dict)
        graph_renderer.node_renderer.data_source.add(current_source.data['sizes'], 'size')
        graph_renderer.node_renderer.glyph = Circle(size='size', fill_color='color')
        #time_slider.value = day+1
        

callback_id = None
def animate():
    global callback_id
    if button.label == '► Play':
        button.label = '❚❚ Pause'
        callback_id = curdoc().add_periodic_callback(animate_update, 200)
    else:
        button.label = '► Play'
        curdoc().remove_periodic_callback(callback_id)
    
    
time_slider.on_change('value', update_data)
button = Button(label='► Play', width=60)
button.on_click(animate)

curdoc().add_root(column(plot, time_slider, button))
curdoc().title="Infectious Disease Model"
#output_file("bubble_SEIR.html")
#show(column(plot, time_slider))




