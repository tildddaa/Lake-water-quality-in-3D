# Lake Water Quality Dashboard - User Interface Setup

## Quick Start

### Prerequisites
- Python 3.8+ installed on your system
- pip (Python package manager)

### Installation Steps

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lakewater-quality-3d.git
   cd lakewater-quality-3d/UI
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run Projekt.py
   ```

   The app will open in your browser at `http://localhost:8501`

## Usage

### Upload Page
- Upload a CSV file with required columns: `latitude`, `longitude`, `depth`
- Optional: `num_sats` for GPS reliability filtering
- Supported measurements: `pH`, `temperature`, `turbidity`, `dissolved_oxygen`, `TDS`

### Predict Page
- Train a Gaussian Process model on your data
- Configure advanced settings: early stopping, validation split, kernel rank
- Generate predictions on a 3D grid throughout the lake

### Advanced Analysis
- **Thermocline Detection**: Identify temperature stratification layers
- **Hypoxia Risk**: Analyze dissolved oxygen depletion zones
- **Horizontal Gradients**: 2D spatial variation analysis
- **Uncertainty Summary**: Statistical confidence metrics

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'streamlit'`
- Solution: Run `pip install -r requirements.txt` again

**Issue**: App runs but data upload fails
- Solution: Verify CSV has required columns (latitude, longitude, depth)

**Issue**: Training is slow
- Solution: This is normal for large datasets (>2000 points). Consider subsampling or using a more powerful machine.

## System Requirements

- **CPU**: 4+ cores recommended for faster training
- **RAM**: 8GB+ recommended for large datasets
- **GPU**: Optional (CUDA support improves training speed)

