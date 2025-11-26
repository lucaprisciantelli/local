import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dotenv import dotenv_values
import os
from typing import Optional

from clients.bitvavo import BitvavoRestClient
from utils import get_portfolio, update_portfolio
from models.portfolio import Portfolio

# --- Constants ---
APP_TITLE = "Crypto Status"
LAYOUT = "wide"

COLOR_PROFIT = "#00FF00"
COLOR_LOSS = "#FF0000"
COLOR_NEUTRAL = "rgb(55, 83, 109)"
COLOR_ACCENT = "#00CC96"
COLOR_TEXT = "#fafafa"
COLOR_STEM = "gray"
COLOR_MARKER_BORDER = "DarkSlateGrey"

CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stMetric {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #464b5d;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
    }
</style>
"""

# --- Helper Functions ---
def format_currency(val: float) -> str:
    return f"€{val:,.2f}"

def render_custom_metric(label: str, value: float, color_text: bool = False) -> None:
    """Renders a custom HTML metric card to ensure consistent styling."""
    formatted_value = format_currency(value)
    color_style = ""
    if color_text:
        color = COLOR_PROFIT if value >= 0 else COLOR_LOSS
        color_style = f"color: {color};"
    
    st.markdown(f"""
    <div class="stMetric">
        <label data-testid="stMetricLabel" class="css-1" style="font-size: 14px; color: {COLOR_TEXT}; margin-bottom: 0px;">{label}</label>
        <div data-testid="stMetricValue" style="font-size: 1.7rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; {color_style}">
            {formatted_value}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Data & Logic Layers ---
class DataLoader:
    """Handles API client initialization and data fetching."""
    
    @staticmethod
    @st.cache_resource
    def get_client() -> Optional[BitvavoRestClient]:
        """Initializes and caches the Bitvavo API client."""
        config = dotenv_values()
        if not config:
            config = os.environ
        
        api_key = config.get("B_API_KEY")
        api_secret = config.get("B_API_SECRET")
        
        if not api_key or not api_secret:
            st.error("API Keys (B_API_KEY, B_API_SECRET) not found in .env or environment variables.")
            return None
            
        return BitvavoRestClient(api_key=api_key, api_secret=api_secret)

    @staticmethod
    def load_portfolio(client: BitvavoRestClient) -> None:
        """Loads portfolio into session state if not present."""
        if "portfolio" not in st.session_state:
            with st.spinner("Initializing Portfolio (fetching history)..."):
                try:
                    st.session_state.portfolio = get_portfolio(client)
                except Exception as e:
                    st.error(f"Failed to load portfolio: {e}")
                    st.stop()

    @staticmethod
    def update_portfolio(client: BitvavoRestClient) -> None:
        """Updates portfolio prices and refreshes the UI."""
        if "portfolio" in st.session_state:
            try:
                with st.spinner("Updating prices..."):
                    update_portfolio(st.session_state.portfolio, client)
                    st.success("Prices updated!")
            except Exception as e:
                st.error(f"Update failed: {e}")

