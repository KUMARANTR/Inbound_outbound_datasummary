import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
import pymysql
import Shared

sslca = 'server-ca.pem'
sslkey = 'client-key.pem'
sslcert = 'client-cert.pem'

# Function to fetch data from the MySQL table
def connect_to_database_inbound():
    connection = pymysql.connect(
        host='10.216.252.8',  #
        user=Shared.userid,
        passwd=Shared.password,
        db='client_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

    try:
        cursor = connection.cursor()
        select_query = """ SELECT DATE,LOAD_NUMBER,PO_NUMBER,SKU,Qty,DC_NAME FROM temporary_data.ALPARGATAS_2024_INBOUND_STANDARD_TESTING """
        cursor.execute(select_query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        df_inbound = pd.DataFrame(rows, columns=columns)

        print("Data fetched successfully!")
        return df_inbound

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

    finally:
        connection.close()



# Helper function to format numbers in K/M style
def format_number(value):
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f} M"
    elif value >= 1_000:
        return f"{value/1_000:.1f} K"
    else:
        return f"{value:.2f}"




####
# Inbound Volumes Calculation
def inbound_volumes(inbound_data, start_date=None, end_date=None, dc_name=None):
    try:
        # Ensure 'DATE' column is in datetime format
        if pd.api.types.is_datetime64_any_dtype(inbound_data['DATE']) == False:
            inbound_data['DATE'] = pd.to_datetime(inbound_data['DATE'])
        # Convert start_date and end_date to pandas Timestamps for correct comparison
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)

        filtered_data = inbound_data
        if start_date and end_date:
            filtered_data = filtered_data[(filtered_data['DATE'] >= start_date) & (filtered_data['DATE'] <= end_date)]
        if dc_name and dc_name != "All":
            filtered_data = filtered_data[filtered_data['DC_NAME'] == dc_name]

        days_of_data = (filtered_data['DATE'].max() - filtered_data['DATE'].min()).days
        total_ib_loads = filtered_data['LOAD_NUMBER'].nunique()
        total_orders = filtered_data['PO_NUMBER'].nunique()
        total_lines = filtered_data.shape[0]
        total_units = filtered_data['Qty'].sum()
        skus_with_movement = filtered_data['SKU'].nunique()

        total_ib_loads_formatted = format_number(total_ib_loads)
        total_orders_formatted = format_number(total_orders)
        total_lines_formatted = format_number(total_lines)
        total_units_formatted = format_number(total_units)
        skus_with_movement_formatted = format_number(skus_with_movement)

        metrics = {
            "Days of Data": days_of_data,
            "Total IB Loads": total_ib_loads_formatted,
            "Total Orders": total_orders_formatted,
            "Total Lines": total_lines_formatted,
            "Total Units": total_units_formatted,
            "SKUs with Movement": skus_with_movement_formatted
        }
        return metrics
    except KeyError as e:
        messagebox.showerror("Error", f"Missing column in inbound data: {str(e)}")
        return None

# Inbound Order Profile Calculation
def inbound_order_profile(inbound_data, start_date=None, end_date=None, dc_name=None):
    try:
        # Convert start_date and end_date to pandas Timestamps for correct comparison
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)

        filtered_data = inbound_data
        if start_date and end_date:
            filtered_data = filtered_data[(filtered_data['DATE'] >= start_date) & (filtered_data['DATE'] <= end_date)]
        if dc_name and dc_name != "All":
            filtered_data = filtered_data[filtered_data['DC_NAME'] == dc_name]

        total_units = filtered_data['Qty'].sum()
        total_lines = filtered_data.shape[0]
        total_orders = filtered_data['PO_NUMBER'].nunique()

        # Prevent division by zero
        ib_units_per_line = total_units / total_lines if total_lines > 0 else 0
        ib_lines_per_po = total_lines / total_orders if total_orders > 0 else 0
        ib_units_per_po = total_units / total_orders if total_orders > 0 else 0

        ib_units_per_line_formatted = format_number(ib_units_per_line)
        ib_lines_per_po_formatted = format_number(ib_lines_per_po)
        ib_units_per_po_formatted = format_number(ib_units_per_po)

        metrics = {
            "IB Units Per Line": ib_units_per_line_formatted,
            "IB Lines Per PO": ib_lines_per_po_formatted,
            "IB Units Per PO": ib_units_per_po_formatted
        }
        return metrics
    except KeyError as e:
        messagebox.showerror("Error", f"Missing column in inbound data: {str(e)}")
        return None


# Display function for inbound data, order profile, and the line chart
def display_inbound_summary(inbound_metrics, inbound_order_profile_metrics, inbound_data, start_date, end_date, dc_name):
    if not inbound_metrics or not inbound_order_profile_metrics:
        return

    for widget in card_frame_inbound.winfo_children():
        widget.destroy()

    def create_card(parent, metric, value, row, col):
        frame = tk.Frame(parent, relief='solid', borderwidth=1, padx=5, pady=5, bg='white')
        frame.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
        frame.grid(row=row, column=col, padx=5, pady=5, ipadx=5, ipady=5)
        label_title = tk.Label(frame, text=metric, font=('Arial', 10, 'bold'))
        label_title.pack(side='top', anchor='center')

        label_value = tk.Label(frame, text=str(value), font=('Arial', 10))
        label_value.pack(side='top', anchor='center')

    inbound_volumes_label = tk.Label(card_frame_inbound, text="Inbound Volumes", font=('Arial', 14, 'bold'), anchor='w')
    inbound_volumes_label.grid(row=0, column=0, columnspan=6, pady=10, sticky='w')

    inbound_order_profile_label = tk.Label(card_frame_inbound, text="Inbound Order Profile", font=('Arial', 14, 'bold'), anchor='w')
    inbound_order_profile_label.grid(row=0, column=6, columnspan=3, pady=10, sticky='w')

    col = 0
    for metric, value in inbound_metrics.items():
        create_card(card_frame_inbound, metric, value, 1, col)
        col += 1

    col = 6
    for metric, value in inbound_order_profile_metrics.items():
        create_card(card_frame_inbound, metric, value, 1, col)
        col += 1



