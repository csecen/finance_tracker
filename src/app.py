# -*- coding: utf-8 -*-
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback_context, clientside_callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import os
import package_root
from src.plotting import pie_chart, line_chart
from src.utils import extract_credit_card_data, get_spending, get_totals, get_income, extract_bank_data, update_investment_data


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA, dbc.icons.FONT_AWESOME],
)

#  make dataframe from  spreadsheet:
DATA_PATH = os.path.join(package_root._root, 'data')

credit_card_data_path = os.path.join(DATA_PATH, 'credit_card_data.csv')
credit_card_df = pd.read_csv(credit_card_data_path)
credit_card_df['Date'] = pd.to_datetime(credit_card_df['Date'], format='%Y-%m-%d')

bank_withdrawals_path = os.path.join(DATA_PATH, 'deductions.csv')
bank_withdrawals_df = pd.read_csv(bank_withdrawals_path)
bank_withdrawals_df['Date'] = pd.to_datetime(bank_withdrawals_df['Date'], format='%Y-%m-%d')

def get_bank_summary():

    rent, credit, misc = get_spending()
    income = get_income()
    saved = get_totals()
    saved = round(saved, 2)
    color = 'green' if saved >= 0 else 'red'

    bank_summary = html.Div([
        html.H5([
            html.Span('Total Monthly Income: '),
            html.Span(income, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span('Total Monthly Rent: '),
            html.Span(rent, style={'color': 'blue'}),
            # children=f'Total Monthly Rent: {rent}',
        ]),
        html.H5([
            html.Span('Total Monthly Credit Spending: '),
            html.Span(credit, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span('Total Monthly Misc Spending: '),
            html.Span(misc, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span('Total Monthly Savings: '),
            html.Span(saved, style={'color': color}),
        ])
    ])

    return bank_summary


"""
==========================================================================
Mode Switcher
"""
color_mode_switch = html.Span([
        dbc.Label(className='fa fa-moon', html_for='switch'),
        dbc.Switch(id='switch',
                   value=True, 
                   className='d-inline-block ms-1', 
                   persistence=True),
        dbc.Label(className='fa fa-sun', html_for='switch'),
    ])

input_form = dbc.Form(
    dbc.Row(
        [
            dbc.Col(
                dbc.FormFloating([dbc.Input(type='number', id='etrade'), dbc.Label('e-trade'),]),
                className='me-3',
            ),
            dbc.Col(
                dbc.FormFloating([dbc.Input(type='number', id='retirement'), dbc.Label('401k'),]),
                className='me-3',
            ),
            dbc.Col(
                dbc.FormFloating([dbc.Input(type='number', id='leidos'), dbc.Label('Leidos Stock'),]),
                className='me-3',
            ),
            dbc.Col(
                dbc.Button('Submit', id='submit_investments', color='primary', className='me-1'),
                class_name='me-3'
            ),
        ],
        className='g-3',
        align='center'
    ),
)

date_pickers = dbc.Form([
    dbc.Row(
        [
            dbc.Label('Start Date', width='auto'),
            dbc.Col(
                dcc.DatePickerSingle(
                    id='start_date',
                    month_format='MMM Do, YY',
                    placeholder='MMM Do, YY',
                ),
                className='me-3',
                width='auto'
            ),
            dbc.Label('End Date', width='auto'),
            dbc.Col(
                dcc.DatePickerSingle(
                    id='end_date',
                    month_format='MMM Do, YY',
                    placeholder='MMM Do, YY',
                ),
                className='me-3',
                width='auto'
            ),
            dbc.Col(dbc.Button('Submit', color='primary', id='submit_date'), width='auto'),
        ],
        className='mb-3',
    ),
    dbc.Row(
        [
            dbc.Label('Year', width='auto'),
            dbc.Col(
                dbc.Input(type='number', id='year'),
                className='me-3',
                width=2
            ),
            dbc.Label('Month', width='auto'),
            dbc.Col(
                dbc.Input(type='number', id='month'),
                className='me-3',
                width=2
            ),
        ],
        className='mb-3',
    ),
    dbc.Row([
        html.Span([
            dbc.Label('Bank'),
            dbc.Switch(id='data_switch',
                       value=True, 
                       className='d-inline-block ms-2', 
                       persistence=True),
            dbc.Label('Credit Card'),
        ])
    ])
])


"""
===========================================================================
Main Layout
"""

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col([
                color_mode_switch,
                html.H2(
                    'FINANCIAL TRACKER',
                    className='text-center text-primary p-2',
                ),
                html.H4(
                    'TOTAL ASSETS',
                    className='text-center text-primary p-2',
                ),
                html.Div(
                    [
                        dbc.Button('REFRESH', color='primary', outline=True, id='refresh'),
                    ],
                    className="d-grid gap-2 col-6 mx-auto",
                ),
                # dbc.Col(dbc.Button('REFRESH', color='primary', outline=True, id='refresh'), width='auto', align='center'),
                html.Hr(),
            ])
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card([
                            dbc.CardHeader('SPENDING'),
                            dbc.CardBody(
                                [
                                    get_bank_summary(),
                                    date_pickers,
                                    dcc.Graph(id='spend_pie_chart', className='mb-2'),
                                    dcc.Graph(id="spend_line_chart", className="mb-2"),
                                ]
                            ),
                        ],
                        style={'width': 'auto'},
                        ),
                    ],
                    className='pt-4',
                ),
                dbc.Col(
                    [
                        dbc.Card([
                            dbc.CardHeader('INVESTMENTS'),
                            dbc.CardBody(
                                [
                                    input_form,
                                    dcc.Graph(id="investment_line_chart", className="mb-2"),
                                ]
                            ),
                        ]),
                    ],
                    className="pt-4",
                ),
            ],
            className="ms-1",
        ),
        # dbc.Row(
        #     [
        #         dbc.Col(tabs, width=12, lg=5, className="mt-4 border"),
        #         dbc.Col(
        #             [
        #                 dcc.Graph(id="allocation_pie_chart", className="mb-2"),
        #                 dcc.Graph(id="returns_chart", className="pb-4"),
        #                 html.Hr(),
        #                 html.Div(id="summary_table"),
        #                 html.H6(datasource_text, className="my-2"),
        #             ],
        #             width=12,
        #             lg=7,
        #             className="pt-4",
        #         ),
        #     ],
        #     className="ms-1",
        # ), 
    ],
    fluid=True,
)


