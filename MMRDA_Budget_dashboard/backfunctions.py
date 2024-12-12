import plotly.graph_objects as go
from datetime import datetime
import pandas as pd


# Define the global DataFrames
receipt_data = None
receipt_backdata = None
expense_data = None
expense_backdata = None

# Global variable to store the summary dataframe and key insights
insight_dataframe = None
key_insights = {}
predicted_revenue = {}

def excel_processing_to_dataframe(receipts, expenditure):
    """
    Processes two Excel/CSV files (receipts and expenditure) and creates four DataFrames:
    - receipt_data: Main data from the receipts file (default sheet)
    - receipt_backdata: Data from a specific sheet in the receipts file (sheet index 2)
    - expense_data: Main data from the expenditure file (default sheet)
    - expense_backdata: Data from a specific sheet in the expenditure file (sheet index 1)

    Args:
        receipts (str): File path to the receipts Excel/CSV file.
        expenditure (str): File path to the expenditure Excel/CSV file.

    Returns:
        tuple: A tuple of four DataFrames (receipt_data, receipt_backdata, expense_data, expense_backdata)
    """
    global receipt_data, receipt_backdata, expense_data, expense_backdata



    try:
        # Load receipt data
        if receipts.endswith(('.xls', '.xlsx')):
            receipt_data = pd.read_excel(receipts)
            receipt_backdata = pd.read_excel(receipts, sheet_name=3)
        elif receipts.endswith('.csv'):
            receipt_data = pd.read_csv(receipts)
            receipt_backdata = None  # CSV files do not have multiple sheets

        # Load expenditure data
        if expenditure.endswith(('.xls', '.xlsx')):
            expense_data = pd.read_excel(expenditure)
            expense_backdata = pd.read_excel(expenditure, sheet_name=3)
        elif expenditure.endswith('.csv'):
            expense_data = pd.read_csv(expenditure)
            expense_backdata = None  # CSV files do not have multiple sheets

        print("DataFrames loaded successfully.")
    except Exception as e:
        print(f"An error occurred while processing the files: {e}")

    return receipt_data, receipt_backdata, expense_data, expense_backdata

def feature_engineering(df, as_on_date):
    """
    Feature engineering for 'Proportionate Budget YTD', '% Achievement YTD', and '% Achievement vs Proportionate'.

    Parameters:
    df (pd.DataFrame): Input DataFrame.
    as_on_date (str): Date in 'MMM YYYY' format (e.g., 'Sept 2024').

    Returns:
    pd.DataFrame: DataFrame with new features.
    """
    # Define the starting date (April 2024)
    start_date = datetime(2024, 4, 1)

    # Month abbreviation mapping to handle both 'Sept' and 'Sep'
    month_map = {
        'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr',
        'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Aug',
        'Sept': 'Sep', 'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dec'
    }

    # Parse the input date
    try:
        month_abbr = month_map.get(as_on_date.split()[0], as_on_date.split()[0])
        formatted_date = f"{month_abbr} {as_on_date.split()[1]}"
        target_date = datetime.strptime(formatted_date, '%b %Y')
    except Exception as e:
        print(f"Error parsing date '{as_on_date}': {e}")
        return df

    # Calculate the number of months elapsed since April 2024
    elapsed_months = (target_date.year - start_date.year) * 12 + (target_date.month - start_date.month) + 1

    # Calculate 'Proportionate Budget YTD' if not already present
    df['Proportionate Budget YTD'] = df['Actual Budget 2024-25'] / 12 * elapsed_months

    # Calculate '% Achievement YTD' (Actual YTD as a percentage of the total budget)
    df['% Achievement YTD'] = (df['Actual YTD (Incurred)'] / df['Actual Budget 2024-25']) * 100
    df['% Achievement YTD'] = round(df['% Achievement YTD'],2)

    # Calculate '% Achievement vs Proportionate' (Actual YTD as a percentage of Proportionate Budget YTD)
    df['% Achievement to Proportionate'] = (df['Actual YTD (Incurred)'] / df['Proportionate Budget YTD']) * 100
    df['% Achievement to Proportionate'] = round(df['% Achievement to Proportionate'],2)

    # Calculate 'Remaining Budget' (how much of the total budget is still pending)
    df['Remaining Budget'] = df['Actual Budget 2024-25'] - df['Actual YTD (Incurred)']

    return df


def rename_date_columns(df):
    """
    Renames columns with datetime format to "Month Year" format (e.g., "Apr 2024").

    Parameters:
    df (pd.DataFrame): Input DataFrame.

    Returns:
    pd.DataFrame: DataFrame with renamed date columns.
    """
    new_columns = []
    for col in df.columns:
        try:
            # Attempt to convert the column name to datetime
            date_col = pd.to_datetime(col)
            # Format the date as "Month Year"
            new_col = date_col.strftime("%b %Y")
        except (ValueError, TypeError):
            # If the conversion fails, keep the original column name
            new_col = col
        new_columns.append(new_col)

    # Rename the columns in the DataFrame
    df.columns = new_columns
    return df


# Function to rename date columns to "Month Year" format
def rename_date_columns(df):
    # Iterate over all columns and modify date columns
    new_columns = []
    for col in df.columns:
        try:
            # Convert the column name to datetime and format it as "Month Year"
            new_col = pd.to_datetime(col).strftime("%b %Y")
        except (ValueError, TypeError):
            # If the conversion fails, keep the original column name
            new_col = col
        new_columns.append(new_col)

    # Rename the columns in the DataFrame
    df.columns = new_columns
    return df


# Function to rename fiscal year columns
def rename_fy_columns(df):
    new_columns = []
    for col in df.columns:
        if "As per" in col:
            # Extract the fiscal year part from the column name
            year_part = col.replace("As per ", "").strip()
            start_year, end_year = year_part.split("-")
            # Create the new column name in "FY 2020-21" format
            new_col = f"FY {start_year[-2:]}-{end_year[-2:]}"
        else:
            new_col = col
        new_columns.append(new_col)

    # Rename the columns in the DataFrame
    df.columns = new_columns
    return df