# Function to update metrics and line chart based on filters
def update_metrics_on_filter_change(inbound_data, start_date, end_date, dc_name):
    # Convert dates to pandas Timestamps
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Fetch metrics and display the summary
    inbound_metrics = inbound_volumes(inbound_data, start_date, end_date, dc_name)
    inbound_order_profile_metrics = inbound_order_profile(inbound_data, start_date, end_date, dc_name)
    display_inbound_summary(inbound_metrics, inbound_order_profile_metrics, inbound_data, start_date, end_date, dc_name)
##############new function inbound onchange ################
def on_date_change_inbound(event=None):
    start_date = order_start_date_entry.get_date()
    end_date = order_end_date_entry.get_date()  # Corrected to fetch from order_end_date_entry

    # Ensure both dates are valid
    if start_date and end_date:
        update_metrics_on_filter_change(inbound_data, start_date, end_date, dc_filter_inbound.get())
##########new function inbound onchange ################
# Function to fetch distinct DC names Inbound from the database
def get_distinct_dc_names():
    try:
        # Set up your database connection (replace with your actual connection parameters)
        conn = pymysql.connect(
        host='10.216.252.8',  #
        user=Shared.userid,
        passwd=Shared.password,
        db='temporary_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

        # Create a cursor to execute the query
        cursor = conn.cursor()

        # SQL query to get distinct DC_NAME
        query = "SELECT DISTINCT DC_NAME FROM temporary_data.ALPARGATAS_2024_INBOUND_STANDARD_TESTING"
        cursor.execute(query)

        # Fetch all distinct DC_NAME values from the result
        dc_names = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Extract the DC names from the result tuples and add "All" at the beginning
        dc_values = ["All"] + [dc[0] for dc in dc_names]
        return dc_values

    except pymysql.Error as e:
        print(f"Error: {e}")
        return ["All"]  # Return "All" in case of error



# Function to initialize the filter for DC name Inbound
def create_dc_filter(parent_frame):
    global dc_filter_inbound
    # dc_values = ["All"] + list(inbound_data['DC_NAME'].unique())  # Add "All" to the unique DC names
    # Create a label for the "Inbound Data Summary" heading
    heading_label = ttk.Label(parent_frame, text="Inbound Data Summary", font=('Arial', 14, 'bold'),background="#FF3B00", foreground="white")
    heading_label.pack(side="top", pady=(10, 0))  # Add padding at the top for spacing

    # Add a blank line (optional for extra spacing)
    spacer_label = ttk.Label(parent_frame, text="")
    spacer_label.pack(side="top", pady=(5, 5))  # Add vertical padding to create space
    dc_label_inbound = ttk.Label(parent_frame, text="DC NAME", font=('Arial', 10))
    dc_label_inbound.pack(side="left", padx=10)
    dc_values = get_distinct_dc_names()
    dc_filter_inbound = ttk.Combobox(parent_frame, values=dc_values, state='readonly', font=('Arial', 10))
    dc_filter_inbound.set("All")  # Set the default value to "All"
    # dc_filter.pack(side="left", padx=10)
    # Position DC filter in the grid after inbound order profile
    # dc_filter_inbound.grid(row=0, column=10, columnspan=1, pady=10, sticky='w')
    dc_filter_inbound.pack(side="left", padx=10)
    # Bind event to update the metrics on DC selection change
    dc_filter_inbound.bind("<<ComboboxSelected>>", lambda event: update_metrics_on_filter_change(inbound_data, order_start_date_entry.get_date(), order_end_date_entry.get_date(), dc_filter_inbound.get()))

# Function to fetch min and max dates from the database
def fetch_min_max_dates_inbound():
    global min_date_sql_inbound, max_date_sql_inbound
    connection = pymysql.connect(
        host='10.216.252.8',
        user=Shared.userid,
        passwd=Shared.password,
        db='client_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

    try:
        cursor = connection.cursor()
        select_query = """SELECT MIN(DATE), MAX(DATE) FROM temporary_data.ALPARGATAS_2024_INBOUND_STANDARD_TESTING"""
        cursor.execute(select_query)
        min_date_sql_inbound, max_date_sql_inbound = cursor.fetchone()

        # Validate data
        if min_date_sql_inbound and max_date_sql_inbound:
            min_date_sql_inbound = pd.Timestamp(min_date_sql_inbound)
            max_date_sql_inbound = pd.Timestamp(max_date_sql_inbound)
            print(f"Data fetched successfully! Min date: {min_date_sql_inbound}, Max date: {max_date_sql_inbound}")
        else:
            print("No valid date data fetched!")
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
    finally:
        connection.close()



# Function to fetch data from the MySQL table
def connect_to_database_outbound():
    connection = pymysql.connect(
        host='10.216.252.8',  #
        user=Shared.userid,
        passwd=Shared.password,
        db='client_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

    try:
        cursor = connection.cursor()
        select_query = """ SELECT DATE,ORDER_NUMBER,SKU,Qty,DC_NAME,BUSINESSUNIT,ORDERTYPE FROM temporary_data.ALPARGATAS_2024_OUTBOUND_STANDARD_TESTING """
        cursor.execute(select_query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        df_outbound = pd.DataFrame(rows, columns=columns)

        print("Data fetched successfully!")
        return df_outbound

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

    finally:
        connection.close()


# Outbound Volumes Calculation
def outbound_volumes(outbound_data, start_date=None, end_date=None, dc_name=None, bu_name=None, channel_name=None):
    try:
        # Ensure 'DATE' column is in datetime format
        if pd.api.types.is_datetime64_any_dtype(outbound_data['DATE']) == False:
            outbound_data['DATE'] = pd.to_datetime(outbound_data['DATE'])
        # Convert start_date and end_date to pandas Timestamps for correct comparison
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)

        filtered_data = outbound_data
        if start_date and end_date:
            filtered_data = filtered_data[(filtered_data['DATE'] >= start_date) & (filtered_data['DATE'] <= end_date)]
        if dc_name and dc_name != "All":
            filtered_data = filtered_data[filtered_data['DC_NAME'] == dc_name]
        if bu_name and bu_name != "All":
            filtered_data = filtered_data[filtered_data['BUSINESSUNIT'] == bu_name]
        if channel_name and channel_name != "All":
            filtered_data = filtered_data[filtered_data['ORDERTYPE'] == channel_name]

        days_of_data = (filtered_data['DATE'].max() - filtered_data['DATE'].min()).days
        total_orders = filtered_data['ORDER_NUMBER'].nunique()
        total_lines = filtered_data.shape[0]
        total_units = filtered_data['Qty'].sum()
        skus_with_movement = filtered_data['SKU'].nunique()

        total_orders_formatted = format_number(total_orders)
        total_lines_formatted = format_number(total_lines)
        total_units_formatted = format_number(total_units)
        skus_with_movement_formatted = format_number(skus_with_movement)

        metrics = {
            "Days of Data": days_of_data,
            "Total Orders": total_orders_formatted,
            "Total Lines": total_lines_formatted,
            "Total Units": total_units_formatted,
            "SKUs with Movement": skus_with_movement_formatted
        }
        return metrics
    except KeyError as e:
        messagebox.showerror("Error", f"Missing column in outbound data: {str(e)}")
        return None

# Outbound Order Profile Calculation
def outbound_order_profile(outbound_data, start_date=None, end_date=None, dc_name=None, bu_name=None, channel_name=None):
    try:
        # Convert start_date and end_date to pandas Timestamps for correct comparison
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)

        filtered_data = outbound_data
        if start_date and end_date:
            filtered_data = filtered_data[(filtered_data['DATE'] >= start_date) & (filtered_data['DATE'] <= end_date)]
        if dc_name and dc_name != "All":
            filtered_data = filtered_data[filtered_data['DC_NAME'] == dc_name]
        if bu_name and bu_name != "All":
            filtered_data = filtered_data[filtered_data['BUSINESSUNIT'] == bu_name]
        if channel_name and channel_name != "All":
            filtered_data = filtered_data[filtered_data['ORDERTYPE'] == channel_name]

        total_units = filtered_data['Qty'].sum()
        total_lines = filtered_data.shape[0]
        total_orders = filtered_data['ORDER_NUMBER'].nunique()

        # Prevent division by zero
        ob_units_per_line = total_units / total_lines if total_lines > 0 else 0
        ob_lines_per_po = total_lines / total_orders if total_orders > 0 else 0
        ob_units_per_po = total_units / total_orders if total_orders > 0 else 0

        ob_units_per_line_formatted = format_number(ob_units_per_line)
        ob_lines_per_po_formatted = format_number(ob_lines_per_po)
        ob_units_per_po_formatted = format_number(ob_units_per_po)

        metrics = {
            "OB Units Per Line": ob_units_per_line_formatted,
            "OB Lines Per PO": ob_lines_per_po_formatted,
            "OB Units Per PO": ob_units_per_po_formatted
        }
        return metrics
    except KeyError as e:
        messagebox.showerror("Error", f"Missing column in outbound data: {str(e)}")
        return None


# Display function for outbound data and outbound order profile
def display_outbound_summary(outbound_metrics, outbound_order_profile_metrics,outbound_data, start_date, end_date, dc_name,bu_name,channel_name):
    if not outbound_metrics or not outbound_order_profile_metrics:
        return

    for widget in card_frame_outbound.winfo_children():
        widget.destroy()

    def create_card(parent, metric, value, row, col):
        frame = tk.Frame(parent, relief='solid', borderwidth=1, padx=5, pady=5, bg='white')
        frame.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
        frame.grid(row=row, column=col, padx=5, pady=5, ipadx=5, ipady=5)

        label_title = tk.Label(frame, text=metric, font=('Arial', 10, 'bold'))
        label_title.pack(side='top', anchor='center')

        label_value = tk.Label(frame, text=str(value), font=('Arial', 10))
        label_value.pack(side='top', anchor='center')

    outbound_volumes_label = tk.Label(card_frame_outbound, text="Outbound Volumes", font=('Arial', 14, 'bold'), anchor='w')
    outbound_volumes_label.grid(row=0, column=0, columnspan=6, pady=10, sticky='w')

    outbound_order_profile_label = tk.Label(card_frame_outbound, text="Outbound Order Profile", font=('Arial', 14, 'bold'), anchor='w')
    outbound_order_profile_label.grid(row=0, column=6, columnspan=3, pady=10, sticky='w')

    col = 0
    for metric, value in outbound_metrics.items():
        create_card(card_frame_outbound, metric, value, 1, col)
        col += 1

    col = 6
    for metric, value in outbound_order_profile_metrics.items():
        create_card(card_frame_outbound, metric, value, 1, col)
        col += 1




# Function to update metrics based on outbound data filters
def update_outbound_metrics_on_filter_change(outbound_data, start_date, end_date, dc_name, bu_name, channel_name):
    outbound_metrics = outbound_volumes(outbound_data, start_date, end_date, dc_name, bu_name, channel_name)
    outbound_order_profile_metrics = outbound_order_profile(outbound_data, start_date, end_date, dc_name, bu_name, channel_name)
    display_outbound_summary(outbound_metrics, outbound_order_profile_metrics,outbound_data, start_date, end_date, dc_name,bu_name,channel_name)
# Function to fetch distinct DC names outbound from the database
def get_distinct_dc_names_outbound():
    try:
        # Set up your database connection (replace with your actual connection parameters)
        conn = pymysql.connect(
        host='10.216.252.8',  #
        user=Shared.userid,
        passwd=Shared.password,
        db='temporary_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

        # Create a cursor to execute the query
        cursor = conn.cursor()

        # SQL query to get distinct DC_NAME
        query = "SELECT DISTINCT DC_NAME FROM temporary_data.ALPARGATAS_2024_OUTBOUND_STANDARD_TESTING"
        cursor.execute(query)

        # Fetch all distinct DC_NAME outbound values from the result
        dc_names_outbound = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Extract the DC names outbound from the result tuples and add "All" at the beginning
        dc_values_outbound = ["All"] + [dc[0] for dc in dc_names_outbound]
        return dc_values_outbound

    except pymysql.Error as e:
        print(f"Error: {e}")
        return ["All"]  # Return "All" in case of error


# Function to initialize the filter for DC OUTBOUND
def create_dc_filter_outbound(parent_frame):
    global dc_filter
    # dc_values = ["All"] + list(outbound_data['DC_NAME'].unique())  # Add "All" to the unique DC names
    # Create a label for the "Inbound Data Summary" heading
    heading_label_outbound = ttk.Label(parent_frame, text="Outbound Data Summary", font=('Arial', 14, 'bold'),background="#FF3B00", foreground="white")
    heading_label_outbound.pack(side="top", pady=(10, 0))  # Add padding at the top for spacing

    # Add a blank line (optional for extra spacing)
    spacer_label_outbound = ttk.Label(parent_frame, text="")
    spacer_label_outbound.pack(side="top", pady=(5, 5))  # Add vertical padding to create space
    # Create a label for DC NAME
    dc_label_outbound = ttk.Label(parent_frame, text="DC NAME", font=('Arial', 10))
    dc_label_outbound.pack(side="left", padx=10)
    dc_values_outbound = get_distinct_dc_names_outbound()
    dc_filter = ttk.Combobox(parent_frame, values=dc_values_outbound, state='readonly', font=('Arial', 10))
    dc_filter.set("All")  # Set the default value to "All"
    dc_filter.pack(side="left", padx=10)

    # Bind event to update the metrics on DC selection change
    dc_filter.bind("<<ComboboxSelected>>", lambda event: update_outbound_metrics_on_filter_change(outbound_data,order_start_date_entry_outbound.get_date(), order_end_date_entry_outbound.get_date(), dc_filter.get(), bu_filter.get(), channel_filter.get()))

def get_distinct_bu_filter_outbound():
    try:
        # Set up your database connection (replace with your actual connection parameters)
        conn = pymysql.connect(
        host='10.216.252.8',  #
        user=Shared.userid,
        passwd=Shared.password,
        db='temporary_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

        # Create a cursor to execute the query
        cursor = conn.cursor()

        # SQL query to get distinct BU_NAME
        query = "SELECT DISTINCT BUSINESSUNIT FROM temporary_data.ALPARGATAS_2024_OUTBOUND_STANDARD_TESTING"
        cursor.execute(query)

        # Fetch all distinct BUSINESSUNIT outbound values from the result
        bu_names_outbound = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Extract the BUSINESSUNIT names outbound from the result tuples and add "All" at the beginning
        bu_values = ["All"] + [dc[0] for dc in bu_names_outbound]
        return bu_values

    except pymysql.Error as e:
        print(f"Error: {e}")
        return ["All"]  # Return "All" in case of error

# Outbound filter for BU
def create_bu_filter(parent_frame):
    global bu_filter
    # bu_values = ["All"] + list(outbound_data['BUSINESSUNIT'].unique())
    bu_label = ttk.Label(parent_frame, text="BUSINESSUNIT", font=('Arial', 10))
    bu_label.pack(side="left", padx=10)
    bu_values = get_distinct_bu_filter_outbound()
    bu_filter = ttk.Combobox(parent_frame, values=bu_values, state='readonly', font=('Arial', 10))
    bu_filter.set("All")  # Set default value
    bu_filter.pack(side="left", padx=10)

    # Bind event to update the metrics on BU selection change
    bu_filter.bind("<<ComboboxSelected>>", lambda event: update_outbound_metrics_on_filter_change(outbound_data, order_start_date_entry_outbound.get_date(), order_end_date_entry_outbound.get_date(), dc_filter.get(), bu_filter.get(), channel_filter.get()))
def get_distinct_channel_filter_outbound():
    try:
        # Set up your database connection (replace with your actual connection parameters)
        conn = pymysql.connect(
        host='10.216.252.8',  #
        user=Shared.userid,
        passwd=Shared.password,
        db='temporary_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

        # Create a cursor to execute the query
        cursor = conn.cursor()

        # SQL query to get distinct channel_NAME
        query = "SELECT DISTINCT ORDERTYPE FROM temporary_data.ALPARGATAS_2024_OUTBOUND_STANDARD_TESTING"
        cursor.execute(query)

        # Fetch all distinct ORDERTYPE outbound values from the result
        channel_names_outbound = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Extract the channel names outbound from the result tuples and add "All" at the beginning
        channel_values = ["All"] + [dc[0] for dc in channel_names_outbound]
        return channel_values

    except pymysql.Error as e:
        print(f"Error: {e}")
        return ["All"]  # Return "All" in case of error

# Outbound filter for Channel
def create_channel_filter(parent_frame):
    global channel_filter
    # channel_values = ["All"] + list(outbound_data['ORDERTYPE'].unique())
    # Create a label for DC NAME
    channel_label = ttk.Label(parent_frame, text="ORDERTYPE", font=('Arial', 10))
    channel_label.pack(side="left", padx=10)
    channel_values = get_distinct_channel_filter_outbound()
    channel_filter = ttk.Combobox(parent_frame, values=channel_values, state='readonly', font=('Arial', 10))
    channel_filter.set("All")  # Set default value
    channel_filter.pack(side="left", padx=10)

    # Bind event to update the metrics on Channel selection change
    channel_filter.bind("<<ComboboxSelected>>", lambda event: update_outbound_metrics_on_filter_change(outbound_data, order_start_date_entry_outbound.get_date(),order_end_date_entry_outbound.get_date(), dc_filter.get(), bu_filter.get(), channel_filter.get()))


# Function to create a scrollable frame
def create_scrollable_frame(parent):
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return scrollable_frame


#############OUTBOUND_FUNCTION##################
##########new function OUTBOUND onchange ################
# Function to fetch min and max dates from the database////Minimum /maximum dates OUTBOUND dates
def fetch_min_max_dates_outbound():
    global min_date_sql_outbound, max_date_sql_outbound
    connection = pymysql.connect(
        host='10.216.252.8',
        user=Shared.userid,
        passwd=Shared.password,
        db='client_data',
        port=3306,
        ssl_ca=sslca,
        ssl_key=sslkey,
        ssl_cert=sslcert
    )

    try:
        cursor = connection.cursor()
        select_query = """SELECT MIN(DATE), MAX(DATE) FROM temporary_data.ALPARGATAS_2024_OUTBOUND_STANDARD_TESTING"""
        cursor.execute(select_query)
        min_date_sql_outbound, max_date_sql_outbound = cursor.fetchone()

        # Validate data
        if min_date_sql_outbound and max_date_sql_outbound:
            min_date_sql_outbound = pd.Timestamp(min_date_sql_outbound)
            max_date_sql_outbound = pd.Timestamp(max_date_sql_outbound)
            print(f"Data fetched successfully! Min date: {min_date_sql_outbound}, Max date: {max_date_sql_outbound}")
        else:
            print("No valid date data fetched!")
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
    finally:
        connection.close()
#############################
##############new function inbound onchange ################
def on_date_change_outbound(event=None):
    start_date_outbound = order_start_date_entry_outbound.get_date()
    end_date_outbound = order_end_date_entry_outbound.get_date()  # Corrected to fetch from order_end_date_entry

    # Ensure both dates are valid
    if start_date_outbound and end_date_outbound:
        # update_metrics_on_filter_change(inbound_data, start_date, end_date, dc_filter_inbound.get())
        update_outbound_metrics_on_filter_change(outbound_data, start_date_outbound, end_date_outbound, dc_filter.get(), bu_filter.get(), channel_filter.get())

########################export
def convert_abbreviated_value(value):
    """Convert a value like '4.5 K' or '1.56 M' into a full numeric value."""
    if isinstance(value, str):
        if 'K' in value:
            return float(value.replace('K', '').strip()) * 1_000
        elif 'M' in value:
            return float(value.replace('M', '').strip()) * 1_000_000
    return value

def convert_abbreviated_value_outbound(value):
    """Convert a value like '4.5 K' or '1.56 M' into a full numeric value."""
    if isinstance(value, str):
        if 'K' in value:
            return float(value.replace('K', '').strip()) * 1_000
        elif 'M' in value:
            return float(value.replace('M', '').strip()) * 1_000_000
    return value

# def export_inbound_outbound_data(inbound_metrics, inbound_order_profile_metrics, outbound_metrics, outbound_order_profile_metrics, inbound_dc_name,outbound_dc_name, bu_name, channel_name):
#     try:
#         # Export Inbound Data
#         inbound_data_to_export = {
#             "DC_NAME": [inbound_dc_name],
#             "Days of Data": [inbound_metrics["Days of Data"]],
#             "Total IB Loads": [convert_abbreviated_value(inbound_metrics["Total IB Loads"])],
#             "Total Orders": [convert_abbreviated_value(inbound_metrics["Total Orders"])],
#             "Total Lines": [convert_abbreviated_value(inbound_metrics["Total Lines"])],
#             "Total Units": [convert_abbreviated_value(inbound_metrics["Total Units"])],
#             "SKUs with Movement": [convert_abbreviated_value(inbound_metrics["SKUs with Movement"])],
#             "IB Units Per Line": [inbound_order_profile_metrics["IB Units Per Line"]],
#             "IB Lines Per PO": [inbound_order_profile_metrics["IB Lines Per PO"]],
#             "IB Units Per PO": [convert_abbreviated_value(inbound_order_profile_metrics["IB Units Per PO"])]
#         }
#
#         df_inbound = pd.DataFrame(inbound_data_to_export)
#         inbound_file_name = f'inbound_data_summary_{inbound_dc_name}.csv'
#         df_inbound.to_csv(inbound_file_name, index=False)
#
#         # Export Outbound Data
#         outbound_data_to_export = {
#             "DC_NAME": [outbound_dc_name],
#             "BUSINESSUNIT": [bu_name],
#             "ORDERTYPE": [channel_name],
#             "Days of Data": [outbound_metrics["Days of Data"]],
#             "Total Orders": [convert_abbreviated_value_outbound(outbound_metrics["Total Orders"])],
#             "Total Lines": [convert_abbreviated_value_outbound(outbound_metrics["Total Lines"])],
#             "Total Units": [convert_abbreviated_value_outbound(outbound_metrics["Total Units"])],
#             "SKUs with Movement": [convert_abbreviated_value_outbound(outbound_metrics["SKUs with Movement"])],
#             "OB Units Per Line": [outbound_order_profile_metrics["OB Units Per Line"]],
#             "OB Lines Per PO": [outbound_order_profile_metrics["OB Lines Per PO"]],
#             "OB Units Per PO": [convert_abbreviated_value_outbound(outbound_order_profile_metrics["OB Units Per PO"])]
#         }
#
#         df_outbound = pd.DataFrame(outbound_data_to_export)
#         outbound_file_name = f'outbound_data_summary_{outbound_dc_name}.csv'
#         df_outbound.to_csv(outbound_file_name, index=False)
#
#         messagebox.showinfo("Success", f"Both Inbound and Outbound data exported successfully!")
#     except Exception as e:
#         messagebox.showerror("Error", f"Failed to export data: {str(e)}")
#
import time

def export_inbound_outbound_data(inbound_metrics, inbound_order_profile_metrics, outbound_metrics, outbound_order_profile_metrics, inbound_dc_name, outbound_dc_name, bu_name, channel_name):
    try:
        # Get current timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Export Inbound Data
        inbound_data_to_export = {
            "DC_NAME": [inbound_dc_name],
            "Days of Data": [inbound_metrics["Days of Data"]],
            "Total IB Loads": [convert_abbreviated_value(inbound_metrics["Total IB Loads"])],
            "Total Orders": [convert_abbreviated_value(inbound_metrics["Total Orders"])],
            "Total Lines": [convert_abbreviated_value(inbound_metrics["Total Lines"])],
            "Total Units": [convert_abbreviated_value(inbound_metrics["Total Units"])],
            "SKUs with Movement": [convert_abbreviated_value(inbound_metrics["SKUs with Movement"])],
            "IB Units Per Line": [inbound_order_profile_metrics["IB Units Per Line"]],
            "IB Lines Per PO": [inbound_order_profile_metrics["IB Lines Per PO"]],
            "IB Units Per PO": [convert_abbreviated_value(inbound_order_profile_metrics["IB Units Per PO"])]
        }

        df_inbound = pd.DataFrame(inbound_data_to_export)
        inbound_file_name = f'inbound_data_summary_{inbound_dc_name}_{timestamp}.csv'
        df_inbound.to_csv(inbound_file_name, index=False)

        # Export Outbound Data
        outbound_data_to_export = {
            "DC_NAME": [outbound_dc_name],
            "BUSINESSUNIT": [bu_name],
            "ORDERTYPE": [channel_name],
            "Days of Data": [outbound_metrics["Days of Data"]],
            "Total Orders": [convert_abbreviated_value_outbound(outbound_metrics["Total Orders"])],
            "Total Lines": [convert_abbreviated_value_outbound(outbound_metrics["Total Lines"])],
            "Total Units": [convert_abbreviated_value_outbound(outbound_metrics["Total Units"])],
            "SKUs with Movement": [convert_abbreviated_value_outbound(outbound_metrics["SKUs with Movement"])],
            "OB Units Per Line": [outbound_order_profile_metrics["OB Units Per Line"]],
            "OB Lines Per PO": [outbound_order_profile_metrics["OB Lines Per PO"]],
            "OB Units Per PO": [convert_abbreviated_value_outbound(outbound_order_profile_metrics["OB Units Per PO"])]
        }

        df_outbound = pd.DataFrame(outbound_data_to_export)
        outbound_file_name = f'outbound_data_summary_{outbound_dc_name}_{timestamp}.csv'
        df_outbound.to_csv(outbound_file_name, index=False)

        messagebox.showinfo("Success", f"Both Inbound and Outbound data exported successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {str(e)}")

# def handle_export(inbound_data, outbound_data, start_date, end_date, start_date_outbound, end_date_outbound, dc_name, bu_name, channel_name):
#     # Step 1: Calculate inbound metrics and order profile
#     inbound_metrics = inbound_volumes(inbound_data, start_date, end_date, dc_name)
#     inbound_order_profile_metrics = inbound_order_profile(inbound_data, start_date, end_date, dc_name)
#
#     # Step 2: Calculate outbound metrics and order profile
#     outbound_metrics = outbound_volumes(outbound_data, start_date_outbound, end_date_outbound, dc_name, bu_name, channel_name)
#     outbound_order_profile_metrics = outbound_order_profile(outbound_data, start_date_outbound, end_date_outbound, dc_name, bu_name,
#                                                             channel_name)
#
#     # Step 3: Ensure metrics are not None
#     if inbound_metrics and inbound_order_profile_metrics and outbound_metrics and outbound_order_profile_metrics:
#         # Step 4: Call the export function with the computed metrics
#         export_inbound_outbound_data(
#             inbound_metrics,
#             inbound_order_profile_metrics,
#             outbound_metrics,
#             outbound_order_profile_metrics,
#             dc_name,
#             bu_name,
#             channel_name
#         )
#     else:
#         messagebox.showerror("Error", "Failed to compute necessary metrics for export.")

########################
def handle_export(inbound_data, outbound_data, start_date, end_date, start_date_outbound, end_date_outbound, inbound_dc_name, bu_name, channel_name, outbound_dc_name):
    # Step 1: Calculate inbound metrics and order profile
    inbound_metrics = inbound_volumes(inbound_data, start_date, end_date, inbound_dc_name)
    inbound_order_profile_metrics = inbound_order_profile(inbound_data, start_date, end_date, inbound_dc_name)

    # Step 2: Calculate outbound metrics and order profile
    outbound_metrics = outbound_volumes(outbound_data, start_date_outbound, end_date_outbound, outbound_dc_name, bu_name, channel_name)
    outbound_order_profile_metrics = outbound_order_profile(outbound_data, start_date_outbound, end_date_outbound, outbound_dc_name, bu_name, channel_name)

    # Step 3: Ensure metrics are not None
    if inbound_metrics and inbound_order_profile_metrics and outbound_metrics and outbound_order_profile_metrics:
        # Step 4: Call the export function with the computed metrics
        export_inbound_outbound_data(
            inbound_metrics,
            inbound_order_profile_metrics,
            outbound_metrics,
            outbound_order_profile_metrics,
            inbound_dc_name,  # Inbound DC Name
            outbound_dc_name,  # Outbound DC Name
            bu_name,
            channel_name

        )
    else:
        messagebox.showerror("Error", "Failed to compute necessary metrics for export.")

##########
# Main function to create the notebook page
def create_notebook_page_inbound_outbound():
    global card_frame_inbound, card_frame_outbound, inbound_data, outbound_data
    global card_frame_inbound, filter_frame_inbound, card_frame_outbound, filter_frame_outbound, root, chart_frame_inbound
    global selected_start_date, selected_end_date, selected_start_date_outbound, selected_end_date_outbound
    global inbound_data, outbound_data, order_start_date_entry, order_end_date_entry, min_date_sql_inbound, max_date_sql_inbound, min_date_sql_outbound, max_date_sql_outbound, order_start_date_entry_outbound, order_end_date_entry_outbound
    global export_button_frame_inbound,export_button_frame_outbound
    # global inbound_metrics, inbound_order_profile_metrics, outbound_metrics, outbound_order_profile_metrics, dc_name,bu_name, channel_name

    # Initialize root window
    root = tk.Tk()
    root.title("Summary Page")
    root.geometry("1200x600")

    # Create a Notebook to hold both tabs
    notebook = ttk.Notebook(root)
    notebook.pack(side='top', fill='both', expand=True)

    # Create Inbound and Outbound Summary Tab
    summary_frame = ttk.Frame(notebook, width=800, height=1000)
    notebook.add(summary_frame, text="Inbound and Outbound Summary")
    # export button
    # Create a style for the button
    style = ttk.Style()
    style.configure('Export.TButton', background='white', foreground='#FF3B00')

    # Create the Export Button at the bottom of the summary frame
    export_button = ttk.Button(summary_frame, text="Export Data", style='Export.TButton',  # Apply the style
                               command=lambda: handle_export(
                                   inbound_data,
                                   outbound_data,
                                   order_start_date_entry.get_date(),  # Inbound Start Date
                                   order_end_date_entry.get_date(),  # Inbound End Date
                                   order_start_date_entry_outbound.get_date(),  # Outbound Start Date
                                   order_end_date_entry_outbound.get_date(),  # Outbound End Date
                                   dc_filter_inbound.get(),  # Get the selected Inbound DC name
                                   bu_filter.get(),  # Business unit filter
                                   channel_filter.get(),  # Channel filter
                                   dc_filter.get()  # Get the selected Outbound DC name
                               )
                               )
    export_button.pack(side='bottom', pady=20)

    #####################################################################
    # Load data from the inbound database
    df_inbound = connect_to_database_inbound()  # Make sure this function is defined
    if df_inbound is not None:
        inbound_data = df_inbound.copy()
        min_date_inbound = inbound_data['DATE'].min()
        max_date_inbound = inbound_data['DATE'].max()
        print(f"Inbound - Min Date: {min_date_inbound}, Max Date: {max_date_inbound}")
    # Fetch min and max order dates
    fetch_min_max_dates_inbound()  # Fetch inbound min dates and max dates from the database
    # Initialize start and end dates for inbound data
    # Ensure min_date_sql_inbound and max_date_sql_inbound are available
    if min_date_sql_inbound and max_date_sql_inbound:
        selected_start_date = min_date_sql_inbound
        selected_end_date = max_date_sql_inbound
    else:
        # Handle fallback in case no data is fetched
        selected_start_date = pd.Timestamp('2000-01-01')
        selected_end_date = pd.Timestamp('2100-01-01')

    # Create scrollable frame for inbound data
    scrollable_frame_inbound = create_scrollable_frame(summary_frame)  # Assuming you have a function to create this
    filter_frame_inbound = ttk.Frame(scrollable_frame_inbound)
    filter_frame_inbound.pack(fill='x')
    card_frame_inbound = ttk.Frame(scrollable_frame_inbound)
    card_frame_inbound.pack(fill='x', pady=10)
    # Create filters and date pickers for inbound data
    create_dc_filter(filter_frame_inbound)  # Assuming this function is defined
    ################
    ####dates min and max dates inbound
    # Create date entries for selecting date range
    order_start_date_entry = DateEntry(filter_frame_inbound, selectmode='day', year=min_date_sql_inbound.year, month=min_date_sql_inbound.month,
                                                day=min_date_sql_inbound.day, mindate=selected_start_date,
                                       maxdate=selected_end_date)
    order_start_date_entry.set_date(min_date_sql_inbound)
    order_start_date_entry_label = tk.Label(filter_frame_inbound,
                                                     text=f"From Date:")
    order_start_date_entry_label.pack(side='left', padx=10)
    order_start_date_entry.pack(side='left', padx=10)
    order_start_date_entry.bind("<<DateEntrySelected>>", on_date_change_inbound)
    order_end_date_entry = DateEntry(filter_frame_inbound, selectmode='day',year=max_date_sql_inbound.year, month=max_date_sql_inbound.month,
                                                day=max_date_sql_inbound.day, mindate=selected_start_date,
                                     maxdate=selected_end_date)
    order_end_date_entry.set_date(max_date_sql_inbound)
    order_end_date_entry_label = tk.Label(filter_frame_inbound,
                                      text=f"To Date:")
    order_end_date_entry_label.pack(side='left', padx=10)
    order_end_date_entry.pack(side='left', padx=10)
    order_end_date_entry.bind("<<DateEntrySelected>>", on_date_change_inbound)
    date_range_label_frame_inbound = tk.Frame(filter_frame_inbound)
    date_range_label_frame_inbound.pack(side='left', padx=10)
    # Add a label to display the available date range
    date_range_label_inbound = tk.Label(date_range_label_frame_inbound,
                                        text=f"Dates available from {min_date_sql_inbound.date()} to {max_date_sql_inbound.date()}")
    date_range_label_inbound.pack(side='left', padx=10)
    # Update inbound metrics
    update_metrics_on_filter_change(inbound_data, selected_start_date, selected_end_date, "All")

    # Load data from the outbound database
    df_outbound = connect_to_database_outbound()  # Make sure this function is defined
    if df_outbound is not None:
        outbound_data = df_outbound.copy()
        min_date_outbound = outbound_data['DATE'].min()
        max_date_outbound = outbound_data['DATE'].max()
        print(f"Outbound - Min Date: {min_date_outbound}, Max Date: {max_date_outbound}")
    # fetch minimum outbound and maximum outbound dates
    fetch_min_max_dates_outbound()  # Fetch outbound min dates and max dates from the database
    # Ensure min_date_sql_outbound and max_date_sql_outbound are available
    if min_date_sql_outbound and max_date_sql_outbound:
        selected_start_date_outbound = min_date_sql_outbound
        selected_end_date_outbound = max_date_sql_outbound
    else:
        # Handle fallback in case no data is fetched
        selected_start_date_outbound = pd.Timestamp('2000-01-01')
        selected_end_date_outbound = pd.Timestamp('2100-01-01')
    # Create scrollable frame for outbound data
    # scrollable_frame_outbound = create_scrollable_frame(summary_frame)
    filter_frame_outbound = ttk.Frame(scrollable_frame_inbound)
    filter_frame_outbound.pack(fill='x')
    card_frame_outbound = ttk.Frame(scrollable_frame_inbound)
    card_frame_outbound.pack(fill='x', pady=10)
    # Set up filters and date pickers for outbound data
    create_dc_filter_outbound(filter_frame_outbound)  # Assuming this function is defined
    create_bu_filter(filter_frame_outbound)  # Assuming this function is defined
    create_channel_filter(filter_frame_outbound)  # Assuming this function is defined

    ####dates min and max dates inbound
    # Create date entries for selecting date range
    order_start_date_entry_outbound = DateEntry(filter_frame_outbound, selectmode='day',
                                                year=min_date_sql_outbound.year, month=min_date_sql_outbound.month,
                                                day=min_date_sql_outbound.day, mindate=selected_start_date_outbound,
                                                maxdate=selected_end_date_outbound)
    order_start_date_entry_outbound.set_date(min_date_sql_outbound)
    order_start_date_entry_outbound_label = tk.Label(filter_frame_outbound,
                                                   text=f"From Date:")
    order_start_date_entry_outbound_label.pack(side='left', padx=10)
    order_start_date_entry_outbound.pack(side='left', padx=10)
    order_start_date_entry_outbound.bind("<<DateEntrySelected>>", on_date_change_outbound)
    order_end_date_entry_outbound = DateEntry(filter_frame_outbound, selectmode='day', year=max_date_sql_outbound.year,
                                              month=max_date_sql_outbound.month, day=max_date_sql_outbound.day,
                                              mindate=selected_start_date_outbound, maxdate=selected_end_date_outbound)
    order_end_date_entry_outbound.set_date(max_date_sql_outbound)
    order_end_date_entry_outbound_label = tk.Label(filter_frame_outbound,
                                         text=f"To Date:")
    order_end_date_entry_outbound_label.pack(side='left', padx=10)
    order_end_date_entry_outbound.pack(side='left', padx=10)
    order_end_date_entry_outbound.bind("<<DateEntrySelected>>", on_date_change_outbound)
    # date_range_label_frame_outbound = tk.Frame(filter_frame_outbound)
    # date_range_label_frame_outbound.pack(side='left', padx=10)
    # # Add a label to display the available date range
    # date_range_label_outbound = tk.Label(date_range_label_frame_outbound,
    #                                      text=f"Dates available from {min_date_sql_outbound.date()} to {max_date_sql_outbound.date()}")
    # date_range_label_outbound.pack(side='left', padx=10)
    # Update outbound metrics
    update_outbound_metrics_on_filter_change(outbound_data, selected_start_date_outbound, selected_end_date_outbound,
                                             "All", "All", "All")

    root.mainloop()

if __name__ == "__main__":
    create_notebook_page_inbound_outbound()