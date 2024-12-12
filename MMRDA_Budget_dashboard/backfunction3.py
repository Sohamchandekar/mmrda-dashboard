import pandas as pd
import plotly.graph_objects as go


def ADB_NDB_loanstructure_processing(excel_file):
    """
    Convert a DataFrame into a nested dictionary categorized by 'Project',
    with 'FY' as keys and their data as nested dictionaries. Replace any '-', NaN,
    or null values with 0 in the resulting dictionary.

    Parameters:
        excel_file (str): The path to the Excel file.

    Returns:
        dict: A dictionary categorized by 'Project' with 'FY' as nested keys,
              and cleaned data with no '-' or NaN values.
    """
    df = pd.read_excel(excel_file, sheet_name=0)
    # Ensure the DataFrame has the correct structure and no missing Project values
    df = df.dropna(subset=['Project', 'FY'])

    # Initialize an empty dictionary
    project_dict = {}

    # Group the DataFrame by the 'Project' column
    grouped = df.groupby('Project')

    for project, group in grouped:
        # Initialize a dictionary for the project
        fy_dict = {}
        for _, row in group.iterrows():
            # Convert the row to a dictionary and use FY as the key
            row_data = row.drop(labels=['Project', 'FY']).to_dict()
            # Replace '-', NaN, or null values with 0 in the row data
            cleaned_data = {k: (0 if (v in ['-', None] or pd.isna(v)) else v) for k, v in row_data.items()}
            fy_dict[row['FY']] = cleaned_data

        # Assign the FY dictionary to the project
        project_dict[project] = fy_dict

    return project_dict


# def project_loan_card(project_data):
#     """
#     Generate HTML cards for each project with the total loan amount.
#
#     Args:
#         project_data (dict): Dictionary where keys are project names, and values are nested dictionaries
#                              containing year-wise loan details.
#
#     Returns:
#         str: HTML string containing all the cards.
#     """
#     # Initialize an empty string to hold all the cards
#     all_cards_html = '<div class="card-group">'
#
#     # Iterate through each project in the dictionary
#     for project_name, year_data in project_data.items():
#         # Initialize the total loan amount for the project
#         total_loan_amount = 0
#
#         # Iterate through each year's data in the project
#         for year, data in year_data.items():
#             # Safely access the 'ML Tranche' value and add it to the total
#             ml_tranche_value = data.get('ML Tranche', 0)
#             if isinstance(ml_tranche_value, (int, float)):  # Ensure it's numeric
#                 total_loan_amount += ml_tranche_value
#
#         # Format the total loan amount with the rupee symbol and "Cr"
#         formatted_loan_amount = f"₹ {total_loan_amount:,.2f} Cr"
#
#         # Create the card HTML for the project
#         card_html = f"""
#         <div class="card custom-card bg-info text-white mb-3">
#             <div class="card-body text-center">
#                 <h5 class="card-title text-blue"><b>Total Loan Amount<br>{project_name}</b></h5>
#                 <p class="card-value-text">{formatted_loan_amount}</p>
#             </div>
#         </div>
#
#     """
#         # Append the card HTML to the group
#         all_cards_html += card_html
#
#     # Close the card group div
#     all_cards_html += '</div>'
#
#     return all_cards_html

def project_loan_card(project_data):
    """
    Generate HTML cards for each project with the total loan amount,
    including integrated styling for individual cards and the card group.

    Args:
        project_data (dict): Dictionary where keys are project names, and values are nested dictionaries
                             containing year-wise loan details.

    Returns:
        str: HTML string containing all the cards with inline styling.
    """
    # Inline styles for individual cards
    card_style = """
        background-color: white; 
        border: none; 
        box-shadow: rgba(0, 0, 0, 0.35) 0px 5px 15px;
        border-radius: 12px; 
        padding: 10px; 
        margin: 5px; 
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        min-width: 250px; /* Minimum width */
        min-height: 100px; /* Minimum height */
    """
    card_heading_style = "color: black; font-size: 18px; font-weight: bold; margin-bottom: 10px;"
    card_value_style = "color: darkblue; font-size: 15px; font-weight: bold;"

    # Inline styles for the card group
    group_style = "display: flex; flex-wrap: wrap; justify-content: center; gap: 15px;"

    # Initialize an empty string to hold all the cards
    all_cards_html = f'<div style="{group_style}">'

    # Iterate through each project in the dictionary
    for project_name, year_data in project_data.items():
        # Initialize the total loan amount for the project
        total_loan_amount = 0

        # Iterate through each year's data in the project
        for year, data in year_data.items():
            # Safely access the 'ML Tranche' value and add it to the total
            ml_tranche_value = data.get('ML Tranche', 0)
            if isinstance(ml_tranche_value, (int, float)):  # Ensure it's numeric
                total_loan_amount += ml_tranche_value

        # Format the total loan amount with the rupee symbol and "Cr"
        formatted_loan_amount = f"₹ {total_loan_amount:,.2f} Cr"

        # Create the card HTML for the project
        card_html = f"""
        <div style="{card_style}">
            <div class="card-body">
                <h5 style="{card_heading_style}">Total Loan Amount<br>{project_name}</h5>
                <p style="{card_value_style}">{formatted_loan_amount}</p>
            </div>
        </div>
        """
        # Append the card HTML to the group
        all_cards_html += card_html

    # Close the card group div
    all_cards_html += '</div>'

    return all_cards_html