# def backdata_processing(receipt_backdata, expense_backdata):
#     """
#     Processes the receipt_backdata and expense_backdata DataFrames:
#     - Calculates YoY growth percentages
#     - Analyzes trends (consistent increase, consistent decrease, fluctuating trend)
#     - Estimates the budget for the next fiscal year
#     - Renames date and fiscal year columns
#
#     Args:
#         receipt_backdata (pd.DataFrame): The receipts backdata DataFrame.
#         expense_backdata (pd.DataFrame): The expenses backdata DataFrame.
#     """
#
#     # Helper functions for column renaming
#     def rename_date_columns(df):
#         new_columns = []
#         for col in df.columns:
#             try:
#                 new_col = pd.to_datetime(col).strftime("%b %Y")
#             except (ValueError, TypeError):
#                 new_col = col
#             new_columns.append(new_col)
#         df.columns = new_columns
#         return df
#
#     def rename_fy_columns(df):
#         new_columns = []
#         for col in df.columns:
#             if "As per" in col:
#                 year_part = col.replace("As per ", "").strip()
#                 start_year, end_year = year_part.split("-")
#                 new_col = f"FY {start_year[-2:]}-{end_year[-2:]}"
#             else:
#                 new_col = col
#             new_columns.append(new_col)
#         df.columns = new_columns
#         return df
#
#     # Process the expense_backdata
#     if expense_backdata is not None:
#         # Calculate YoY growth percentages
#         expense_backdata['YoY Growth 2021-22'] = ((expense_backdata['As per 2021-2022'] - expense_backdata[
#             'As per 2020-2021']) / expense_backdata['As per 2020-2021']) * 100
#         expense_backdata['YoY Growth 2022-23'] = ((expense_backdata['As per 2022-2023'] - expense_backdata[
#             'As per 2021-2022']) / expense_backdata['As per 2021-2022']) * 100
#         expense_backdata['YoY Growth 2023-24'] = ((expense_backdata['Actual Budget 2023-24'] - expense_backdata[
#             'As per 2022-2023']) / expense_backdata['As per 2022-2023']) * 100
#         expense_backdata['YoY Growth 2024-25'] = ((expense_backdata['Actual Budget 2024-25'] - expense_backdata[
#             'Actual Budget 2023-24']) / expense_backdata['Actual Budget 2023-24']) * 100
#
#         # Analyze trends
#         trends = {}
#         for index, row in expense_backdata.iterrows():
#             growth_rates = row[['YoY Growth 2021-22', 'YoY Growth 2022-23', 'YoY Growth 2023-24', 'YoY Growth 2024-25']]
#             if all(growth_rates > 0):
#                 trends[index] = 'Consistent Increase'
#             elif all(growth_rates < 0):
#                 trends[index] = 'Consistent Decrease'
#             else:
#                 trends[index] = 'Fluctuating Trend'
#
#         expense_backdata['Trend Analysis'] = expense_backdata.index.map(trends)
#
#         # Estimate next year's budget
#         expense_backdata['Estimated Budget 2025-26'] = expense_backdata['Actual Budget 2024-25'] * (
#                     1 + expense_backdata[
#                 ['YoY Growth 2021-22', 'YoY Growth 2022-23', 'YoY Growth 2023-24', 'YoY Growth 2024-25']].mean(
#                 axis=1) / 100)
#
#         # Rename columns
#         expense_backdata = rename_date_columns(expense_backdata)
#         expense_backdata = rename_fy_columns(expense_backdata)
#
#     # Process the receipt_backdata
#     if receipt_backdata is not None:
#         # Calculate YoY growth percentages
#         receipt_backdata['YoY Growth 2021-22'] = ((receipt_backdata['As per 2021-2022'] - receipt_backdata[
#             'As per 2020-2021']) / receipt_backdata['As per 2020-2021']) * 100
#         receipt_backdata['YoY Growth 2022-23'] = ((receipt_backdata['As per 2022-2023'] - receipt_backdata[
#             'As per 2021-2022']) / receipt_backdata['As per 2021-2022']) * 100
#         receipt_backdata['YoY Growth 2023-24'] = ((receipt_backdata['Actual Budget 2023-24'] - receipt_backdata[
#             'As per 2022-2023']) / receipt_backdata['As per 2022-2023']) * 100
#         receipt_backdata['YoY Growth 2024-25'] = ((receipt_backdata['Actual Budget 2024-25'] - receipt_backdata[
#             'Actual Budget 2023-24']) / receipt_backdata['Actual Budget 2023-24']) * 100
#
#         # Analyze trends
#         trends = {}
#         for index, row in receipt_backdata.iterrows():
#             growth_rates = row[['YoY Growth 2021-22', 'YoY Growth 2022-23', 'YoY Growth 2023-24', 'YoY Growth 2024-25']]
#             if all(growth_rates > 0):
#                 trends[index] = 'Consistent Increase'
#             elif all(growth_rates < 0):
#                 trends[index] = 'Consistent Decrease'
#             else:
#                 trends[index] = 'Fluctuating Trend'
#
#         receipt_backdata['Trend Analysis'] = receipt_backdata.index.map(trends)
#
#         # Estimate next year's budget
#         receipt_backdata['Estimated Budget 2025-26'] = receipt_backdata['Actual Budget 2024-25'] * (
#                     1 + receipt_backdata[
#                 ['YoY Growth 2021-22', 'YoY Growth 2022-23', 'YoY Growth 2023-24', 'YoY Growth 2024-25']].mean(
#                 axis=1) / 100)
#
#         # Rename columns
#         receipt_backdata = rename_date_columns(receipt_backdata)
#         receipt_backdata = rename_fy_columns(receipt_backdata)
#
#     print('Backdata Preprocesed Successfully')
#
#     return receipt_backdata, expense_backdata
#
#
def insights_calculation(receipt_backdata, expense_backdata):
    global insight_dataframe, key_insights

    # Monthly columns representing the months of the year
    monthly_columns = [
        "Apr 2024", "May 2024", "Jun 2024", "Jul 2024", "Aug 2024",
        "Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024", "Jan 2025",
        "Feb 2025", "Mar 2025"
    ]

    # Calculate total monthly revenue and expense
    total_revenue = receipt_backdata[monthly_columns].sum()
    total_expense = expense_backdata[monthly_columns].sum()

    # Calculate monthly profit/loss
    monthly_profit_loss = total_revenue - total_expense

    # Calculate Revenue per Rupee of Expense
    revenue_per_rupee_of_expense = total_revenue / total_expense
    revenue_per_rupee_of_expense = revenue_per_rupee_of_expense.fillna(0)  # Handle division by zero

    # Create a summary DataFrame
    summary_df = pd.DataFrame({
        "Total Revenue": total_revenue,
        "Total Expense": total_expense,
        "Profit/Loss": monthly_profit_loss,
        "Revenue per Rupee of Expense": revenue_per_rupee_of_expense
    })

    # Calculate cumulative revenue, expense, and profit/loss
    summary_df["Cumulative Revenue"] = total_revenue.cumsum()
    summary_df["Cumulative Expense"] = total_expense.cumsum()
    summary_df["Cumulative Profit/Loss"] = summary_df["Cumulative Revenue"] - summary_df["Cumulative Expense"]

    # Calculate percentage of annual budget utilized
    annual_revenue_budget = receipt_backdata["Actual Budget 2024-25"].sum()
    annual_expense_budget = expense_backdata["Actual Budget 2024-25"].sum()
    summary_df["Revenue Budget Utilization (%)"] = (total_revenue.cumsum() / annual_revenue_budget) * 100
    summary_df["Expense Budget Utilization (%)"] = (total_expense.cumsum() / annual_expense_budget) * 100

    # Store the summary DataFrame as global variable
    insight_dataframe = summary_df

    # Find the month with highest revenue and highest expense
    highest_revenue_month = total_revenue.idxmax()
    highest_expense_month = total_expense.idxmax()

    # Overall profit/loss at the end of the year
    total_profit_loss = summary_df["Profit/Loss"].sum()

    total_annual_revenue = summary_df["Total Revenue"].sum()
    total_annual_revenue = round(total_annual_revenue, 2)

    total_annual_expenditure = summary_df["Total Expense"].sum()
    total_annual_expenditure = round(total_annual_expenditure, 2)

    # Populate key insights dictionary
    key_insights = {
        "Total Revenue": total_annual_revenue,
        "Total Expenditure": total_annual_expenditure,

        "Highest Revenue Month": {
            "Month": highest_revenue_month,
            "Revenue": total_revenue[highest_revenue_month]
        },
        "Highest Expense Month": {
            "Month": highest_expense_month,
            "Expense": total_expense[highest_expense_month]
        },
        "Overall P/L for the Year": total_profit_loss,
        "Revenue per Rupee of Expense (Monthly)": revenue_per_rupee_of_expense.to_dict(),
        "Months with Surplus": summary_df[summary_df['Profit/Loss'] > 0].index.tolist(),
        "Months with Deficit": summary_df[summary_df['Profit/Loss'] < 0].index.tolist()
    }

    # Return the summary dataframe and key insights (optional)
    return summary_df, key_insights
