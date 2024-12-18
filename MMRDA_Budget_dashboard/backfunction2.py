import pandas as pd
from datetime import datetime


def read_excel_and_process(excel_file):
    # Read the data from the sheets
    engineering_division = pd.read_excel(excel_file, sheet_name='engineering')
    town_country_division = pd.read_excel(excel_file, sheet_name='town_planning')
    transport_communication_division = pd.read_excel(excel_file, sheet_name='transport_communication')
    metro_projects_division = pd.read_excel(excel_file, sheet_name='metro_projects')
    mono_piu_division = pd.read_excel(excel_file, sheet_name='mono_piu')

    # Define a function for processing a DataFrame
    def process_dataframe(df):
        # Initialize an empty list for new column names
        new_columns = []

        for col in df.columns:
            # Attempt to parse column name as datetime in different formats
            parsed_date = None
            try:
                # ISO datetime format (e.g., "2024-02-01 00:00:00")
                parsed_date = datetime.strptime(str(col), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # Custom datetime format (e.g., "01-02-2024 12.00.00 AM")
                    parsed_date = datetime.strptime(str(col), "%d-%m-%Y %I.%M.%S %p")
                except ValueError:
                    pass

            # Convert parsed date to "Month Year" format, or check for patterns
            if parsed_date:
                new_col = parsed_date.strftime("%b %Y")  # Format as "Month Year"
            else:
                # Check for specific string patterns
                if isinstance(col, str):
                    if 'B. E.\n2023-24' in col or 'B. E 2023-24' in col:
                        new_col = "Budgeted Expenditure 2023-24"
                    elif 'R. E.\n2023-24' in col or 'R. E 2023-24' in col:
                        new_col = "Revised Expenditure 2023-24"
                    elif 'B. E.\n2024-25' in col or 'B. E 2024-25' in col:
                        new_col = "Budgeted Expenditure 2024-25"
                    else:
                        new_col = col  # If no match, keep the original column name
                else:
                    new_col = col  # Leave non-string columns unchanged

            new_columns.append(new_col)

        # Update DataFrame columns
        df.columns = new_columns

        # Convert all numeric values to 2 decimal places
        df = df.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)

        return df

    # Process each DataFrame
    engineering_division = process_dataframe(engineering_division)
    town_country_division = process_dataframe(town_country_division)
    transport_communication_division = process_dataframe(transport_communication_division)
    metro_projects_division = process_dataframe(metro_projects_division)
    mono_piu_division = process_dataframe(mono_piu_division)

    return (engineering_division, town_country_division, transport_communication_division,
            metro_projects_division, mono_piu_division)


def generate_table_from_dataframe(df, cutoff_month):
    """
    Generates HTML table with progress bars and target markers based on a DataFrame and a cutoff month.

    Args:
        df (pd.DataFrame): DataFrame containing project data.
        cutoff_month (str): The cutoff month till which data is considered (e.g., 'Oct 2024').

    Returns:
        str: HTML table with stacked and animated progress bars.
    """
    from datetime import datetime

    # Convert cutoff_month to datetime object
    cutoff_month = datetime.strptime(cutoff_month, "%b %Y")

    # List of month columns from which we will sum up the expenses
    month_columns = ['Apr 2024', 'May 2024', 'Jun 2024', 'Jul 2024', 'Aug 2024', 'Sep 2024',
                     'Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025']

    # Filter month columns up to the cutoff month
    valid_month_columns = [col for col in month_columns if datetime.strptime(col, "%b %Y") <= cutoff_month]
    # Sort the DataFrame by budget in descending order
    df = df.sort_values(by='Budgeted Expenditure 2024-25', ascending=False)

    # Calculate months elapsed since April 2024 (start of financial year)
    start_of_year = datetime.strptime("Apr 2024", "%b %Y")
    months_elapsed = (cutoff_month.year - start_of_year.year) * 12 + (cutoff_month.month - start_of_year.month) + 1

    # Create the HTML table structure
    table_html = '<table class="project-table">'

    # Add table header
    table_html += '''
        <thead>
            <tr>
                <th style="width: 3%;">Sr No.</th>
                <th style="width: 25%;">Project Name</th>
                <th style="width: 20%;">Project Owner</th>
                <th style="width: 50%;">Progress</th>
            </tr>
        </thead>
        <tbody>
    '''

    # Iterate over the rows of the DataFrame to create table rows
    for index, row in df.iterrows():
        project_name = row.get('Particulars', 'N/A')  # Default to 'N/A' if no project name

        # Handle multiple engineers
        engineer_names = row.get('SE', 'NA')  # Default to 'NA' if no engineer name
        if isinstance(engineer_names, str):  # If it's a string, split into a list
            engineer_list = [name.strip() for name in engineer_names.split(',')]
        else:
            engineer_list = [str(engineer_names)]  # Ensure single names are still a list

        # Create a bullet list for engineers
        engineer_html = '<ul class="engineer-list">'
        for name in engineer_list:
            engineer_html += f'<li class="engineer-item" ondblclick="filterByEngineer(this)">{name}</li>'
        engineer_html += '</ul>'

        total_budget = row.get('Budgeted Expenditure 2024-25', 0)  # Total budget for the project

        # Calculate YTD expense by summing the expenses till the cutoff month
        ytd_expense = sum(row.get(month, 0) for month in valid_month_columns)

        # Calculate the progress percentage
        progress_percentage = (ytd_expense / total_budget) * 100 if total_budget > 0 else 0
        remaining_percentage = max(0, 100 - progress_percentage) if total_budget > 0 else 100

        # Calculate estimated expenditure (target)
        monthly_budget = total_budget / 12
        estimated_expenditure = monthly_budget * months_elapsed

        # Calculate target percentage
        target_percentage = (estimated_expenditure / total_budget) * 100 if total_budget > 0 else 0

        # Check for overachievement
        if progress_percentage > 100:
            progress_percentage_display = progress_percentage
            achieved_color = "#F3C623"  # Yellow for overachievement
        else:
            progress_percentage_display = progress_percentage
            achieved_color = "#4caf50"  # Green for normal progress

        # Create stacked progress bar HTML
        progress_bar_html = f'''
            <div class="progress-bar-container" style="position: relative;">
                <div class="progress-bar achieved" style="width: {min(progress_percentage, 100)}%; background-color: {achieved_color};">
                    <span class="progress-text">{progress_percentage_display:.2f}%</span>
                </div>
                <div class="progress-bar remaining" style="width: {remaining_percentage}%; background-color: #c8e6c9;"></div>
                <div class="progress-bar target" style="position: absolute; top: 0; left: {target_percentage}%; width: 2px; height: 100%; background-color: #ff9800;"></div>
            </div>
            <div class="progress-values">
                <span><b>Budget:</b> ₹ {total_budget:,.2f} | <b>Incurred:</b> ₹ {ytd_expense:,.2f} | <b>Target:</b> ₹ {estimated_expenditure:,.2f}</span>
            </div>
        '''

        # Add the row to the table
        table_html += f'''
            <tr data-engineers="{','.join(engineer_list).lower()}">
                <td>{index + 1}</td>
                <td>{project_name}</td>
                <td>{engineer_html}</td>
                <td>{progress_bar_html}</td>
            </tr>
        '''

    # Close the table
    table_html += '</tbody></table>'

    return table_html

