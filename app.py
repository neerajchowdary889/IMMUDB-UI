import streamlit as st
import pandas as pd
import json
import time
import plotly.express as px
from datetime import datetime
from Operations.Ops import ImmuDBReader, read_transactions, get_merkle_root

# Page config
st.set_page_config(
    page_title="ImmuDB Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        text-align: center;
    }
    .stat-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .stat-label {
        font-weight: bold;
        color: #555;
    }
    .stat-value {
        font-size: 1.5rem;
        color: #2c3e50;
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_transactions_stats(transactions):
    """Calculate statistics for transactions"""
    if not transactions:
        return {
            "count": 0,
            "avg_key_length": 0,
            "avg_value_length": 0,
            "largest_value": {"key": "", "size": 0},
            "common_prefixes": []
        }
    
    # Calculate statistics
    key_lengths = [len(k) for k in transactions.keys()]
    value_lengths = [len(str(v)) for v in transactions.values()]
    
    # Find common prefixes (simple approach)
    prefixes = {}
    for key in transactions.keys():
        for i in range(1, min(5, len(key))):
            prefix = key[:i]
            if prefix in prefixes:
                prefixes[prefix] += 1
            else:
                prefixes[prefix] = 1
    
    # Get top 5 prefixes
    common_prefixes = sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Find largest value
    largest_value = {"key": "", "size": 0}
    for key, value in transactions.items():
        value_size = len(str(value))
        if value_size > largest_value["size"]:
            largest_value = {"key": key, "size": value_size}
    
    return {
        "count": len(transactions),
        "avg_key_length": sum(key_lengths) / len(key_lengths) if key_lengths else 0,
        "avg_value_length": sum(value_lengths) / len(value_lengths) if value_lengths else 0,
        "largest_value": largest_value,
        "common_prefixes": common_prefixes
    }

# Initialize session state
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'reader' not in st.session_state:
    st.session_state.reader = None
if 'transactions' not in st.session_state:
    st.session_state.transactions = {}
if 'stats' not in st.session_state:
    st.session_state.stats = None

# Header
st.markdown("<h1 class='main-header'>ImmuDB Transaction Explorer</h1>", unsafe_allow_html=True)

# Sidebar - Connection Settings
with st.sidebar:
    st.header("Connection Settings")
    url = st.text_input("ImmuDB URL", value="localhost:3322")
    db_name = st.text_input("Database Name", value="defaultdb")
    
    # Connect button
    if st.button("Connect to Database"):
        with st.spinner("Connecting to ImmuDB..."):
            try:
                reader = ImmuDBReader(url, db_name).connect()
                st.session_state.reader = reader
                st.session_state.url = url
                st.session_state.db_name = db_name
                st.session_state.connected = True
                
                # Fetch initial stats when connecting
                with st.spinner("Loading database statistics..."):
                    transactions = read_transactions(url, db_name)
                    st.session_state.transactions = transactions
                    st.session_state.stats = get_transactions_stats(transactions)
                    
                st.success("Connected successfully!")
            except Exception as e:
                st.error(f"Connection failed: {e}")
                st.session_state.connected = False

    # Database info (only shown when connected)
    if st.session_state.connected:
        st.markdown("---")
        st.subheader("Database Info")
        try:
            root = get_merkle_root(url, db_name)
            st.markdown(f"**Transaction ID**: {root['txId']}")
            st.markdown(f"**Merkle Root**:")
            st.markdown(f"```{root['merkleRoot']}```")
            
            if st.session_state.stats:
                st.markdown("---")
                st.subheader("Quick Stats")
                st.markdown(f"**Total Transactions**: {st.session_state.stats['count']}")
                st.markdown(f"**Avg Key Length**: {st.session_state.stats['avg_key_length']:.2f} chars")
                st.markdown(f"**Avg Value Length**: {st.session_state.stats['avg_value_length']:.2f} chars")
        except Exception as e:
            st.error(f"Error fetching database info: {e}")

# Main content
if not st.session_state.connected:
    st.info("Please connect to an ImmuDB database using the sidebar.")
else:
    # Create tabs for different operations
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "All Transactions", "Search by Prefix", "Search by Suffix", "About"])
    
    # Tab 1: Dashboard
    with tab1:
        st.header("Database Dashboard")
        
        # Stats cards in a row
        if st.session_state.stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div class="stat-box">
                    <div class="stat-label">Total Transactions</div>
                    <div class="stat-value">{}</div>
                </div>
                """.format(st.session_state.stats["count"]), unsafe_allow_html=True)
                
            with col2:
                st.markdown("""
                <div class="stat-box">
                    <div class="stat-label">Average Key Length</div>
                    <div class="stat-value">{:.2f}</div>
                </div>
                """.format(st.session_state.stats["avg_key_length"]), unsafe_allow_html=True)
                
            with col3:
                st.markdown("""
                <div class="stat-box">
                    <div class="stat-label">Average Value Length</div>
                    <div class="stat-value">{:.2f}</div>
                </div>
                """.format(st.session_state.stats["avg_value_length"]), unsafe_allow_html=True)
            
            # Common prefixes visualization
            st.subheader("Common Key Prefixes")
            if st.session_state.stats["common_prefixes"]:
                prefixes_df = pd.DataFrame(st.session_state.stats["common_prefixes"], columns=["Prefix", "Count"])
                fig = px.bar(prefixes_df, x="Prefix", y="Count", title="Most Common Key Prefixes")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No common prefixes found.")
            
            # Largest values
            st.subheader("Largest Value")
            if st.session_state.stats["largest_value"]["key"]:
                st.markdown(f"**Key**: `{st.session_state.stats['largest_value']['key']}`")
                st.markdown(f"**Size**: {st.session_state.stats['largest_value']['size']} characters")
            else:
                st.info("No values found.")
            
            # Refresh stats button
            if st.button("Refresh Stats"):
                with st.spinner("Updating statistics..."):
                    try:
                        transactions = read_transactions(st.session_state.url, st.session_state.db_name)
                        st.session_state.transactions = transactions
                        st.session_state.stats = get_transactions_stats(transactions)
                        st.success("Statistics updated!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error updating statistics: {e}")
    
    # Tab 2: All Transactions
    with tab2:
        st.header("All Transactions")
        
        col1, col2 = st.columns(2)
        with col1:
            limit = st.slider("Max transactions to fetch", min_value=10, max_value=1000, value=100, step=10)
        
        if st.button("Fetch All Transactions", key="fetch_all"):
            with st.spinner("Fetching transactions..."):
                try:
                    transactions = read_transactions(url, db_name)
                    st.session_state.transactions = transactions
                    
                    # Show transaction count
                    st.markdown(f"### Found {len(transactions)} transactions")
                    
                    if transactions:
                        # Create a DataFrame
                        df = pd.DataFrame(list(transactions.items()), columns=['Key', 'Value'])
                        
                        # Apply limit
                        df = df.head(limit)
                        
                        # Display the data
                        st.dataframe(df, use_container_width=True)
                        
                        # Download option
                        json_data = json.dumps(transactions)
                        st.download_button(
                            label="Download as JSON",
                            data=json_data,
                            file_name="transactions.json",
                            mime="application/json"
                        )
                    else:
                        st.info("No transactions found in the database.")
                except Exception as e:
                    st.error(f"Error fetching transactions: {e}")
    
    # Tab 3: Search by Prefix
    with tab3:
        st.header("Search by Prefix")
        prefix = st.text_input("Enter prefix to search for", key="prefix_input")
        
        # Quick select common prefixes if available
        if st.session_state.stats and st.session_state.stats["common_prefixes"]:
            st.markdown("**Common prefixes:**")
            cols = st.columns(len(st.session_state.stats["common_prefixes"]))
            for i, (prefix_val, count) in enumerate(st.session_state.stats["common_prefixes"]):
                if cols[i].button(f"{prefix_val} ({count})"):
                    prefix = prefix_val
                    st.experimental_rerun()
        
        if st.button("Search by Prefix"):
            if not prefix:
                st.warning("Please enter a prefix to search for.")
            else:
                with st.spinner(f"Searching for keys with prefix '{prefix}'..."):
                    try:
                        transactions = read_transactions(url, db_name, prefix=prefix)
                        
                        # Show search results
                        st.markdown(f"### Found {len(transactions)} transactions with prefix '{prefix}'")
                        
                        if transactions:
                            # Create a DataFrame
                            df = pd.DataFrame(list(transactions.items()), columns=['Key', 'Value'])
                            
                            # Display the data
                            st.dataframe(df, use_container_width=True)
                            
                            # Download option
                            json_data = json.dumps(transactions)
                            st.download_button(
                                label="Download as JSON",
                                data=json_data,
                                file_name=f"transactions_prefix_{prefix}.json",
                                mime="application/json"
                            )
                        else:
                            st.info(f"No transactions found with prefix '{prefix}'.")
                    except Exception as e:
                        st.error(f"Error searching by prefix: {e}")
    
    # Tab 4: Search by Suffix
    with tab4:
        st.header("Search by Suffix")
        suffix = st.text_input("Enter suffix to search for", key="suffix_input")
        
        if st.button("Search by Suffix"):
            if not suffix:
                st.warning("Please enter a suffix to search for.")
            else:
                with st.spinner(f"Searching for keys with suffix '{suffix}'..."):
                    try:
                        transactions = read_transactions(url, db_name, suffix=suffix)
                        
                        # Show search results
                        st.markdown(f"### Found {len(transactions)} transactions with suffix '{suffix}'")
                        
                        if transactions:
                            # Create a DataFrame
                            df = pd.DataFrame(list(transactions.items()), columns=['Key', 'Value'])
                            
                            # Display the data
                            st.dataframe(df, use_container_width=True)
                            
                            # Download option
                            json_data = json.dumps(transactions)
                            st.download_button(
                                label="Download as JSON",
                                data=json_data,
                                file_name=f"transactions_suffix_{suffix}.json",
                                mime="application/json"
                            )
                        else:
                            st.info(f"No transactions found with suffix '{suffix}'.")
                    except Exception as e:
                        st.error(f"Error searching by suffix: {e}")
    
    # Tab 5: About
    with tab5:
        st.header("About ImmuDB Transaction Explorer")
        st.write("""
        This dashboard allows you to explore and search transactions stored in an ImmuDB database.
        
        **Features:**
        
        - Connect to any ImmuDB database
        - View database statistics and visualizations
        - View all transactions
        - Search transactions by key prefix
        - Search transactions by key suffix
        - View Merkle root for verification
        - Export results as JSON
        
        **ImmuDB** is a lightweight, high-speed immutable database with built-in cryptographic proofs.
        """)
        
        st.markdown("### How to use")
        st.write("""
        1. Enter your ImmuDB connection details in the sidebar
        2. Click 'Connect to Database'
        3. Use the tabs to view statistics, search for transactions, or export data
        4. The dashboard tab provides visual insights into your database
        """)

# Footer
st.markdown("""
<div class="footer">
    ImmuDB Transaction Explorer • Developed with Streamlit
</div>
""", unsafe_allow_html=True)