#
#
# def revenue_predictor(receipt_backdata, summary_df, as_on_month):
#     # Define a list of all possible month columns
#     month_columns = [
#         'Apr 2024', 'May 2024', 'Jun 2024', 'Jul 2024', 'Aug 2024', 'Sep 2024',
#         'Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025'
#     ]
#
#     # Extract the relevant columns from receipt_backdata
#     revenue_data = receipt_backdata[month_columns].sum(numeric_only=True)
#
#     # Extract cumulative revenue from summary_df
#     cumulative_revenue = summary_df['Cumulative Revenue']
#
#     # Filter out data up to the 'as_on_month'
#     try:
#         as_on_index = month_columns.index(as_on_month)
#         historical_revenue = revenue_data[:as_on_index + 1]
#         cumulative_revenue = cumulative_revenue[:as_on_index + 1]
#     except ValueError:
#         print(f"Error: '{as_on_month}' not found in month columns.")
#         return None
#
#     # Create a DataFrame combining both sources
#     historical_df = pd.DataFrame({
#         'Month': np.arange(len(historical_revenue)),
#         'Revenue': historical_revenue.values,
#         'CumulativeRevenue': cumulative_revenue.values
#     }).dropna()
#
#     # Prepare features and target for regression
#     X = historical_df[['Month', 'CumulativeRevenue']]
#     y = historical_df['Revenue']
#
#     # Initialize and fit the linear regression model
#     lin_reg_model = LinearRegression()
#     lin_reg_model.fit(X, y)
#
#     # Use Exponential Smoothing for trend analysis
#     exp_smooth_model = ExponentialSmoothing(historical_revenue.values, trend='add', seasonal=None)
#     exp_smooth_fit = exp_smooth_model.fit()
#
#     # Predict revenue for the next 3 months using linear regression
#     next_months = np.arange(len(historical_revenue), len(historical_revenue) + 3).reshape(-1, 1)
#     next_cumulative_revenue = cumulative_revenue.values[-1] + np.cumsum([historical_revenue.mean()] * 3)
#     lin_reg_predictions = lin_reg_model.predict(np.hstack((next_months, next_cumulative_revenue.reshape(-1, 1))))
#
#     # Predict revenue for the next 3 months using exponential smoothing
#     exp_smooth_predictions = exp_smooth_fit.forecast(steps=3)
#
#     # Average the predictions from both models
#     final_predictions = (lin_reg_predictions + exp_smooth_predictions) / 2
#
#     # Map the predictions to month names
#     predicted_months = month_columns[as_on_index + 1:as_on_index + 4]
#     prediction_results = dict(zip(predicted_months, final_predictions))
#
#     return prediction_results
#
# def plot_revenue_forecast(receipt_backdata, summary_df, as_on_month):
#     """
#     This function calls the `revenue_predictor` to forecast future revenue,
#     calculates supposed revenue, and creates an enhanced line chart using Plotly.
#     """
#     # Call the revenue predictor function
#     predicted_revenue = revenue_predictor(receipt_backdata, summary_df, as_on_month)
#
#     if predicted_revenue is None:
#         print("Revenue prediction failed.")
#         return
#
#     # Define month columns
#     month_columns = [
#         'Apr 2024', 'May 2024', 'Jun 2024', 'Jul 2024', 'Aug 2024', 'Sep 2024',
#         'Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025'
#     ]
#
#     # Get the index of the 'as_on_month'
#     as_on_index = month_columns.index(as_on_month)
#
#     # Extract actual revenue data up to the specified month
#     actual_revenue = receipt_backdata[month_columns].sum(numeric_only=True)[:as_on_index + 1]
#
#     # Calculate the total budgeted revenue and supposed monthly revenue
#     total_budgeted_revenue = receipt_backdata['Actual Budget 2024-25'].sum()
#     supposed_monthly_revenue = total_budgeted_revenue / 12
#
#     # Prepare the data for plotting
#     all_months = month_columns[:as_on_index + 4]  # Include 3 projected months
#     all_revenue = list(actual_revenue.values) + list(predicted_revenue.values())
#
#     # Create a DataFrame for plotting
#     plot_df = pd.DataFrame({
#         'Month': all_months,
#         'Revenue': all_revenue
#     })
#
#     # Split the DataFrame into actual and projected parts
#     actual_df = plot_df.iloc[:as_on_index + 1]
#     projected_df = plot_df.iloc[as_on_index + 1:]
#
#     # Create the Plotly figure
#     fig = go.Figure()
#
#     # Add actual revenue line (solid) with markers and data labels
#     fig.add_trace(go.Scatter(
#         x=actual_df['Month'],
#         y=actual_df['Revenue'],
#         mode='lines+markers+text',
#         name='Actal Received Revenue',
#         line=dict(color='blue', width=3),
#         marker=dict(size=8, color='blue'),
#         text=[f"{val:.2f}" for val in actual_df['Revenue']],
#         textposition='top center'
#     ))
#
#     # Add projected revenue line (dotted) with markers and data labels
#     fig.add_trace(go.Scatter(
#         x=projected_df['Month'],
#         y=projected_df['Revenue'],
#         mode='lines+markers+text',
#         name='Projected Receivable Revenue',
#         line=dict(color='red', width=3, dash='dot'),
#         marker=dict(size=8, color='red', symbol='diamond'),
#         text=[f"{val:.2f}" for val in projected_df['Revenue']],
#         textposition='top center'
#     ))
#
#     # Add a supposed revenue line (dashed) representing the expected monthly revenue
#     supposed_revenue_line = [supposed_monthly_revenue] * len(all_months)
#     fig.add_trace(go.Scatter(
#         x=all_months,
#         y=supposed_revenue_line,
#         mode='lines+markers',
#         name='Budgeted Revenue',
#         line=dict(color='green', width=2, dash='dash'),
#         marker=dict(size=6, color='green', symbol='circle'),
#         text=[f"Supposed: {supposed_monthly_revenue:.2f}"] * len(all_months),
#         textposition='bottom center'
#     ))
#
#     # Add a shaded area between the actual and projected revenue
#     fig.add_trace(go.Scatter(
#         x=all_months,
#         y=all_revenue,
#         fill='tozeroy',
#         name='Revenue Trend Area',
#         line=dict(width=0),
#         opacity=0.2,
#         fillcolor='rgba(0, 128, 255, 0.2)'
#     ))
#
#     # Update layout with enhanced styling
#     fig.update_layout(
#
#         height=540,  # Set figure height
#         title={
#             'text': 'Revenue Forcasting',  # Title text
#             'font': {
#                 'size': 19,  # Font size
#                 'color': '#0C359E',  # Font color
#                 'family': 'Arial, sans-serif',  # Font family (optional)
#                 'weight': 'bold'  # Make the title bold
#             }
#         },
#         xaxis=dict(
#             title='Month',
#             tickmode='array',
#             tickvals=all_months,
#             tickangle=45,
#             showgrid=True
#         ),
#         yaxis=dict(
#             title='Revenue (in Units)',
#             showgrid=True,
#             zeroline=True,
#             zerolinewidth=2
#         ),
#         legend=dict(
#             orientation='h',  # Horizontal legend
#             yanchor='bottom',  # Anchor the legend to the bottom
#             y=-0.3,  # Position the legend below the x-axis
#             xanchor='center',  # Center the legend
#             x=0.5  # Center the legend horizontally
#         ),
#         template='plotly_white',
#         margin=dict(l=50, r=20, t=70, b=10), # Adjust margins for better spacing
#         hovermode='x unified'
#     )
#
#     # Add tooltips with more details
#     fig.update_traces(hovertemplate='%{x}<br>Revenue: %{y:.2f}')
#     return fig
#
# ## Charts Creation ##
#
#
#
# def plot_revenue_expense_trend(summary_df):
#     """
#     Generates a line chart to show the trend of Total Revenue and Total Expense with markers.
#
#     Parameters:
#         summary_df (pd.DataFrame): DataFrame containing the summary data with columns
#                                    ['Total Revenue', 'Total Expense'] and index as months.
#
#     Returns:
#         fig (plotly.graph_objects.Figure): The generated Plotly figure.
#     """
#     # Extract data
#     months = summary_df.index
#     total_revenue = summary_df['Total Revenue']
#     total_expense = summary_df['Total Expense']
#
#     # Create the line chart
#     fig = go.Figure()
#
#     # Add Total Revenue line with markers
#     fig.add_trace(go.Scatter(
#         x=months,
#         y=total_revenue,
#         mode='lines+markers+text',
#         name='Total Revenue',
#         line=dict(color='#859F3D', width=2),
#         marker=dict(color='#859F3D', size=8),
#         text=[f"{val:.2f}" for val in total_revenue],
#         textposition="top center"
#     ))
#
#     # Add Total Expense line with markers
#     fig.add_trace(go.Scatter(
#         x=months,
#         y=total_expense,
#         mode='lines+markers+text',
#         name='Total Expense',
#         line=dict(color='#C40C0C', width=2),
#         marker=dict(color='#C40C0C', size=8),
#         text=[f"{val:.2f}" for val in total_expense],
#         textposition="bottom center"
#     ))
#
#     # Update layout
#     fig.update_layout(
#         width=1200,  # Set figure width
#         height=500,  # Set figure height
#         title={
#             'text': 'Receipts & Expenditure Comparison',  # Title text
#             'font': {
#                 'size': 19,  # Font size
#                 'color': '#0C359E',  # Font color
#                 'family': 'Arial, sans-serif',  # Font family (optional)
#                 'weight': 'bold'  # Make the title bold
#             }
#         },
#         xaxis_title='Month',
#         yaxis_title='Amount (in Cr)',
#         legend=dict(
#             orientation='h',  # Horizontal legend
#             yanchor='bottom',  # Anchor the legend to the bottom
#             y=-0.3,  # Position the legend below the x-axis
#             xanchor='center',  # Center the legend
#             x=0.5  # Center the legend horizontally
#         ),
#         template='plotly_white',
#         hovermode='x unified',
#         margin=dict(l=50, r=20, t=70, b = 10)  # Adjust margins for better spacing
#     )
#
#     # Show grid for better readability
#     fig.update_xaxes(showgrid=True)
#     fig.update_yaxes(showgrid=True)
#
#     return fig
# def receipt_timeline_L3(receipt_backdata):
#     """
#     Processes the receipt_backdata to create a revenue timeline DataFrame and plots a line chart
#     with a dropdown slicer for selecting Particulars, including 'Total Revenue'.
#
#     Args:
#         receipt_backdata (pd.DataFrame): The input DataFrame containing receipt data.
#
#     Returns:
#         fig (plotly.graph_objs._figure.Figure): The Plotly figure object for embedding in the dashboard.
#     """
#     # Extract the relevant columns for the timeline DataFrame
#     columns = [
#         "Particulars", "Apr 2024", "May 2024", "Jun 2024", "Jul 2024", "Aug 2024",
#         "Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024", "Jan 2025", "Feb 2025", "Mar 2025"
#     ]
#
#     # Create the revenue timeline DataFrame
#     revenue_timeline_df = receipt_backdata[columns].copy()
#
#     # Calculate Total Revenue for each month
#     total_revenue = revenue_timeline_df.drop(columns=["Particulars"]).sum()
#
#     # Append the Total Revenue as a new row
#     total_revenue_row = pd.DataFrame([["Total Revenue"] + total_revenue.tolist()], columns=columns)
#     revenue_timeline_df = pd.concat([revenue_timeline_df, total_revenue_row], ignore_index=True)
#
#     # Melt the DataFrame for better plotting (long format)
#     revenue_timeline_df_melted = revenue_timeline_df.melt(
#         id_vars=["Particulars"],
#         var_name="Month",
#         value_name="Revenue"
#     )
#
#     # Define a color map for consistent colors
#     color_map = {
#         "Total Revenue": "#636EFA",
#         "Revenue A": "#EF553B",
#         "Revenue B": "#00CC96",
#         "Revenue C": "#AB63FA",
#         "Revenue D": "#FFA15A"
#     }
#
#     # Create the initial line chart using Plotly
#     fig = go.Figure()
#
#     # Add traces for each Particular with consistent colors and data labels
#     unique_particulars = revenue_timeline_df["Particulars"].unique()
#     for particular in unique_particulars:
#         filtered_df = revenue_timeline_df_melted[revenue_timeline_df_melted["Particulars"] == particular]
#         color = color_map.get(particular, "#1F77B4")
#
#         # Add the line trace
#         fig.add_trace(
#             go.Scatter(
#                 x=filtered_df["Month"],
#                 y=filtered_df["Revenue"],
#                 mode="lines+markers+text",
#                 name=particular,
#                 line=dict(color=color, width=2),
#                 marker=dict(size=8),
#                 text=filtered_df["Revenue"],
#                 textposition="top center",
#                 showlegend=True
#             )
#         )
#
#     # Add dropdown menu for selecting Particulars including 'Total Revenue'
#     dropdown_buttons = []
#
#     # Create a dropdown button for each Particular
#     for particular in unique_particulars:
#         filtered_visibility = [p == particular for p in unique_particulars]
#         dropdown_buttons.append(
#             dict(
#                 label=particular,
#                 method="update",
#                 args=[
#                     {"visible": filtered_visibility},
#                     {"title": f"Revenue Timeline for {particular} (FY 2024-25)"}
#                 ]
#             )
#         )
#
#     # Add an "All" option to show all Particulars except "Total Revenue"
#     dropdown_buttons.insert(
#         0,
#         dict(
#             label="All (Excluding Total Revenue)",
#             method="update",
#             args=[
#                 {"visible": [p != "Total Revenue" for p in unique_particulars]},
#                 {"title": "Revenue Timeline (FY 2024-25)"}
#             ]
#         )
#     )
#
#     # Add an option to show only "Total Revenue"
#     dropdown_buttons.append(
#         dict(
#             label="Total Revenue",
#             method="update",
#             args=[
#                 {"visible": [p == "Total Revenue" for p in unique_particulars]},
#                 {"title": "Total Revenue Timeline (FY 2024-25)"}
#             ]
#         )
#     )
#
#     # Update layout with dropdown menu and styling
#     fig.update_layout(
#         xaxis_title="Month",
#         yaxis_title="Revenue (In Cr)",
#         hovermode="x unified",
#         template="plotly_white",
#         updatemenus=[
#             dict(
#                 buttons=dropdown_buttons,
#                 direction="down",
#                 showactive=True,
#                 x=0.5,
#                 xanchor="center",
#                 y=1.15,
#                 yanchor="top"
#             )
#         ],
#         legend=dict(title="Particulars", orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
#     )
#
#     # Return the Plotly figure object
#     return fig
#
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
#
# def expense_timeline_L3(expense_backdata):
#     """
#     Processes the expense_backdata to create an expense timeline DataFrame and plots a line chart
#     with a dropdown slicer for selecting Particulars, including 'Total Expense'.
#
#     Args:
#         expense_backdata (pd.DataFrame): The input DataFrame containing expense data.
#
#     Returns:
#         fig (plotly.graph_objs._figure.Figure): The Plotly figure object for embedding in the dashboard.
#     """
#     # Define the relevant columns for the timeline DataFrame
#     columns = [
#         "Particulars", "Apr 2024", "May 2024", "Jun 2024", "Jul 2024", "Aug 2024",
#         "Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024", "Jan 2025", "Feb 2025", "Mar 2025"
#     ]
#
#     # Check if all required columns exist in the DataFrame
#     missing_columns = [col for col in columns if col not in expense_backdata.columns]
#     if missing_columns:
#         raise ValueError(f"Missing columns in the input DataFrame: {missing_columns}")
#
#     # Create the expense timeline DataFrame
#     expense_timeline_df = expense_backdata[columns].copy()
#
#     # Calculate Total Expense for each month
#     total_expense = expense_timeline_df.drop(columns=["Particulars"]).sum()
#
#     # Append the Total Expense as a new row
#     total_expense_row = pd.DataFrame([["Total Expense"] + total_expense.tolist()], columns=columns)
#     expense_timeline_df = pd.concat([expense_timeline_df, total_expense_row], ignore_index=True)
#
#     # Melt the DataFrame for better plotting (long format)
#     expense_timeline_df_melted = expense_timeline_df.melt(
#         id_vars=["Particulars"],
#         var_name="Month",
#         value_name="Expense"
#     )
#
#     # Define a color map for consistent colors
#     color_map = {
#         "Total Expense": "#636EFA",
#         "Expense A": "#EF553B",
#         "Expense B": "#00CC96",
#         "Expense C": "#AB63FA",
#         "Expense D": "#FFA15A"
#     }
#
#     # Create the initial line chart using Plotly
#     fig = go.Figure()
#
#     # Add traces for each Particular with consistent colors and data labels
#     unique_particulars = expense_timeline_df["Particulars"].unique()
#     for particular in unique_particulars:
#         filtered_df = expense_timeline_df_melted[expense_timeline_df_melted["Particulars"] == particular]
#         color = color_map.get(particular, "#1F77B4")
#
#         # Add the line trace
#         fig.add_trace(
#             go.Scatter(
#                 x=filtered_df["Month"],
#                 y=filtered_df["Expense"],
#                 mode="lines+markers+text",
#                 name=particular,
#                 line=dict(color=color, width=2),
#                 marker=dict(size=8),
#                 text=filtered_df["Expense"],
#                 textposition="top center",
#                 showlegend=True
#             )
#         )
#
#     # Add dropdown menu for selecting Particulars including 'Total Expense'
#     dropdown_buttons = []
#
#     # Create a dropdown button for each Particular
#     for particular in unique_particulars:
#         filtered_visibility = [p == particular for p in unique_particulars]
#         dropdown_buttons.append(
#             dict(
#                 label=particular,
#                 method="update",
#                 args=[
#                     {"visible": filtered_visibility},
#                     {"title": f"Expense Timeline for {particular} (FY 2024-25)"}
#                 ]
#             )
#         )
#
#     # Add an "All" option to show all Particulars except "Total Expense"
#     dropdown_buttons.insert(
#         0,
#         dict(
#             label="All (Excluding Total Expense)",
#             method="update",
#             args=[
#                 {"visible": [p != "Total Expense" for p in unique_particulars]},
#                 {"title": "Expense Timeline (FY 2024-25)"}
#             ]
#         )
#     )
#
#     # Add an option to show only "Total Expense"
#     dropdown_buttons.append(
#         dict(
#             label="Total Expense",
#             method="update",
#             args=[
#                 {"visible": [p == "Total Expense" for p in unique_particulars]},
#                 {"title": "Total Expense Timeline (FY 2024-25)"}
#             ]
#         )
#     )
#
#     # Update layout with dropdown menu and styling
#     fig.update_layout(
#         xaxis_title="Month",
#         yaxis_title="Expense (In Cr)",
#         hovermode="x unified",
#         template="plotly_white",
#         updatemenus=[
#             dict(
#                 buttons=dropdown_buttons,
#                 direction="down",
#                 showactive=True,
#                 x=0.5,
#                 xanchor="center",
#                 y=1.15,
#                 yanchor="top"
#             )
#         ],
#         legend=dict(title="Particulars", orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
#     )
#
#     # Return the Plotly figure object
#     return fig
#
#
# def revenue_expense_pl_bar_chart(insight_dataframe):
#     # Extract data for plotting
#     months = insight_dataframe.index
#     total_revenue = insight_dataframe["Total Revenue"]
#     total_expense = insight_dataframe["Total Expense"]
#     profit_loss = insight_dataframe["Profit/Loss"]
#
#     # Create a Plotly figure
#     fig = go.Figure()
#
#     # Add bars for Total Revenue
#     fig.add_trace(go.Bar(
#         x=months,
#         y=total_revenue,
#         name='Total Revenue',
#         marker_color='skyblue'
#     ))
#
#     # Add bars for Total Expense
#     fig.add_trace(go.Bar(
#         x=months,
#         y=total_expense,
#         name='Total Expense',
#         marker_color='salmon'
#     ))
#
#     # Add bars for Profit/Loss
#     fig.add_trace(go.Bar(
#         x=months,
#         y=profit_loss,
#         name='Profit/Loss',
#         marker_color='lightgreen'
#     ))
#
#     # Update layout for the figure
#     fig.update_layout(
#         title='Monthly Revenue, Expense, and Profit/Loss',
#         xaxis_title='Months',
#         yaxis_title='Amount (In Cr)',
#         barmode='group',  # Use 'group' for side-by-side bars, 'stack' for stacked bars
#         legend_title='Metrics',
#         template='plotly_white',
#         xaxis_tickangle=-45,
#         autosize=True,
#         width=1000,
#         height=600
#     )
#
#     # Customize hover labels
#     fig.update_traces(hovertemplate='%{y:.2f}')
#
#     # Return the Plotly figure
#     return fig
#
#
# def profit_card(key_insights):
#     # HTML string to store all card components
#     cards_html = ""
#
#     # Card for Overall Profit/Loss
#     profit_loss = key_insights['Overall P/L for the Year']
#     cards_html += f"""
#     <div class="card custom-card {profit_loss} text-white mb-3">
#         <div class="card-body text-center">
#             <h5 class="card-title text-blue">Overall Profit/Loss for the Year</h5>
#             <p class="card-value-text">₹ {profit_loss:.2f} cr</p>
#         </div>
#     </div>
#     """
#     return cards_html
#
# def total_revenue_card(key_insights):
#     # HTML string to store all card components
#     cards_html = ""
#
#     # Card for Overall Profit/Loss
#     revenue = key_insights['Total Revenue']
#     profit_color = "bg-success" if revenue > 0 else "bg-danger"
#     cards_html += f"""
#     <div class="card custom-card {revenue} text-white mb-3">
#         <div class="card-body text-center">
#             <h5 class="card-title text-blue">Total Revenue Received<br>(YTD 2024) </h5>
#             <p class="card-value-text">₹ {revenue:.2f} cr</p>
#         </div>
#     </div>
#     """
#     return cards_html
#
# def total_expenditure_card(key_insights):
#     # HTML string to store all card components
#     cards_html = ""
#
#     # Card for Overall Profit/Loss
#     expenditure = key_insights['Total Expenditure']
#     cards_html += f"""
#     <div class="card custom-card {expenditure} text-white mb-3">
#         <div class="card-body text-center">
#             <h5 class="card-title text-blue">Total Expenditure Incurred <br>(YTD 2024) </h5>
#             <p class="card-value-text">₹ {expenditure:.2f} cr</p>
#         </div>
#     </div>
#     """
#     return cards_html
#