class ChartFactory:
    """Generates Plotly figures for the dashboard."""
    
    @staticmethod
    def create_performance_bar_chart(df: pd.DataFrame, val_col: str, rev_col: str, title: str, height: int) -> go.Figure:
        """Creates a horizontal bar chart for asset performance with Profit/Loss overlays."""
        fig = go.Figure()
        
        # Base Value Bar (Blue)
        fig.add_trace(go.Bar(
            y=df['Token'],
            x=df[val_col],
            name='Value',
            orientation='h',
            marker_color=COLOR_NEUTRAL,
            text=df[val_col].apply(lambda x: f"€{x:,.0f}"),
            textposition='inside',
            insidetextanchor='start',
            hoverinfo='x+y+name'
        ))
        
        # Profit Segment (Green)
        df_profit = df[df[rev_col] >= 0].copy()
        if not df_profit.empty:
            fig.add_trace(go.Bar(
                y=df_profit['Token'],
                x=df_profit[rev_col],
                base=df_profit[val_col] - df_profit[rev_col],
                name='Profit',
                orientation='h',
                marker_color=COLOR_PROFIT,
                opacity=0.6,
                text=df_profit[rev_col].apply(lambda x: f"+€{x:,.0f}"),
                textposition='inside',
                hoverinfo='x+y+name'
            ))

        # Loss Segment (Red)
        df_loss = df[df[rev_col] < 0].copy()
        if not df_loss.empty:
            fig.add_trace(go.Bar(
                y=df_loss['Token'],
                x=df_loss[rev_col].abs(),
                base=df_loss[val_col],
                name='Loss',
                orientation='h',
                marker_color=COLOR_LOSS,
                opacity=0.6,
                text=df_loss[rev_col].apply(lambda x: f"-€{abs(x):,.0f}"),
                textposition='outside',
                hoverinfo='x+y+name'
            ))

        fig.update_layout(
            title=title,
            barmode='overlay',
            xaxis_title="EUR",
            yaxis_title="Token",
            template="plotly_dark",
            height=height,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig

    @staticmethod
    def create_lollipop_chart(df: pd.DataFrame, x_col: str, y_col: str, color_col: Optional[str], 
                            title: str, x_label: str, y_label: str, 
                            x_format: str = "", x_range: list = None, 
                            height: int = 600, distinct_color: Optional[str] = None) -> go.Figure:
        """Creates a lollipop (scatter + stems) chart."""
        
        hover_cols = list(df.columns)
        
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col if not distinct_color else None,
            title=title,
            labels={x_col: x_label, y_col: y_label},
            hover_data=hover_cols,
            template="plotly_dark"
        )
        
        # Style Markers
        marker_style = dict(size=12, line=dict(width=1, color=COLOR_MARKER_BORDER))
        if distinct_color:
             marker_style['color'] = distinct_color
        
        fig.update_traces(marker=marker_style)

        # Add vertical dotted lines (stems)
        shapes = [
            dict(
                type="line",
                xref="x", yref="y",
                x0=row[x_col], y0=0,
                x1=row[x_col], y1=row[y_col],
                line=dict(color=COLOR_STEM, width=1, dash="dot"),
                layer="below"
            ) for _, row in df.iterrows()
        ]
        
        fig.update_layout(shapes=shapes, height=height, yaxis_title=y_label)
        
        # Apply Axis Formatting
        if x_format:
            update_args = {'tickformat': x_format}
            if x_range:
                update_args['range'] = x_range
                update_args['autorange'] = False
            fig.update_xaxes(**update_args)
            
        return fig

