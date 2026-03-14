# Insight Forge - Complete Architecture & Working Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [File Structure & Connections](#file-structure--connections)
4. [Data Flow Pipeline](#data-flow-pipeline)
5. [Component Deep Dive](#component-deep-dive)
6. [AI Integration](#ai-integration)
7. [Frontend Architecture](#frontend-architecture)
8. [Session Management](#session-management)
9. [Error Handling](#error-handling)
10. [Deployment Considerations](#deployment-considerations)

---

## Project Overview

**Insight Forge** is a sophisticated, AI-powered data analytics platform that transforms raw CSV/XLSX files into comprehensive business intelligence dashboards. The system combines traditional statistical analysis with modern AI capabilities to provide automated insights, visualizations, and natural language querying.

### Core Capabilities
- **Automated Data Analysis**: Statistical profiling, health scoring, outlier detection
- **AI-Powered Insights**: Executive summaries, recommendations, chart planning
- **Interactive Visualizations**: Dynamic charts with AI recommendations
- **Natural Language Q&A**: Ask questions about your data in plain English
- **Business Report Generation**: Professional HTML reports with insights
- **Data Quality Assessment**: Health scores, risk analysis, missing data detection

---

## System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services  │
│                 │    │   (Flask)      │    │                 │
│ • Dashboard UI  │◄──►│ • Routes        │◄──►│ • LLM Client    │
│ • Home Page     │    │ • Data Processing│    │ • Chart Planner │
│ • Visualizations│    │ • Session Mgmt  │    │ • Query Agent   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   Data Cache    │    │   External APIs │
│                 │    │                 │    │                 │
│ • File Upload   │    │ • Session Data  │    │ • Gemini/Other  │
│ • Queries       │    │ • Analysis      │    │ • Chart APIs    │
│ • Navigation    │    │ • Results       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Backend**: Python Flask
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **AI/ML**: Multiple LLM providers, Chart.js, Pandas, NumPy
- **Data Processing**: Pandas, NumPy, Statistical Analysis
- **Visualization**: Chart.js, Custom Dashboard Components
- **Caching**: File-based session management

---

## File Structure & Connections

### Core Application Files

#### `app.py` - Main Flask Application
**Purpose**: Central web server and request router
**Connections**:
- Imports all analysis functions from `main.py`
- Imports AI modules (`ai_chart_planner`, `ai/query_agent`)
- Imports reporting module (`reporting/report_generator`)
- Imports data processing modules (`dataset_intelligence`, `feature_importance`)
- Renders templates (`templates/dashboard.html`, `templates/home.html`)

**Key Routes**:
- `POST /analyze` - Main analysis pipeline
- `POST /ask` - Natural language Q&A
- `POST /report` - Business report generation
- `POST /report/download` - Report download

#### `main.py` - Core Data Analysis Engine
**Purpose**: Fundamental statistical analysis functions
**Connections**:
- Imported by `app.py` for core analysis
- Functions called in sequence during analysis pipeline
- No external dependencies (pure Python/NumPy/Pandas)

**Key Functions**:
- `basic_overview()` - Row/column counts
- `missing_overview()` - Missing data analysis
- `column_types()` - Data type classification
- `healthy()` - Data quality checks
- `simple_stats()` - Statistical summaries
- `detect_outliers()` - Outlier detection
- `overall_dataset_health()` - Health scoring
- `column_risk_scores()` - Risk assessment
- `generate_chart_data()` - Chart data preparation

### AI Intelligence Layer

#### `ai_chart_planner.py` - AI Chart Recommendation
**Purpose**: Uses AI to determine optimal chart types and generate business-focused visualizations
**Connections**:
- Called by `app.py` during analysis pipeline
- Uses `llm_client.py` for AI communication
- Receives processed data from analysis pipeline
- Returns structured chart recommendations

**Two-Phase Process**:
1. **Dataset Classification**: Identifies domain (Sales, HR, Financial, etc.)
2. **Chart Generation**: Creates 8-12 business-focused charts with insights

#### `ai/query_agent.py` - Natural Language Q&A
**Purpose**: Enables users to ask questions about their data in plain English
**Connections**:
- Called via `/ask` route in `app.py`
- Uses `llm_client.py` for AI responses
- Accesses cached analysis data for context
- Can generate charts as part of responses

#### `llm_client.py` - LLM Abstraction Layer
**Purpose**: Unified interface for multiple AI providers
**Connections**:
- Used by all AI modules (`ai_chart_planner`, `ai/query_agent`, `insight_analysis`)
- Supports multiple models (Gemini, GPT, etc.)
- Handles API authentication and rate limiting

### Data Processing Modules

#### `dataset_intelligence.py` - Advanced Profiling
**Purpose**: Deep dataset analysis beyond basic statistics
**Connections**:
- Called by `app.py` during analysis
- Enhances basic analysis with domain-specific insights
- Results used by AI modules for better recommendations

#### `feature_importance.py` - Feature Analysis
**Purpose**: Identifies most important features/columns
**Connections**:
- Uses dataset profile from `dataset_intelligence.py`
- Results used by `chart_recommender.py`
- Influences AI chart planning

#### `chart_recommender.py` - Chart Type Logic
**Purpose**: Rule-based chart type recommendations
**Connections**:
- Complements AI chart planning
- Uses feature importance and correlation data
- Provides fallback recommendations

#### `column_classifier.py` - Automatic Type Detection
**Purpose**: Intelligent column classification beyond basic pandas types
**Connections**:
- Enhances basic type detection from `main.py`
- Used by AI modules for better understanding
- Results stored in analysis cache

#### `target_detector.py` - Target Column Identification
**Purpose**: Automatically identifies potential target variables for ML
**Connections**:
- Uses column classifications
- Results used by feature importance analysis
- Helps guide chart recommendations

### Analysis Modules

#### `analysis/correlation_engine.py` - Correlation Analysis
**Purpose**: Computes relationships between variables
**Connections**:
- Called by `app.py` during analysis pipeline
- Results used by AI modules and visualization
- Supports both numerical and categorical correlations

#### `insight_engine.py` - Automated Insight Discovery
**Purpose**: Finds interesting patterns automatically
**Connections**:
- Uses correlation data and feature importance
- Generates insights without AI prompting
- Complements AI-generated insights

#### `insight_analysis.py` - Executive Summary Generation
**Purpose**: Creates high-level business summaries
**Connections**:
- Called by `app.py` for AI summary generation
- Uses `llm_client.py` for AI processing
- Results displayed prominently on dashboard

### Reporting System

#### `reporting/report_generator.py` - Business Report Creation
**Purpose**: Generates comprehensive business reports
**Connections**:
- Called via `/report` route in `app.py`
- Uses all analysis data and AI insights
- Supports both JSON and HTML output formats

### Frontend Architecture

#### `templates/dashboard.html` - Main Analytics Dashboard
**Purpose**: Primary user interface for data exploration
**Connections**:
- Receives data from Flask routes
- Uses Chart.js for visualizations
- Implements responsive design with Tailwind CSS
- Contains JavaScript for interactivity

**Key Sections**:
- Welcome/KPI overview
- AI summary cards
- Data profiling sections
- Interactive charts
- Natural language query interface
- Report generation controls

#### `templates/home.html` - Landing Page
**Purpose**: File upload and initial configuration
**Connections**:
- Simple form for file upload
- API key configuration
- Model selection
- Redirects to dashboard after analysis

#### `static/dashboard.css` & `dashboard.js` - Frontend Assets
**Purpose**: Styling and interactivity
**Connections**:
- CSS provides responsive design
- JavaScript handles user interactions
- Works with dashboard.html template

---

## Data Flow Pipeline

### Complete Analysis Flow

```
1. USER UPLOAD
   └── File uploaded via home.html
   └── API key and model selected
   └── POST /analyze triggered

2. FILE PROCESSING
   └── File validation (CSV/XLSX)
   └── Pandas DataFrame creation
   └── Large dataset sampling (50k rows max)

3. BASIC ANALYSIS (main.py)
   ├── basic_overview() - Dimensions
   ├── missing_overview() - Missing data
   ├── column_types() - Type classification
   ├── healthy() - Quality checks
   ├── simple_stats() - Statistics
   └── detect_outliers() - Outlier detection

4. ADVANCED ANALYSIS
   ├── overall_dataset_health() - Health scoring
   ├── column_risk_scores() - Risk assessment
   ├── primary_risk_column() - Risk ranking
   ├── dataset_intelligence.py - Profiling
   ├── column_classifier.py - Type enhancement
   ├── target_detector.py - Target identification
   └── analysis/correlation_engine.py - Correlations

5. AI PROCESSING
   ├── insight_analysis.py - Executive summary
   ├── ai_chart_planner.py - Chart recommendations
   ├── feature_importance.py - Feature ranking
   ├── chart_recommender.py - Chart logic
   └── insight_engine.py - Pattern discovery

6. SESSION MANAGEMENT
   ├── UUID generation for session
   ├── Cache data storage
   ├── Session ID in user cookie
   └── API keys stored server-side

7. DASHBOARD RENDERING
   ├── All data passed to template
   ├── JSON serialization for JavaScript
   ├── Chart.js initialization
   └── Interactive dashboard displayed

8. INTERACTIVE FEATURES
   ├── Natural language queries (/ask)
   ├── Report generation (/report)
   ├── Dynamic chart updates
   └── Real-time responses
```

### Data Structures

#### Analysis Cache Structure
```json
{
  "session_id": "uuid-string",
  "clean_insights": {
    "basic_overview": {...},
    "missing_overview": {...},
    "column_types": {...},
    "health_checks": {...},
    "simple_stats": {...},
    "outliers": {...},
    "overall_health_score": 85,
    "data_trust_level": "High",
    "primary_risk_column": "column_name",
    "primary_risk_score": 75,
    "correlations": {...},
    "summary": "AI-generated text"
  },
  "dataset_profile": {...},
  "top_features": {...},
  "column_classifications": {...},
  "api_key": "encrypted-key",
  "model_name": "gemini-2.5-flash",
  "total_rows": 10000
}
```

---

## Component Deep Dive

### Session Management System

**Purpose**: Maintain state across multiple requests without cookie size limits
**Implementation**:
- UUID-based session identification
- Server-side file caching (`cache/` directory)
- Session ID stored in browser cookie
- Automatic cleanup of old sessions

**Flow**:
1. User uploads file → UUID generated
2. All analysis data stored in `{session_id}.json`
3. Session ID sent to browser as cookie
4. Subsequent requests use session ID to retrieve data
5. API keys kept server-side for security

### AI Integration Architecture

**Multi-Provider Support**:
- Abstract `llm_client.py` interface
- Support for Gemini, GPT, Claude, etc.
- Consistent response format across providers
- Error handling and fallbacks

**AI Usage Patterns**:
1. **Executive Summary**: High-level business insights
2. **Chart Planning**: Domain-specific visualization recommendations
3. **Natural Language Q&A**: Interactive data exploration
4. **Report Generation**: Structured business documentation

### Chart Generation Pipeline

**Two-Tier Approach**:
1. **AI-Driven**: `ai_chart_planner.py` creates contextual charts
2. **Rule-Based**: `chart_recommender.py` provides logical fallbacks

**Chart Types Supported**:
- Bar charts (comparisons)
- Line charts (trends)
- Pie/Doughnut charts (proportions)
- Radar charts (multi-dimensional)
- Scatter plots (correlations)
- Histograms (distributions)

### Error Handling Strategy

**File Upload Errors**:
- File type validation
- Size limits
- Encoding detection
- Graceful fallbacks

**AI Service Errors**:
- Rate limiting handling
- API key validation
- Model fallbacks
- Offline mode support

**Data Processing Errors**:
- Type conversion safety
- Missing data handling
- Outlier detection robustness
- Memory management

---

## Frontend Architecture Details

### Dashboard Component Structure

```
dashboard.html
├── Header (Navigation + Context)
├── Sidebar (Section Navigation)
├── Main Content Area
│   ├── Welcome Section
│   ├── Hero KPI Row
│   ├── Insight Highlight Cards
│   ├── Data Profiling Group
│   │   ├── Basic Overview
│   │   ├── Missing Data
│   │   └── Outliers
│   ├── Executive Health Section
│   ├── AI Summary Section
│   ├── Statistics Section
│   ├── Column Types Section
│   ├── Correlation Section
│   └── Charts Section
└── Interactive Components
    ├── Natural Language Query
    ├── Report Generation
    └── Dynamic Filters
```

### JavaScript Architecture

**Core Functions**:
- `showSection()` - Navigation between dashboard sections
- `buildCharts()` - Chart.js initialization
- `buildAICharts()` - AI-recommended chart rendering
- `askQuestion()` - Natural language query handling
- `generateReport()` - Business report creation

**Data Flow**:
1. JSON data injected from Flask
2. JavaScript parses and processes
3. Chart.js renders visualizations
4. User interactions trigger API calls
5. Dynamic updates without page reload

### Responsive Design

**Breakpoints**:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

**Adaptations**:
- Sidebar collapses on mobile
- Grid layouts adjust columns
- Charts resize responsively
- Touch-friendly interactions

---

## Security Considerations

### API Key Management
- Keys stored server-side only
- Session-based isolation
- No client-side exposure
- Automatic cleanup on session end

### Data Privacy
- No data persistence beyond session
- File-based cache with automatic cleanup
- No external data sharing
- Local processing only

### Input Validation
- File type restrictions
- Size limitations
- Content sanitization
- SQL injection prevention

---

## Performance Optimizations

### Data Processing
- Large dataset sampling (50k row limit)
- Efficient NumPy/Pandas operations
- Memory-conscious processing
- Parallel computation where possible

### Caching Strategy
- Session-based result caching
- Chart data pre-computation
- Static asset optimization
- Minimal API calls

### Frontend Performance
- Lazy loading of sections
- Optimized Chart.js rendering
- Efficient DOM manipulation
- Minimal external dependencies

---

## Deployment Considerations

### Production Requirements
- Python 3.8+
- Sufficient RAM for large datasets
- SSL for API security
- Regular cache cleanup

### Scaling Considerations
- Horizontal scaling with shared cache
- Database-backed session storage
- Load balancing for AI requests
- CDN for static assets

### Monitoring Needs
- Error logging and alerting
- Performance metrics tracking
- AI service usage monitoring
- User analytics collection

---

## Future Enhancement Opportunities

### Technical Improvements
- Real-time data streaming
- Advanced ML models
- Database integration
- API rate limiting

### Feature Enhancements
- Collaborative analysis
- Custom chart builder
- Data export options
- Advanced filtering

### User Experience
- Onboarding tutorials
- Template gallery
- Keyboard shortcuts
- Dark/light themes

---

## Conclusion

Insight Forge represents a sophisticated integration of traditional data analysis with modern AI capabilities. The modular architecture ensures maintainability while the comprehensive feature set provides end-to-end analytics capabilities. The system successfully bridges the gap between raw data and actionable business intelligence through intelligent automation and intuitive interfaces.

The architecture supports both technical users who want detailed analysis and business users who need quick insights, making it a versatile solution for data-driven decision making.