#
# def revenue_achievement_gauge(receipt_backdata, summary_df):
#     """
#     This function calculates the percentage of revenue achieved against the budgeted revenue
#     and displays it using a professional-looking gauge chart.
#     """
#     # Step 1: Calculate Total Budgeted Revenue for 2024-25
#     total_budgeted_revenue = receipt_backdata['Actual Budget 2024-25'].sum()
#
#     # Step 2: Calculate Total Revenue Achieved from the summary_df
#     total_revenue_achieved = summary_df['Total Revenue'].sum()
#
#     # Step 3: Calculate the Achievement Percentage
#     achievement_percentage = (total_revenue_achieved / total_budgeted_revenue) * 100
#
#     # Step 4: Create the Gauge Chart
#     fig = go.Figure(go.Indicator(
#         mode="gauge+number+delta",
#         value=achievement_percentage,
#         number={'suffix': "%", 'font': {'size': 30, 'color': '#0C359E'}},  # Change number color
#         delta={'reference': 100, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
#         gauge={
#             'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "darkblue"},
#             'bar': {'color': "#0C359E", 'line': {'width': 2, 'color': 'black'}},  # Add border to the bar
#             'bgcolor': "rgba(246, 246, 246, 0.5)",
#             'borderwidth': 2,
#             'bordercolor': "lightgray",
#             'steps': [
#                 {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.7)'},  # Light red
#                 {'range': [50, 75], 'color': 'rgba(255, 165, 0, 0.7)'},  # Light orange
#                 {'range': [75, 100], 'color': 'rgba(0, 128, 0, 0.7)'}  # Light green
#             ],
#             'threshold': {
#                 'line': {'color': "black", 'width': 4},
#                 'thickness': 0.75,
#                 'value': achievement_percentage
#             }
#         }
#     ))
#
#     # Step 5: Update the Layout for Aesthetics
#     fig.update_layout(
#         width=350,  # Set figure width
#         height=280,  # Set figure height
#         title={
#             'text': f"Revenue Achievement % of<br> Rs. {total_budgeted_revenue} Cr",
#             'y': 0.9,
#             'x': 0.5,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': dict(size=19, color='#0C359E', family='Arial, sans-serif', weight='bold')  # Change title font color and size
#         },
#         font=dict(family="Arial, sans-serif", size=15),
#         # template='plotly_white',
#         paper_bgcolor='rgba(246, 246, 246, 0.5)',
#         margin=dict(l=35, r=35, b=30)  # Adjust margins for better spacing
#     )
#
#     return fig
#
# def expense_achievement_gauge(expense_backdata, summary_df):
#     """
#     This function calculates the percentage of revenue achieved against the budgeted revenue
#     and displays it using a professional-looking gauge chart.
#     """
#     # Step 1: Calculate Total Budgeted Revenue for 2024-25
#     total_budgeted_expense = expense_backdata['Actual Budget 2024-25'].sum()
#
#     # Step 2: Calculate Total Revenue Achieved from the summary_df
#     total_expense_achieved = summary_df['Total Expense'].sum()
#
#     # Step 3: Calculate the Achievement Percentage
#     achievement_percentage = (total_expense_achieved / total_budgeted_expense) * 100
#
#     # Step 4: Create the Gauge Chart
#     fig = go.Figure(go.Indicator(
#         mode="gauge+number+delta",
#         value=achievement_percentage,
#         number={'suffix': "%", 'font': {'size': 30, 'color': '#0C359E'}},  # Change number color
#         delta={'reference': 100, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
#         gauge={
#             'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "darkblue"},
#             'bar': {'color': "#0C359E", 'line': {'width': 2, 'color': 'black'}},  # Add border to the bar
#             'bgcolor': "rgba(246, 246, 246, 0.5)",
#             'borderwidth': 2,
#             'bordercolor': "lightgray",
#             'steps': [
#                 {'range': [0, 50], 'color': 'rgba(255, 0, 0, 0.7)'},  # Light red
#                 {'range': [50, 75], 'color': 'rgba(255, 165, 0, 0.7)'},  # Light orange
#                 {'range': [75, 100], 'color': 'rgba(0, 128, 0, 0.7)'}  # Light green
#             ],
#             'threshold': {
#                 'line': {'color': "black", 'width': 4},
#                 'thickness': 0.75,
#                 'value': achievement_percentage
#             }
#         }
#     ))
#
#     # Step 5: Update the Layout for Aesthetics
#     fig.update_layout(
#         width=350,  # Set figure width
#         height=280,  # Set figure height
#         title={
#             'text': f"Expense Achievement % of<br> Rs. {total_budgeted_expense} Cr",
#             'y': 0.9,
#             'x': 0.5,
#             'xanchor': 'center',
#             'yanchor': 'top',
#             'font': dict(size=19, color='#0C359E', family='Arial, sans-serif', weight='bold')  # Change title font color and size
#         },
#         font=dict(family="Arial, sans-serif", size=15),
#         # template='plotly_white',
#         paper_bgcolor='rgba(246, 246, 246, 0.5)',
#         margin=dict(l=35, r=35, b=30)  # Adjust margins for better spacing
#     )
#
#     return fig

