#!/usr/bin/env python
#-*- coding: utf-8 -*-
# THOUVENIN Arthur athouvenin@outlook.fr
# 01/01/2020
########################
import pandas
import plotly.express

from geonamescache.mappers import country as country_mapper

def map_display(search_title,country_dict):
    key='iso3'
    mapper=country_mapper(from_key='name',to_key=key)
    countries=[]
    nb_aff=[]
    mapp=[]
    for country in country_dict:
        countries.append(country)
        nb_aff.append(country_dict[country])
        mapp.append(mapper(country))
    df=pandas.DataFrame.from_dict({"Country name":countries,"Number of Affiliation":nb_aff,key:mapp})
    fig=plotly.express.choropleth(
        df,
        locations=key,
        color="Number of Affiliation",
        hover_name="Country name",
        color_continuous_scale=plotly.express.colors.sequential.Greens)
    fig.update_layout(title=search_title)
    plotly.offline.plot(fig,filename="./TMP/map_choropleth.html",auto_open=True)
    country_dict_plot={k:v for k,v in sorted(country_dict.items(), key=lambda item:item[1])}
    fig1=plotly.graph_objs.Figure([plotly.graph_objs.Bar(
        x=list(country_dict_plot.keys()),
        y=list(country_dict_plot.values()),
        text=list(country_dict_plot.values()),
        textposition='auto')])
    fig1.update_layout(
        title=search_title,
        xaxis_tickangle=-45)
    plotly.offline.plot(fig1,filename="./TMP/bar_countries.html",auto_open=True)
