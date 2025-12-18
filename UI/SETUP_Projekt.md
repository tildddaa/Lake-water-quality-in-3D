# Lake Water Quality Dashboard - User Interface Setup

## Quick Start

### Prerequisites
- Python 3.8+ installed on your system
- pip (Python package manager)

### Installation Steps

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/tildddaa/Lake-water-quality-in-3D.git
   cd Lake-water-quality-in-3D/User_Interface
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

**Example CSV structure:**
```csv
latitude,longitude,depth,pH,temperature,turbidity,dissolved_oxygen,TDS,num_sats
59.3293,18.0686,1.5,7.2,18.5,2.3,8.5,120,6
59.3294,18.0687,2.0,7.1,17.8,2.5,8.2,118,5
59.3295,18.0688,3.0,7.0,16.2,2.7,7.9,115,6
```

### Predict Page
- Train a Gaussian Process model on your data
- Configure advanced settings in sidebar:
  - **Early Stopping Patience** (1-50, default: 10) - How long to wait for improvement
  - **Validation Split Ratio** (0.1-0.5, default: 0.2) - Fraction of data for validation
  - **Multitask Kernel Rank** (1-5, default: 1) - Model complexity
- Click **"Train GP & Predict on Grid"** to generate predictions throughout the lake

### Visualization Tabs

**3D Thermal Visualization**
- Interactive 3D plot showing spatial distribution
- Blue points = training data, Red points = predictions
- Select different measurements from dropdown
- Model uncertainty metrics displayed

**Measurement vs Depth**
- Depth profile plots for each measurement
- Blue dots = training observations, Red dots = predictions
- Shaded area = 95% confidence interval

**Advanced Analysis**
- **Thermocline Detection**: Identifies temperature stratification layers with gradient analysis
- **Hypoxia Risk**: Analyzes dissolved oxygen depletion zones with adjustable threshold
- **Horizontal Gradients**: 2D temperature variation at specific depths
- **Uncertainty Summary**: Statistical distribution of prediction confidence

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'streamlit'`
- Solution: Run `pip install -r requirements.txt` again

**Issue**: App runs but data upload fails
- Solution: Verify CSV has required columns (latitude, longitude, depth)

**Issue**: Training is slow
- Solution: Normal for large datasets (>2000 points). Consider subsampling or using a more powerful machine.

**Issue**: GPS filtering removes too many points
- Solution: Check your `num_sats` column values. Only points with ≥4 satellites are kept.

## System Requirements

- **CPU**: 4+ cores recommended for faster training
- **RAM**: 8GB+ recommended for large datasets
- **GPU**: Optional (CUDA support improves training speed)
- **Browser**: Chrome, Firefox, Safari, or Edge (modern versions)

## Features

### Data Processing
- Automatic GPS quality filtering (num_sats ≥ 4)
- Lat/lon to Cartesian coordinate conversion
- Stratified train/validation splitting by depth
- Data normalization for stable training

### Model Training
- Gaussian Process regression with exact inference
- Multitask learning (predicts all measurements simultaneously)
- RBF kernel with Automatic Relevance Determination (ARD)
- Early stopping to prevent overfitting
- Full dataset retraining with optimized hyperparameters

### Predictions
- Dense 3D grid generation within lake boundaries
- Alpha-shape boundary detection for accurate lake outline
- Depth-aware predictions (respects max depth at each location)
- Uncertainty quantification for all predictions

### Analysis Tools
- Thermocline detection with Savitzky-Golay smoothing
- Hypoxia risk assessment with customizable thresholds
- Horizontal temperature gradient analysis
- Statistical uncertainty summaries

## Support

For issues or feature requests, open an issue on GitHub or contact the development team.