def total_revenue_card(receipt_backdata):
    """
    Generates an HTML card for the Total Budgeted Revenue (FY 2024-25).

    Parameters:
    receipt_backdata (pd.DataFrame): DataFrame containing budget data.

    Returns:
    str: HTML string for the card.
    """
    # Calculate the total budgeted revenue
    total_budgeted_revenue = receipt_backdata['Actual Budget 2024-25'].sum()

    # Format the revenue value with a currency symbol and suffix 'Cr'
    revenue_value = f"₹ {total_budgeted_revenue:,.0f} Cr"

    # Create the HTML card
    cards_html = f"""
    <div class="card custom-card bg-info text-white mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-blue">Total Budgeted Receipts<br>(FY 2024-25)</h5>
            <p class="card-value-text">{revenue_value}</p>
        </div>
    </div>
    """
    return cards_html

def proportion_revenue_card(receipt_backdata):
    """
    Generates an HTML card for the Total Budgeted Revenue (FY 2024-25).

    Parameters:
    receipt_backdata (pd.DataFrame): DataFrame containing budget data.

    Returns:
    str: HTML string for the card.
    """

    total_Proportionate_Budget_YTD = receipt_backdata['Proportionate Budget YTD'].sum()

    # Format the revenue value with a currency symbol and suffix 'Cr'
    revenue_value = f"₹ {total_Proportionate_Budget_YTD:,.0f} Cr"

    # Create the HTML card
    cards_html = f"""
    <div class="card custom-card bg-info text-white mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-blue">Planned<br>Year to Date Receipt </h5>
            <p class="card-value-text">{revenue_value}</p>
        </div>
    </div>
    """
    return cards_html

