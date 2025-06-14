# -*- coding: utf-8 -*-
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback_context, clientside_callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import os
import package_root
from src.plotting import pie_chart, line_chart
from src.utils import extract_credit_card_data, get_spending, get_totals, get_income, extract_bank_data, update_investment_data, get_total_assets


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


def total_assets_summary():
    total = get_total_assets()

    total_text = html.H4(
        f'TOTAL ASSETS: {total}',
        className='text-center text-primary p-2',
    )

    return total_text


def get_bank_summary(summary_type, n_months):

    sum_txt = 'Total' if summary_type else 'Average'

    rent, credit, misc = get_spending()
    income = get_income(summary_type, n_months)
    saved = get_totals()
    saved = round(saved, 2)
    color = 'green' if saved >= 0 else 'red'

    summary_list = [
        html.H5([
            html.Span(f'{sum_txt} Monthly Income: '),
            html.Span(income, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span(f'{sum_txt} Monthly Rent: '),
            html.Span(rent, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span(f'{sum_txt} Monthly Credit Spending: '),
            html.Span(credit, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span(f'{sum_txt} Monthly Misc Spending: '),
            html.Span(misc, style={'color': 'blue'}),
        ]),
        html.H5([
            html.Span(f'{sum_txt} Monthly Savings: '),
            html.Span(saved, style={'color': color}),
        ]),
    ]

    return summary_list


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

input_form = dbc.Form([
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
                dbc.FormFloating([dbc.Input(type='number', id='cambridge'), dbc.Label('Cambridge'),]),
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
    html.Br(),
    dbc.Row(
        [
            dbc.Col(
                dbc.FormFloating([dbc.Input(type='number', id='nasdaq'), dbc.Label('NASDAQ'),]),
                className='me-3',
            ),
            dbc.Col(
                dbc.FormFloating([dbc.Input(type='number', id='dow'), dbc.Label('DOW'),]),
                className='me-3',
            ),
            dbc.Col(
                dbc.FormFloating([dbc.Input(type='number', id='snp'), dbc.Label('S&P'),]),
                className='me-3',
            ),
        ],
        className='g-3',
        align='center'
    ),
])


spend_inputs = dbc.Stack(
    [
        html.Div(
            html.Span([
                dbc.Label('Average'),
                dbc.Switch(id='summary_switch',
                        value=True, 
                        className='d-inline-block ms-2', 
                        persistence=True),
                dbc.Label('Total'),
            ])
        ),
        html.Div(
            dbc.Input(id='month_total', placeholder='', type='number'),
            className='w-25'
        ),
        html.Div(
            dbc.Col(dbc.Button('Submit', color='primary', id='submit_n_month'), width='auto'),
            className='me-auto',
        ),
        html.Div(
            dbc.Button('REFRESH', color='primary', outline=True, id='refresh'),
        ),
    ],
    direction="horizontal",
    gap=3,
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
                dbc.Input(type='number', id='month', min=1, max=12),
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
                html.Br(),
                dbc.Button('Upload', color='primary', outline=True, id='upload'),
                html.H2(
                    'FINANCIAL TRACKER',
                    className='text-center text-primary p-2',
                ),
                html.Div([
                    total_assets_summary()
                ],
                id='total'),
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
                                    spend_inputs,
                                    html.Br(),
                                    html.Div(id='bank_summary'),
                                    html.Br(),
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
    ],
    fluid=True,
)


"""
==========================================================================
Callbacks
"""

@app.callback(
        Input('upload', 'n_clicks'),
)
def upload_data(upload):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'upload' in changed_id:
        total_text = total_assets_summary()


@app.callback(
        Output('total', 'children'),
        Input('refresh', 'n_clicks'),
)
def display_total(refresh):
    total_text = total_assets_summary()

    return total_text


@app.callback(
        Output('bank_summary', 'children'),
        Output('month_total', 'value'),
        Input('summary_switch', 'value'),
        State('month_total', 'value'),
        Input('refresh', 'n_clicks'),
        Input('submit_n_month', 'n_clicks')
)
def display_monthly_data(summary_type, n_months, refresh, submit):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    
    n_months = 0 if not n_months else n_months
    summary_list = get_bank_summary(summary_type, n_months)
    # if 'refresh' in changed_id and n_months > 1:
    #     n_months = n_months
    # else:
    #     n_months = None
    # print()
        # n_months = 1 if not n_months else n_months
    # print(n_months)
    # summary_list = get_bank_summary(summary_type)


    return summary_list, None


@app.callback(
    Output('investment_line_chart', 'figure'),
    Output('investment_line_chart', 'style'),
    Output('etrade', 'value'),
    Output('retirement', 'value'),
    Output('leidos', 'value'),
    Output('cambridge', 'value'),
    Output('nasdaq', 'value'),
    Output('dow', 'value'),
    Output('snp', 'value'),
    State('etrade', 'value'),
    State('retirement', 'value'),
    State('leidos', 'value'),
    State('cambridge', 'value'),
    State('nasdaq', 'value'),
    State('dow', 'value'),
    State('snp', 'value'),
    Input('switch', 'value'),
    Input('submit_investments', 'n_clicks'),
)
def update_data_display(etrade, retirement, leidos, cambridge, nasdaq, dow, snp, switch, n_clicks):

    data = {'etrade': etrade, 'retirement': retirement, 'leidos': leidos,
            'cambridge': cambridge, 'nasdaq': nasdaq, 'dow': dow, 'snp': snp}
    if etrade or retirement or leidos or cambridge or nasdaq or dow or snp:
        update_investment_data(data)
    path = os.path.join(DATA_PATH, 'investments.csv')

    if n_clicks or os.path.exists(path):
        df = pd.read_csv(path)
        line_figure = line_chart(df,
                                credit=False,
                                switch=switch)
        
        return line_figure, {}, '', '', '', '', '', '', ''
    else:
        return None, {'display': 'none'}, '', '', '', '', '', '', ''


@app.callback(
    Output('spend_pie_chart', 'figure'),
    Output('spend_pie_chart', 'style'),
    Output('spend_line_chart', 'figure'),
    Output('spend_line_chart', 'style'),
    Input('submit_date', 'n_clicks'),
    Input('refresh', 'n_clicks'),
    Input('switch', 'value'),
    Input('data_switch', 'value'),
    State('start_date', 'date'),
    State('end_date', 'date'),
    State('year', 'value'),
    State('month', 'value'),
)
def update_pie(n_clicks, refresh, switch, data_switch, start_date, end_date, year, month):
    # changed_id = [p['prop_id'] for p in callback_context.triggered][0]

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
