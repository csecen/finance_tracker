import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import package_root
from src.utils import date_parser


def line_chart(data: pd.DataFrame, credit: bool = True, switch: bool = True):
    '''
    Plot the line chart for the given data
    '''
    y = 'Debit' if credit else 'Amount'   # dynamically change title text

    fig = px.line(data, x='Date', y=y, color='Category')

    # change background and text color based on selected light or dark mode
    if switch:
        background = 'white'
        font = '#1C2525'
    else:
        background = '#1C2525'
        font = 'white'

    title = f"Overall {'Credit' if credit else 'Account'} Spend Summary "
    fig.update_layout(
        title_text=title,
        title_x=0.5,
        margin=dict(b=25, t=75, l=35, r=25),
        height=325,
        paper_bgcolor=background,
        font=dict(color=font),
    )

    return fig


def pie_chart(data: pd.DataFrame, 
              start_date: str = None, 
              end_date: str = None, 
              year: int = None, 
              month: int = None,
              switch: bool = True,
              credit: bool = True):
    '''
    Plot the pie graph for the selected data source based on the selected dates
    '''

    # get only a subset of the data based on the selected dates
    subset, date_string = date_parser(data,
                                      start_date,
                                      end_date,
                                      year,
                                      month)

    labels = subset['Category'].unique().tolist()
    col_name = 'Debit' if credit else 'Amount'
    group = subset.groupby(['Category'])[col_name].sum()
    values = group.values.tolist()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                textinfo='label+percent',
                textposition='inside',
                sort=False,
                hoverinfo='none',
            )
        ])
    
    # change background and text color based on selected light or dark mode
    if switch:
        background = 'white'
        font = '#1C2525'
    else:
        background = '#1C2525'
        font = 'white'

    # Dynamically change title based on data source
    title = f"{'Credit' if credit else 'Account'} Summary for {date_string}"

    fig.update_layout(
        title_text=title,
        title_x=0.5,
        margin=dict(b=25, t=75, l=35, r=25),
        height=325,
        paper_bgcolor=background,
        font=dict(color=font),
    )

    return fig