"""
==========================================================================
Callbacks
"""

@app.callback(
    Output("investment_line_chart", "figure"),
    Output('investment_line_chart', 'style'),
    Output('etrade', 'value'),
    Output('retirement', 'value'),
    Output('leidos', 'value'),
    State('etrade', 'value'),
    State('retirement', 'value'),
    State('leidos', 'value'),
    Input('switch', 'value'),
    Input('submit_investments', 'n_clicks'),
)
def update_data(etrade, retirement, leidos, switch, n_clicks):

    data = {'etrade': etrade, 'retirement': retirement, 'leidos': leidos}
    if etrade or retirement or leidos:
        update_investment_data(data)
    path = os.path.join(DATA_PATH, 'investments.csv')

    if n_clicks or os.path.exists(path):
        df = pd.read_csv(path)
        line_figure = line_chart(df,
                                credit=False,
                                switch=switch)
        
        return line_figure, {}, '', '', ''
    else:
        return None, {'display': 'none'}, '', '', ''


@app.callback(
    Output('spend_pie_chart', 'figure'),
    Output('spend_pie_chart', 'style'),
    Output('spend_line_chart', 'figure'),
    Output('spend_line_chart', 'style'),
    Input('submit_date', 'n_clicks'),
    Input('switch', 'value'),
    Input('data_switch', 'value'),
    State('start_date', 'date'),
    State('end_date', 'date'),
    State('year', 'value'),
    State('month', 'value'),
)
def update_pie(n_clicks, switch, data_switch, start_date, end_date, year, month):
    if n_clicks:
        if data_switch:
            df = credit_card_df
            credit = True
        else:
            df = bank_withdrawals_df
            credit = False
        
        pie_figure = pie_chart(df,
                               start_date,
                               end_date,
                               year,
                               month,
                               switch,
                               credit
                               )
        
        line_figure = line_chart(df,
                                 credit,
                                 switch)

        return pie_figure, {}, line_figure, {}
    else:
        return None, {'display': 'none'}, None, {'display': 'none'}
       

clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute("data-bs-theme", switchOn ? "light" : "dark");
       return window.dash_clientside.no_update
    }
    """,
    Output("switch", "id"),
    Input("switch", "value"),
)


if __name__ == "__main__":
    app.run(debug=True)
