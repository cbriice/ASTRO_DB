from dash import dcc, html

def default_layout():
    return dict(
        xaxis=dict(
            tickformatstops=[
                dict(dtickrange=[None, 60000], value="%H:%M:%S.%L"),    #various time formats depending on x axis scale
                dict(dtickrange=[60000, 3600000], value="%H:%M:%S"),
                dict(dtickrange=[3600000, 86400000], value="%H:%M"),
                dict(dtickrange=[86400000, None], value="%H:%M")
            ],
            title_text='Time', showline=True, linewidth=2, linecolor='black', mirror=True,
            ticks='inside', tickwidth=2, tickcolor='black', tickfont=dict(size=16), showgrid=False
        ),
        yaxis=dict(
            showline=True, linewidth=2, linecolor='black', mirror=True,
            ticks='inside', tickwidth=2, tickcolor='black', tickfont=dict(size=16), showgrid=False
        ),
        height=500, width=750, plot_bgcolor='white', font=dict(size=18), showlegend=True, xaxis_title_font=dict(size=20), yaxis_title_font=dict(size=20),
    )