def total_expense_card(expense_backdata):
    """
    Generates an HTML card for the Total Budgeted Revenue (FY 2024-25).

    Parameters:
    receipt_backdata (pd.DataFrame): DataFrame containing budget data.

    Returns:
    str: HTML string for the card.
    """
    # Calculate the total budgeted revenue
    total_budgeted_expense = expense_backdata['Actual Budget 2024-25'].sum()

    # Format the revenue value with a currency symbol and suffix 'Cr'
    expense_value = f"₹ {total_budgeted_expense:,.0f} Cr"

    # Create the HTML card
    cards_html = f"""
    <div class="card custom-card bg-info text-white mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-blue">Total Budgeted Expense<br>(FY 2024-25)</h5>
            <p class="card-value-text">{expense_value}</p>
        </div>
    </div>
    """
    return cards_html


def proportion_expense_card(expense_backdata):
    """
    Generates an HTML card for the Total Budgeted Revenue (FY 2024-25).

    Parameters:
    receipt_backdata (pd.DataFrame): DataFrame containing budget data.

    Returns:
    str: HTML string for the card.
    """

    total_Proportionate_Budget_YTD = expense_backdata['Proportionate Budget YTD'].sum()

    # Format the revenue value with a currency symbol and suffix 'Cr'
    expense_value = f"₹ {total_Proportionate_Budget_YTD:,.0f} Cr"

    # Create the HTML card
    cards_html = f"""
    <div class="card custom-card bg-info text-white mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-blue">Planned<br>Year to Date Expense </h5>
            <p class="card-value-text">{expense_value}</p>
        </div>
    </div>
    """
    return cards_html

def average_revenue_per_expense_card(summary_df, as_on_month):
    """
    This function takes `summary_df` and an `as_on_month` string as input,
    computes the average 'Revenue per Rupee of Expense' up to the given month,
    and returns a card-like HTML structure displaying this metric.
    """
    # List of months in order
    month_columns = [
        'Apr 2024', 'May 2024', 'Jun 2024', 'Jul 2024', 'Aug 2024', 'Sep 2024',
        'Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025'
    ]

    # Ensure the month is valid
    if as_on_month not in month_columns:
        return f"Error: '{as_on_month}' is not a valid month."

    try:
        # Find the index of the given 'as_on_month'
        as_on_index = month_columns.index(as_on_month)

        # Filter the DataFrame up to the given month
        filtered_df = summary_df.iloc[:as_on_index + 1]

        # Calculate the average of 'Revenue per Rupee of Expense' column
        average_value = filtered_df['Revenue per Rupee of Expense'].mean()

        # Create the card HTML for display
        card_html = f"""
        <div class="card custom-card bg-info text-white mb-3">
            <div class= "card-body text-center">
                <h5 class = "card-title text-blue">Average Revenue per Rupee of Expense</h5>
                <p class = "card-value-text">₹ {average_value:.1f}</p>
            </div>
        </div>
        """

        return card_html

    except Exception as e:
        return f"Error: {str(e)}"





def position_card(receipt_backdata, expense_backdata):
    # Calculate total revenue and expenditure
    total_revenue = receipt_backdata['Actual YTD (Incurred)'].sum()
    total_expenditure = expense_backdata['Actual YTD (Incurred)'].sum()

    # Calculate profit or loss
    position_ytd = total_revenue - total_expenditure

    # Determine the card color based on profit or loss
    if position_ytd >= 0:
        average_value = "bg-success"  # Green for profit
    else:
        average_value = "bg-danger"  # Red for loss

    # Format the position_ytd value
    formatted_value = f"₹ {position_ytd:,.0f} cr"  # Format with rupee symbol, commas, and "CR"

    # Create the card HTML for display
    card_html = f"""
    <div class="card custom-card bg-info text-white mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-blue">YTD Cash <br>In-Hand</h5>
            <p class="card-value-text">{formatted_value}</p>
        </div>
    </div>
    """

    return card_html

def cash_inhand_card(receipt_backdata, expense_backdata, previous_closing):
    # Calculate total revenue and expenditure
    total_revenue = receipt_backdata['Actual YTD (Incurred)'].sum()
    total_expenditure = expense_backdata['Actual YTD (Incurred)'].sum()

    # Calculate profit or loss
    position_ytd = total_revenue - total_expenditure
    cash_inhand = previous_closing + position_ytd

    # Determine the card color based on profit or loss
    if position_ytd >= 0:
        average_value = "bg-success"  # Green for profit
    else:
        average_value = "bg-danger"  # Red for loss

    # Format the position_ytd value
    formatted_cash_inhand = f"₹ {cash_inhand:,.0f} cr"  # Format with rupee symbol, commas, and "CR"

    # Create the card HTML for display
    card_html = f"""
    <div class="card custom-card bg-info text-white mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-blue"><b>Total Cash<br>In-Hand</b></h5>
            <p class="card-value-text">{formatted_cash_inhand}</p>
        </div>
    </div>
    """

    return card_html