# --- Main Dashboard Logic ---
class Dashboard:
    def __init__(self, client: BitvavoRestClient):
        self.client = client
        DataLoader.load_portfolio(self.client)
        self.portfolio: Portfolio = st.session_state.portfolio

    def run(self):
        self._render_top_section()
        self._render_separator()
        self._render_asset_performance()
        self._render_open_positions()

    def _render_separator(self):
        st.markdown("---")

    def _render_top_section(self):
        col_upd, col_metrics = st.columns([1, 5])
        
        with col_upd:
            st.write("") # Vertical alignment spacer
            if st.button("Update Price", use_container_width=True):
                DataLoader.update_portfolio(self.client)
        
        with col_metrics:
            m1, m2, m3 = st.columns(3)
            with m1:
                render_custom_metric("Investment (Current Value)", self.portfolio.investment)
            with m2:
                render_custom_metric("Open Revenue", self.portfolio.open_revenue, color_text=True)
            with m3:
                render_custom_metric("Closed Revenue", self.portfolio.closed_revenue, color_text=True)

    def _render_asset_performance(self):
        st.subheader("Asset Performance")
        
        assets = self.portfolio.assets
        if not assets:
            st.info("No assets to display.")
            return

        # Prepare Data for both charts
        plot_data = []
        for asset in assets:
            closed_inv = sum(p.investment for p in asset.closed_positions)
            plot_data.append({
                "Token": asset.token,
                "Open Value": asset.investment,
                "Open Revenue": asset.open_revenue,
                "Closed Cost": closed_inv,
                "Closed Revenue": asset.closed_revenue
            })
            
        df_assets = pd.DataFrame(plot_data)
        df_assets["Closed Value"] = df_assets["Closed Cost"] + df_assets["Closed Revenue"]
        df_assets = df_assets.sort_values(by="Open Value", ascending=True)
        
        # Calculate dynamic height
        chart_height = int(max(240, len(assets) * 30))
        
        col_open, col_closed = st.columns(2)
        
        with col_open:
            fig = ChartFactory.create_performance_bar_chart(
                df_assets, "Open Value", "Open Revenue", "Open Positions (Current Value)", chart_height
            )
            st.plotly_chart(fig, width='stretch')
            
        with col_closed:
            fig = ChartFactory.create_performance_bar_chart(
                df_assets, "Closed Value", "Closed Revenue", "Closed Positions (Realized Value)", chart_height
            )
            st.plotly_chart(fig, width='stretch')

    def _render_open_positions(self):
        st.subheader("Open Positions Distribution")
        
        # UI Controls
        col_filter, col_limit = st.columns([1, 3])
        with col_filter:
            options = ["All"] + self.portfolio.assets_tokens()
            selected_token = st.selectbox("Filter Token", options, index=0)
        with col_limit:
            x_max_limit = st.number_input("Max Price Distance (%)", min_value=10.0, max_value=5000.0, value=50.0, step=25.0)

        # Logic: Filter positions based on selection
        if selected_token == "All":
            positions = self.portfolio.relative_open_positions
            y_col, y_label = 'investment', 'Investment (€)'
            asset_subject = None
        else:
            asset_subject = self.portfolio.get_asset_by_token(selected_token)
            positions = asset_subject.relative_open_positions
            y_col, y_label = 'amount', f'Amount ({selected_token})'

        if not positions:
            st.info("No open positions available for the selected scope.")
            return

        df_pos = pd.DataFrame(positions)

        # 1. Relative Open Positions Chart
        fig_rel = ChartFactory.create_lollipop_chart(
            df=df_pos,
            x_col='price_distance',
            y_col=y_col,
            color_col='token',
            title="Relative Open Positions",
            x_label="Price Distance",
            y_label=y_label,
            x_format=".1%",
            x_range=[-0.05, x_max_limit / 100],
            height=600
        )
        fig_rel.add_vline(x=0, line_width=2, line_dash="dash", line_color="white", annotation_text="Current Price")
        st.plotly_chart(fig_rel, width='stretch', key="positions_chart")

        # 2. Absolute Price Distribution Chart (Only when single asset selected)
        if selected_token != "All" and asset_subject:
            st.subheader(f"{selected_token} Price Distribution")
            
            fig_abs = ChartFactory.create_lollipop_chart(
                df=df_pos,
                x_col='price',
                y_col='amount',
                color_col=None,
                title=f"{selected_token} Positions by Price",
                x_label=f'Price ({selected_token})',
                y_label='Amount',
                height=500,
                distinct_color=COLOR_ACCENT
            )
            
            current_price = asset_subject.ticker.sell_price
            fig_abs.add_vline(x=current_price, line_width=2, line_dash="dash", line_color="white", annotation_text=f"Current: €{current_price:,.2f}")
            st.plotly_chart(fig_abs, use_container_width=True, key="abs_positions_chart")

def main():
    # Page setup must be first
    st.set_page_config(layout=LAYOUT, page_title=APP_TITLE, initial_sidebar_state="collapsed")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    client = DataLoader.get_client()
    if client:
        dashboard = Dashboard(client)
        dashboard.run()

if __name__ == "__main__":
    main()