def plot_repayment_trend(data):
    """
    Generates an interactive line chart showing repayment trends for each project
    and a summed-up trend across all projects, including zones for interest-only
    and principal repayment.

    Parameters:
        data (dict): A nested dictionary containing project data with yearly disbursement details.
    """
    fig = go.Figure()
    total_trend = {}  # To store summed values across all projects
    max_y = 0  # To determine the global maximum y-value

    # Precompute the global max y-value for consistent zone height
    for years in data.values():
        for details in years.values():
            max_y = max(max_y, details.get("ML CASH FLOW", 0))

    shapes_per_project = {}  # To store shapes for each project
    project_names = list(data.keys())
    default_project = project_names[0]  # Use the first key as the default project

    # Loop through each project
    for project, years in data.items():
        x_values = []
        y_values = []
        text_values = []  # Text values for formatting

        # Initialize zones for interest-only and principal repayment
        interest_zones = []
        principal_zones = []
        principal_started = False  # Flag to track when principal repayment starts

        for year, details in years.items():
            x_values.append(year)
            cash_flow = details.get("ML CASH FLOW", 0)
            y_values.append(cash_flow)  # Fetch ML CASH FLOW
            text_values.append(f"₹{cash_flow:,.2f}")  # Format with Rs prefix

            repayment_principal = details.get("Repayment - Principal", 0)

            # If repayment_principal is 0, this is the interest-only zone
            if repayment_principal == 0 and not principal_started:
                interest_zones.append(year)
            elif repayment_principal > 0:
                # Once principal repayment starts, mark the principal repayment zone
                if not principal_started:
                    principal_started = True
                principal_zones.append(year)

            # Update the total trend dictionary
            total_trend[year] = total_trend.get(year, 0) + cash_flow

        # Add traces for the current project
        fig.add_trace(go.Scatter(
            x=x_values, y=y_values, mode='lines+markers',
            text=text_values, texttemplate='%{text}',  # Add formatted text
            textposition='top center',
            name=project, visible=(project == default_project)
        ))

        # Prepare shapes for interest-only and principal repayment zones
        project_shapes = []
        if interest_zones:
            project_shapes.append(
                dict(
                    type="rect",
                    x0=interest_zones[0], x1=interest_zones[-1],
                    y0=0, y1=max_y,  # Static y boundaries
                    fillcolor="rgba(0, 255, 0, 0.2)",  # Solid green for interest-only
                    line=dict(width=0)
                )
            )

        if principal_zones:
            project_shapes.append(
                dict(
                    type="rect",
                    x0=principal_zones[0], x1=principal_zones[-1],
                    y0=0, y1=max_y,  # Static y boundaries
                    fillcolor="rgba(255, 0, 0, 0.2)",  # Solid red for principal repayment
                    line=dict(width=0)
                )
            )

        shapes_per_project[project] = project_shapes

    # Add trace for total disbursement across all projects
    total_x = sorted(total_trend.keys())
    total_y = [total_trend[year] for year in total_x]
    total_text = [f"₹{value:,.2f}" for value in total_y]  # Format total values
    fig.add_trace(go.Scatter(
        x=total_x, y=total_y, mode='lines+markers',
        text=total_text, texttemplate='%{text}',  # Add formatted text
        textposition='top center',
        name='Total Disbursement', visible=False
    ))

    # Dropdown menu for toggling individual projects and total
    buttons = []
    for i, project in enumerate(project_names):
        visibility = [False] * (len(project_names) + 1)  # Hide all traces by default
        visibility[i] = True  # Show the selected project

        buttons.append(dict(
            label=project,
            method="update",
            args=[
                {"visible": visibility},
                {"shapes": shapes_per_project.get(project, []),
                 "title": f"Repayment Trend for {project}"}
            ]
        ))

    # Add a button for the total disbursement trend
    visibility = [False] * (len(project_names) + 1)
    visibility[-1] = True
    buttons.append(dict(
        label="Total Disbursement",
        method="update",
        args=[
            {"visible": visibility},
            {"shapes": [],
             "title": "Total Repayment Trend Across All Projects"}
        ]
    ))

    # Update layout
    fig.update_layout(
        updatemenus=[dict(active=0, buttons=buttons, x=1.15, y=1.1)],
        title=f"Repayment Trend for {default_project}",
        xaxis_title="Year",
        yaxis_title="Disbursement (ML CASH FLOW)",
        legend_title="Projects",
        template="plotly",
        showlegend=True,
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")  # Move legend below chart
    )

    # Set chart size and initial shapes
    fig.update_layout(
        width=1080, height=580,
        shapes=shapes_per_project.get(default_project, [])
    )

    return fig