def revenue_gauge(df):
    # Calculate the required values
    budgeted_revenue = df['Actual Budget 2024-25'].sum()
    achieved_revenue = df['Actual YTD (Incurred)'].sum()
    target_revenue = df['Proportionate Budget YTD'].sum()
    to_achieve_revenue = budgeted_revenue - achieved_revenue

    # Calculate percentages
    achieved_percentage = (achieved_revenue / budgeted_revenue) * 100 if budgeted_revenue > 0 else 0
    target_percentage = (target_revenue / budgeted_revenue) * 100 if budgeted_revenue > 0 else 0
    to_achieve_percentage = (to_achieve_revenue / budgeted_revenue) * 100

    # Create the gauge chart
    fig = go.Figure()

    # Define tick values for 0%, achieved, target, and 100%
    tickvals = [0,
                budgeted_revenue * (achieved_percentage / 100),
                budgeted_revenue * (target_percentage / 100),
                budgeted_revenue]
    ticktext = [
        '0%',  # Start of the gauge
        f'₹ {achieved_revenue:,.0f}<br>({achieved_percentage:.0f}%)',  # Achieved Revenue with percentage
        f'₹ {target_revenue:,.0f}<br>({target_percentage:.0f}%)',  # Target Revenue with percentage
        f'₹ {budgeted_revenue:,.0f}<br>(100%)'  # End of the gauge
    ]

    # Add the gauge for achieved revenue
    fig.add_trace(go.Indicator(
        mode="gauge",
        value=achieved_revenue,
        gauge={
            'axis': {
                'range': [0, budgeted_revenue],
                'tickmode': 'array',
                'tickvals': tickvals,  # Custom tick values
                'ticktext': ticktext,  # Custom tick labels with percentages
                'tickangle': 0,
                'tickfont': {
                    'size': 12,  # Set your desired font size here
                    'color': 'black'  # Optional: set the color of the ticks
                }
            },
            'bar': {'color': "#3f37c9", 'thickness': 0.95},  # Base thickness
            'steps': [
                {'range': [0, achieved_revenue], 'color': "#3f37c9"},
                {'range': [achieved_revenue, target_revenue], 'color': "rgba(63, 55, 201, 0.3)"},  # 50% transparent
                {'range': [target_revenue, budgeted_revenue], 'color': "#ced4da"}  # Keep the rest light gray
            ],
            'threshold': {
                'line': {'color': "#495057", 'width': 3},
                'value': target_revenue
            }
        },
        number={'prefix': "₹", 'valueformat': '.0f'},
        delta={'reference': target_revenue, 'increasing': {'color': "green"}}
    ))

    # Update layout with annotations
    fig.update_layout(
        title={
            'text': "<b>Receipts YTD</b><br>INR Cr",  # Title text
            'x': 0.5,  # Positioning the title at the center
            'xanchor': 'center',  # Anchor the title to the center
            'y': 0.95,  # Positioning the title vertically
            'yanchor': 'top'  # Anchor the title to the top
        },
        width=550,  # Set width to 450 pixels
        height=500,  # Set height to 300 pixels
        margin=dict(l=60, r=70, t=40, b=80),  # Set margins

        annotations=[

            dict(
                x=0.5,
                y=0.25,
                xref='paper',
                yref='paper',
                text=f"<b>Budgeted Receipts:</b> ₹{budgeted_revenue:,.0f}<br>"
                     f"<b>Target Receipts:</b> ₹{target_revenue:,.0f} ({target_percentage:.0f}%)<br><br>"

                     f"<b>Achieved Receipts:</b> ₹{achieved_revenue:,.0f} ({achieved_percentage:.0f}%)<br>",
                showarrow=False,
                font=dict(size=13, color="black")  # Set the font size and color
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.0,  # Adjust this value to position the legend vertically
            xanchor="center",
            x=0.5
        ),
        # Set the background to be transparent
        paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent paper background
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent plot background
        xaxis=dict(
            showgrid=False,  # Hide x-axis grid
            showline=False,  # Hide x-axis line
            showticklabels=False,  # Hide x-axis tick labels
            zeroline=False  # Hide zero line
        ),
        yaxis=dict(
            showgrid=False,  # Hide y-axis grid
            showline=False,  # Hide y-axis line
            showticklabels=False,  # Hide y-axis tick labels
            zeroline=False  # Hide zero line
        )  # Hide y-axis grid
    )

    # Add legends for achieved and budgeted revenue
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color="#3f37c9", size=9),
        name=f'Achieved Revenue',
        showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color="rgba(63, 55, 201, 0.3)", size=9),
        name=f'Targeted Revenue',
        showlegend=True
    ))

    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color="#ced4da", size=9),
        name=f'Budgeted Revenue',
        showlegend=True
    ))
    # Show the figure
    return fig


def expense_gauge(df):
    # Calculate the required values
    budgeted_expense = df['Actual Budget 2024-25'].sum()
    incurred_expense = df['Actual YTD (Incurred)'].sum()
    expected_expense = df['Proportionate Budget YTD'].sum()
    to_incurred_expense = budgeted_expense - incurred_expense

    # Calculate percentages
    achieved_percentage = (incurred_expense / budgeted_expense) * 100 if budgeted_expense > 0 else 0
    target_percentage = (expected_expense / budgeted_expense) * 100 if budgeted_expense > 0 else 0
    to_achieve_percentage = (to_incurred_expense / budgeted_expense) * 100

    # Create the gauge chart
    fig = go.Figure()

    # Define tick values for 0%, achieved, target, and 100%
    tickvals = [0,
                budgeted_expense * (achieved_percentage / 100),
                budgeted_expense * (target_percentage / 100),
                budgeted_expense]
    ticktext = [
        '0%',  # Start of the gauge
        f'₹ {incurred_expense:,.0f}<br>({achieved_percentage:.0f}%)',  # Achieved Revenue with percentage
        f'₹ {expected_expense:,.0f}<br>({target_percentage:.0f}%)',  # Target Revenue with percentage
        f'₹ {budgeted_expense:,.0f}<br>(100%)'  # End of the gauge
    ]

    # Add the gauge for achieved revenue
    fig.add_trace(go.Indicator(
        mode="gauge",
        value=incurred_expense,
        gauge={
            'axis': {
                'range': [0, budgeted_expense],
                'tickmode': 'array',
                'tickvals': tickvals,  # Custom tick values
                'ticktext': ticktext,  # Custom tick labels with percentages
                'tickangle': 0,
                'tickfont': {
                    'size': 12,  # Set your desired font size here
                    'color': 'black'  # Optional: set the color of the ticks
                }
            },
            'bar': {'color': "#2c6e49", 'thickness': 0.95},  # Base thickness
            'steps': [
                {'range': [0, incurred_expense], 'color': "#3f37c9"},
                {'range': [incurred_expense, expected_expense], 'color': "rgba(44, 110, 73, 0.3)"},  # 50% transparent
                {'range': [expected_expense, budgeted_expense], 'color': "#ced4da"}  # Keep the rest light gray
            ],
            'threshold': {
                'line': {'color': "#495057", 'width': 3},
                'value': expected_expense
            }
        },
        number={'prefix': "₹", 'valueformat': '.0f'},
        delta={'reference': expected_expense, 'increasing': {'color': "green"}}
    ))

    # Update layout with annotations
    fig.update_layout(
        title={
            'text': "<b>Expense YTD</b><br>INR Cr",  # Title text
            'x': 0.5,  # Positioning the title at the center
            'xanchor': 'center',  # Anchor the title to the center
            'y': 0.95,  # Positioning the title vertically
            'yanchor': 'top'  # Anchor the title to the top
        },
        width=550,  # Set width to 450 pixels
        height=500,  # Set height to 300 pixels
        margin=dict(l=60, r=70, t=40, b=80),  # Set margins

        annotations=[

            dict(
                x=0.5,
                y=0.25,
                xref='paper',
                yref='paper',
                text=f"<b>Budgeted Expense:</b> ₹{budgeted_expense:,.0f}<br>"
                     f"<b>Expected Expense:</b> ₹{expected_expense:,.0f} ({target_percentage:.0f}%)<br><br>"

                     f"<b>Incurred Expense:</b> ₹{incurred_expense:,.0f} ({achieved_percentage:.0f}%)<br>",
                showarrow=False,
                font=dict(size=13, color="black")  # Set the font size and color
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.0,  # Adjust this value to position the legend vertically
            xanchor="center",
            x=0.5
        ),
        # Set the background to be transparent
        paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent paper background
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent plot background
        xaxis=dict(
            showgrid=False,  # Hide x-axis grid
            showline=False,  # Hide x-axis line
            showticklabels=False,  # Hide x-axis tick labels
            zeroline=False  # Hide zero line
        ),
        yaxis=dict(
            showgrid=False,  # Hide y-axis grid
            showline=False,  # Hide y-axis line
            showticklabels=False,  # Hide y-axis tick labels
            zeroline=False  # Hide zero line
        )  # Hide y-axis grid
    )

    # Add legends for achieved and budgeted revenue
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color="#2c6e49", size=9),
        name=f'Incurred Expenditure',
        showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color="rgba(44, 110, 73, 0.3)", size=9),
        name=f'Expected Expenditure',
        showlegend=True
    ))

    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(color="#ced4da", size=9),
        name=f'Budgeted Expenditure',
        showlegend=True
    ))

    # Show the figure
    return fig


def revenue_distribution_donut(df):
    # Calculate total YTD revenue
    total_ytd_revenue = df['Actual YTD (Incurred)'].sum()

    # Extract categories and values
    categories = df['Particular']
    values = df['Actual YTD (Incurred)']

    # Format values with ₹, commas, and round to 0 decimal
    formatted_values = [f"₹ {value:,.0f}" for value in values]
    # Determine the pull factor based on the value size
    pulls = [0.05 if value < (total_ytd_revenue / len(values)) else 0 for value in values]

    # Combine categories and values for the legend
    legend_labels = [f"{category}: <b>{formatted_value}</b>" for category, formatted_value in
                     zip(categories, formatted_values)]

    # Define custom colors for the pie chart
    colors = ['#0a369d', '#BBCFFF', '#4472ca', '#5e7ce2', '#1089FF', '#03256c', '#AD7BE9']

    # Create the pie chart
    fig = go.Figure(data=[go.Pie(
        labels=legend_labels,  # Use combined labels for the pie chart
        values=values,
        textinfo='percent',  # Show percentages on the pie slices
        textposition='outside',  # Position text outside the pie slices
        hole=0.4,  # For a donut chart, set this to a value between 0 and 1
        rotation=180,
        marker=dict(
            line=dict(color='#000000', width=0.3),  # Optional: add a border to the slices
            colors=colors  # Set custom colors for the pie slices
        ),
        pull=pulls,  # Apply pull to create separation for smaller angles
        textfont=dict(size=12),  # Set font size for the text
    )])

    # Update layout for size and background
    fig.update_layout(
        title={
            'text': "<b>Receipts Overhead Distribution</b><br>INR Cr",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.90,
            'yanchor': 'top'
        },
        width=550,
        height=400,
        paper_bgcolor='rgba(255, 255, 255, 0.0)',  # Set paper background to white
        showlegend=True,
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='top',  # Anchor at the bottom
            y=0.75,  # Adjust position to be below the chart
            xanchor='left',  # Center-align the legend
            x=1.25,  # Center the legend in the figure
            itemclick='toggleothers',  # Optional: allow clicking to toggle other items
            itemdoubleclick='toggle',  # Optional: allow double-clicking to toggle
            font=dict(size=12),  # Adjust legend font size
            traceorder='normal',  # Maintain the order of items

        )
    )

    return fig

