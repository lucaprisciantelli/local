# Crypto Portfolio Status

A Streamlit dashboard to monitor your Bitvavo crypto portfolio.

## Setup

### Local Development

1.  **Install dependencies**:
    ```bash
    uv sync
    ```

2.  **Configure API Keys**:
    Create a `.env` file in the root directory (copy from `.env.example`) and add your Bitvavo API credentials:
    ```env
    B_API_KEY=...
    B_API_SECRET=...
    ```

3.  **Run the Streamlit app**:
    ```bash
    uv run streamlit run app.py
    ```

### Docker

1.  **Build and Run**:
    Ensure your `.env` file is configured, then run:
    ```bash
    docker compose up --build
    ```

2.  **Access**:
    Open [http://localhost:8501](http://localhost:8501) in your browser.

## Features

-   **Dashboard**: View total investment (current value), closed revenue, and open revenue.
-   **Asset Breakdown**: Filter by specific tokens or view all.
-   **Performance Visualization**: Horizontal bars showing current value and open revenue.
-   **Position Analysis**: Interactive charts showing open positions relative to current price.