def expense_distribution_donut(df):
    # Calculate total YTD expense
    total_ytd_expense = df['Actual YTD (Incurred)'].sum()
    threshold = 0.05

    # Extract categories and values
    categories = df['Particular']
    values = df['Actual YTD (Incurred)']


    # Calculate the percentage of each category
    percentages = values / 700

    # Filter out categories with percentages below the threshold (10%)
    filtered_df = df[percentages >= threshold]
    filtered_categories = filtered_df['Particular']
    filtered_values = filtered_df['Actual YTD (Incurred)']

    # Format values with ₹, commas, and round to 0 decimal
    formatted_values = [f"₹ {value:,.0f}" for value in filtered_values]

    # Define custom colors for the pie chart
    colors = ['#4b8e1b', '#2e5d1f', '#1a3d1a', '#abc32f', '#526E48']
    # Determine the pull factor based on the value size
    pulls = [0.05 if value < (total_ytd_expense / len(values)) else 0 for value in values]
     # Combine categories and values for the legend
    # Combine filtered categories and values for the legend
    legend_labels = [f"{category}: <b>{formatted_value}</b>" for category, formatted_value in
                     zip(filtered_categories, formatted_values)]

    # Create the pie chart
    fig = go.Figure(data=[go.Pie(
        labels=legend_labels,  # Use combined labels for the pie chart
        values=filtered_values,  # Use filtered values for the pie chart
        texttemplate='%{percent}',  # Custom text formatting
        customdata=formatted_values,  # Use formatted values in the custom data field
        textinfo='percent',  # Show only percentages in the chart
        textposition='outside',  # Position text outside the pie slices
        rotation=55,  # Rotate the chart to start at a specific angle
        insidetextorientation='horizontal',  # Orientation of text inside the pie
        hole=0.4,  # For a donut chart
        marker=dict(
            line=dict(color='#000000', width=0.3),  # Optional: add a border to the slices
            colors=colors  # Set custom colors for the pie slices
        ),
        textfont=dict(size=12),  # Set font size for the text
        pull=pulls  # Apply pull to create separation for smaller angles
    )])

    # Update layout for size and background
    fig.update_layout(
        title={
            'text': "<b>Expenditure Overhead Distribution</b><br>INR Cr",  # Title text
            'x': 0.5,  # Positioning the title at the center
            'xanchor': 'center',  # Anchor the title to the center
            'y': 0.90,  # Positioning the title vertically
            'yanchor': 'top'  # Anchor the title to the top
        },
        width=550,  # Set figure width
        height=450,  # Set figure height
        paper_bgcolor='rgba(255, 255, 255, 0.0)',  # Set paper background to white
        showlegend=True,  # Show legend
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='bottom',  # Position the legend at the bottom
            y=0.3,  # Move the legend below the chart
            xanchor='center',  # Center the legend horizontally
            x=1.9,  # Center the legend
            itemclick='toggleothers',  # Optional: allow clicking to toggle other items
            itemdoubleclick='toggle'  # Optional: allow double-clicking to toggle
        )
    )
    # Show the figure
    return fig


def growth_bar_chart(receipt_backdata, expense_backdata):
    # Define the columns for revenue and expenses
    revenue_columns = ['FY 2020-21', 'FY 2021-22', 'FY 2022-23', 'Actual Budget 2023-24', 'Actual Budget 2024-25']
    expense_columns = ['FY 2020-21', 'FY 2021-22', 'FY 2022-23', 'Actual Budget 2023-24', 'Actual Budget 2024-25']

    # Calculate total revenue and expenses for each year
    total_revenue = receipt_backdata[revenue_columns].sum().values
    total_expense = expense_backdata[expense_columns].sum().values

    # Calculate year-on-year growth rates for revenue starting from FY 2021-22
    revenue_growth = [(total_revenue[i] - total_revenue[i - 1]) / total_revenue[i - 1] * 100 if i > 0 else None for i in
                      range(len(total_revenue))]
    revenue_growth[0] = None  # Set growth for FY 2020-21 to None

    # Calculate year-on-year growth rates for expenses starting from FY 2021-22
    expense_growth = [(total_expense[i] - total_expense[i - 1]) / total_expense[i - 1] * 100 if i > 0 else None for i in
                      range(len(total_expense))]
    expense_growth[0] = None  # Set growth for FY 2020-21 to None

    # Prepare data for the bar chart
    years = ['FY 2021-22', 'FY 2022-23', 'Actual Budget 2023-24', 'Actual Budget 2024-25']

    # Create the bar chart
    fig = go.Figure()

    # Add revenue growth bars
    fig.add_trace(go.Bar(
        x=years,
        y=revenue_growth[1:],  # Skip the first year for growth
        name='Revenue Growth (%)',
        marker_color='#2D46B9',  # Custom color with transparency
        width=0.4,  # Reduce bar thickness
        hoverinfo='text',
        text=[f"{val:.2f}%" for val in revenue_growth[1:]],  # Show percentage on top of bars
        textposition='outside',  # Position text outside the bar
        marker=dict(line=dict(width=1, color='rgba(0, 0, 0, 0.3)'))  # Add shadow effect
    ))

    # Add expense growth bars
    fig.add_trace(go.Bar(
        x=years,
        y=expense_growth[1:],  # Skip the first year for growth
        name='Expense Growth (%)',
        marker_color='#626F47',  # Custom color with transparency
        width=0.4,  # Reduce bar thickness
        hoverinfo='text',
        text=[f"{val:.2f}%" for val in expense_growth[1:]],  # Show percentage on top of bars
        textposition='outside',  # Position text outside the bar
        marker=dict(line=dict(width=1, color='rgba(0, 0, 0, 0.3)'))  # Add shadow effect
    ))

    # Update layout with customized x-axis labels
    fig.update_layout(
        title={
            'text': "Year-on-Year Growth Rate (%) for Receipt & Expenditure",  # Title text
            'x': 0.6,  # Positioning the title at the center
            'xanchor': 'center',  # Anchor the title to the center
            'y': 0.95,  # Positioning the title vertically
            'yanchor': 'top'  # Anchor the title to the top
        },
        width=850,  # Set width to 450 pixels
        height=450,  # Set height to 300 pixels
        margin=dict(l=90, r=0, t=60, b=60),  # Set margins
        xaxis_title='Financial Year',
        yaxis_title='Growth Rate (%)',
        barmode='group',  # Group bars together
        paper_bgcolor='rgba(0,0,0,0)',  # Set background to transparent
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='bottom',  # Position the legend at the bottom
            y=-0.2,  # Move the legend below the chart
            xanchor='center',  # Center the legend horizontally
            x=0.5,  # Center the legend
            itemclick='toggleothers',  # Optional: allow clicking to toggle other items
            itemdoubleclick='toggle'  # Optional: allow double-clicking to toggle
        ),
        xaxis=dict(
            tickmode='array',
            tickvals=years,
            ticktext=['FY 2021-22', 'FY 2022-23', 'FY 2023-24', 'FY 2024-25']  # Custom labels
        ),
        yaxis=dict(
            showticklabels=False
        ),
    )

    # Show the figure
    return fig


def date_time_card():
    """
    Generates an HTML card displaying the current date and time.

    Returns:
    str: HTML string for the card.
    """
    # Get the current date and time
    now = datetime.now()
    current_date = now.strftime("%d %B %Y")  # Format: 15 November 2024
    current_time = now.strftime("%I:%M %p")  # Format: 02:30 PM

    # Create the HTML card
    card_html = f"""
    <div class="card custom-card bg-light text-dark mb-3">
        <div class="card-body text-center">
            <h5 class="card-title text-primary">Current Date and Time</h5>
            <p class="card-value-text">
                <strong>Date:</strong> {current_date}<br>
                <strong>Time:</strong> {current_time}
            </p>
        </div>
    </div>
    """
    return card_html

