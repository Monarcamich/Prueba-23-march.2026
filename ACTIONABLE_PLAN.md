# F1 Project - 30 Acciones Concretas Para Mejorar Tu Carrera

## 🎯 Instrucciones
Elige tu rol (Data Engineer / Analytics / ML / Full-Stack) y sigue los pasos EN ORDEN.
Cada paso tiene duración estimada. Haz uno por día.

---

## 🔧 Path A: DATA ENGINEER (12 semanas → €85k promedio)

### Semana 1: Code Quality Fundamentals
**Objetivo:** Código listo para producción

#### Día 1: Add pytest Tests
**Tiempo:** 2-3 horas | **Dificultad:** ⭐⭐
```bash
# Crea archivo tests/test_analysis.py
# Escribe 5 tests mínimo:
def test_parse_lap_time(): ...
def test_degradation_calculation(): ...
def test_outlier_detection(): ...
def test_driver_consistency(): ...
def test_invalid_data_handling(): ...

# Ejecuta: pytest tests/
# Meta: 80%+ code coverage
```

**Skill ganada:** TestingPruebas, Code Quality
**Portfolio value:** ⭐⭐⭐⭐

---

#### Día 2: Add Type Hints & Docstrings
**Tiempo:** 1-2 horas | **Dificultad:** ⭐⭐
```python
# Mejora tus funciones así:
from typing import List, Dict, Optional

def identify_tyre_degradation(
    df: pd.DataFrame, 
    driver_id: Optional[str] = None
) -> Dict[str, Dict[str, float]]:
    """
    Estimate tire degradation based on lap times.
    
    Args:
        df: DataFrame with lap data
        driver_id: Filter by specific driver (optional)
        
    Returns:
        Dict mapping driver_id -> {rate, r_squared, total_loss}
        
    Example:
        >>> degradation = identify_tyre_degradation(df, 'max_verstappen')
        >>> print(degradation['max_verstappen']['degradation_rate'])
        0.1234
    """
```

**Skill ganada:** Documentation, Professional Code
**Portfolio value:** ⭐⭐⭐

---

#### Día 3: Add Logging
**Tiempo:** 1 hora | **Dificultad:** ⭐
```python
# Reemplaza todos los print() con logging:
import logging

logger = logging.getLogger(__name__)

# En lugar de: print("Processing race...")
logger.info("Starting race processing for race_id=%s", race_id)

# En lugar de: print("ERROR!")
logger.error("Failed to fetch data: %s", error_message)

# Reemplaza en: etl_pipeline.py, data_fetcher.py, analysis.py
```

**Skill ganada:** Production Debugging
**Portfolio value:** ⭐⭐⭐

---

#### Día 4: Setup GitHub Properly
**Tiempo:** 1 hora | **Dificultad:** ⭐
```bash
# En GitHub, crea estos archivos:
.github/
  └── workflows/
      └── tests.yml  # GitHub Actions to run tests automatically

# Contenido básico:
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -e .
      - run: pytest
```

**Skill ganada:** CI/CD, DevOps basics
**Portfolio value:** ⭐⭐⭐⭐

---

#### Día 5: Improve README
**Tiempo:** 1-2 horas | **Dificultad:** ⭐⭐
Add sections to README.md:
```markdown
## Architecture Overview
[ASCII diagram of Bronze→Silver→Gold]

## Data Quality Metrics
- Records processed: 1,160+
- Validation rate: 100%
- Error rate: 0%

## Performance Benchmarks
- Avg processing time: XXX ms
- Memory usage: XXX MB

## Testing
- Unit tests: 5+
- Code coverage: 80%+
- All tests: ✓ PASSING

## Deployment
- Container: Docker ✓
- CI/CD: GitHub Actions ✓
```

**Skill ganada:** Communication, Technical Writing
**Portfolio value:** ⭐⭐⭐⭐

---

### Semana 2: Data Persistence

#### Día 6: Add SQLite Database
**Tiempo:** 3-4 horas | **Dificultad:** ⭐⭐⭐
```python
# src/database.py - Nuevo módulo
import sqlite3
import pandas as pd

class RaceDatabase:
    def __init__(self, db_path: str = "f1_races.db"):
        self.conn = sqlite3.connect(db_path)
    
    def save_race(self, race_df: pd.DataFrame, season: int, round_num: int):
        """Save race data to SQLite"""
        table_name = f"race_{season}_r{round_num}"
        race_df.to_sql(table_name, self.conn, if_exists='replace')
        self.conn.commit()
    
    def load_race(self, season: int, round_num: int) -> pd.DataFrame:
        """Load race data from SQLite"""
        table_name = f"race_{season}_r{round_num}"
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

# Uso:
db = RaceDatabase()
db.save_race(analysis_df, 2024, 1)
```

**Skill ganada:** SQL, Data Modeling
**Portfolio value:** ⭐⭐⭐⭐⭐

---

#### Día 7: Add DDL (Data Definition)
**Tiempo:** 2 hours | **Dificultad:** ⭐⭐
```python
# sql_scripts/schema.sql - Nuevo archivo
CREATE TABLE races (
    race_id INTEGER PRIMARY KEY,
    season INTEGER,
    round INTEGER,
    race_name TEXT,
    date DATE,
    UNIQUE(season, round)
);

CREATE TABLE lap_data (
    lap_id INTEGER PRIMARY KEY,
    race_id INTEGER FOREIGN KEY,
    driver_id TEXT,
    lap_num INTEGER,
    lap_time_seconds FLOAT,
    pace_delta FLOAT,
    degradation_rate FLOAT,
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

CREATE INDEX idx_race_driver ON lap_data(race_id, driver_id);
CREATE INDEX idx_lap_num ON lap_data(lap_num);
```

**Skill ganada:** Database Design, Optimization
**Portfolio value:** ⭐⭐⭐⭐

---

#### Día 8: Query Optimization
**Tiempo:** 2 hours | **Dificultad:** ⭐⭐⭐
```python
# Escribe queries optimizadas:
def get_driver_stats(season: int, driver_id: str) -> Dict:
    query = """
    SELECT 
        AVG(lap_time_seconds) as avg_pace,
        MIN(lap_time_seconds) as best_lap,
        STDDEV(lap_time_seconds) as consistency,
        COUNT(*) as total_races
    FROM lap_data
    WHERE season = ? AND driver_id = ?
    GROUP BY driver_id
    """
    return pd.read_sql(query, self.conn, params=(season, driver_id))

# Analiza EXPLAIN PLAN:
# EXPLAIN QUERY PLAN SELECT...
```

**Skill ganada:** Query Optimization, Performance
**Portfolio value:** ⭐⭐⭐

---

### Semana 3: APIs & Integration

#### Día 9: Create FastAPI REST API
**Tiempo:** 3-4 horas | **Dificultad:** ⭐⭐⭐
```python
# src/api.py - Nuevo módulo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="F1 Analysis API", version="1.0")

@app.get("/api/races/{season}")
def get_races(season: int):
    """Get all races for a season"""
    races = db.query_races(season)
    return {"races": races, "count": len(races)}

@app.get("/api/driver/{driver_id}/stats")
def get_driver_stats(driver_id: str):
    """Get driver performance stats"""
    stats = calculate_consistency(df[df['driver_id'] == driver_id])
    return stats

@app.post("/api/process_race")
def process_race(season: int, round_num: int):
    """Trigger race processing"""
    result = pipeline.process_race(season, round_num)
    return {"status": "success", "records": len(result)}

# Ejecuta: uvicorn src.api:app --reload
# Test en http://localhost:8000/docs
```

**Skill ganada:** REST APIs, Backend Engineering
**Portfolio value:** ⭐⭐⭐⭐⭐

---

#### Día 10: Add API Tests
**Tiempo:** 2 hours | **Dificultad:** ⭐⭐
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_get_races():
    response = client.get("/api/races/2024")
    assert response.status_code == 200
    assert "races" in response.json()

def test_driver_stats():
    response = client.get("/api/driver/max_verstappen/stats")
    assert response.status_code == 200
    assert "consistency" in response.json()

def test_process_race():
    response = client.post("/api/process_race", 
                          params={"season": 2024, "round": 1})
    assert response.status_code == 200
```

**Skill ganada:** Integration Testing
**Portfolio value:** ⭐⭐⭐

---

### Semana 4: Containerization

#### Día 11: Create Dockerfile
**Tiempo:** 1-2 horas | **Dificultad:** ⭐⭐
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY src/ src/
COPY scripts/ scripts/
COPY data/ data/

EXPOSE 8000

# Para API:
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]

# O para CLI:
# CMD ["python", "scripts/fetch_f1_seasons.py"]
```

**Skill ganada:** Docker, Containerization
**Portfolio value:** ⭐⭐⭐⭐

---

#### Día 12: Create Docker Compose
**Tiempo:** 1-2 horas | **Dificultad:** ⭐⭐
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/f1_db
    depends_on:
      - db
      - postgres
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=f1_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

volumes:
  postgres_data:

# Ejecuta: docker-compose up
```

**Skill ganada:** DevOps, Infrastructure
**Portfolio value:** ⭐⭐⭐⭐⭐

---

### Semana 5-6: Data Warehouse

#### Día 13: Setup PostgreSQL
**Tiempo:** 2-3 horas | **Dificultad:** ⭐⭐⭐
```python
# src/database_pg.py
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/f1_db")
engine = create_engine(DATABASE_URL)

def save_race_data(df: pd.DataFrame, season: int, round_num: int):
    table_name = f"race_{season}_{round_num}"
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Saved to PostgreSQL: {table_name}")

def load_all_races(season: int) -> pd.DataFrame:
    query = f"SELECT * FROM races WHERE season = {season}"
    return pd.read_sql(query, engine)
```

**Skill ganada:** PostgreSQL, Production Databases
**Portfolio value:** ⭐⭐⭐⭐

---

#### Día 14: Create Data Warehouse Schema
**Tiempo:** 2-3 horas | **Dificultad:** ⭐⭐⭐
```sql
-- sql_scripts/warehouse_schema.sql

-- Dimension tables
CREATE TABLE dim_drivers (
    driver_id SERIAL PRIMARY KEY,
    driver_code VARCHAR(3) UNIQUE,
    driver_name VARCHAR(100),
    nationality VARCHAR(50)
);

CREATE TABLE dim_circuits (
    circuit_id SERIAL PRIMARY KEY,
    circuit_name VARCHAR(100),
    country VARCHAR(50)
);

CREATE TABLE dim_seasons (
    season_id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE
);

-- Fact table
CREATE TABLE fct_lap_times (
    lap_id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES dim_seasons,
    circuit_id INTEGER REFERENCES dim_circuits,
    driver_id INTEGER REFERENCES dim_drivers,
    lap_number INTEGER,
    lap_time_seconds FLOAT,
    pace_delta FLOAT,
    degradation_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fct_season_driver ON fct_lap_times(season_id, driver_id);
```

**Skill ganada:** Dimensional Modeling, Star Schema
**Portfolio value:** ⭐⭐⭐⭐⭐

---

### Semana 7: Automation & Orchestration

#### Día 15: Setup Apache Airflow
**Tiempo:** 3-4 horas | **Dificultad:** ⭐⭐⭐⭐
```bash
# Instala Airflow
pip install apache-airflow

# Crea DAG: airflow/dags/f1_pipeline.py
```

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'f1_analysis_pipeline',
    default_args=default_args,
    description='F1 Race Analysis ETL Pipeline',
    schedule_interval='0 0 * * *',  # Daily at midnight
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

def fetch_races_task():
    fetcher = get_fetcher()
    season_data = fetcher.fetch_season(2024)
    return season_data

def process_races_task(**context):
    season_data = context['task_instance'].xcom_pull(task_ids='fetch_races')
    pipeline = Pipeline()
    for race in season_data['races']:
        pipeline.process_race(2024, int(race['round']), race)

def generate_reports_task():
    # Generate reports and send alerts
    pass

fetch_task = PythonOperator(task_id='fetch_races', python_callable=fetch_races_task, dag=dag)
process_task = PythonOperator(task_id='process_races', python_callable=process_races_task, dag=dag)
report_task = PythonOperator(task_id='generate_reports', python_callable=generate_reports_task, dag=dag)

fetch_task >> process_task >> report_task
```

**Skill ganada:** Workflow Orchestration, Automation
**Portfolio value:** ⭐⭐⭐⭐⭐

---

### Semana 8: Cloud Deployment

#### Día 16: Deploy to AWS (ECR + ECS)
**Tiempo:** 4-5 horas | **Dificultad:** ⭐⭐⭐⭐
```bash
# Push Docker image to AWS ECR
# (Requiere AWS CLI configurado)

aws ecr create-repository --repository-name f1-analysis
aws ecr get-login-password | docker login --username AWS --password-stdin YOUR_REGISTRY_URI
docker tag f1-analysis:latest YOUR_REGISTRY_URI/f1-analysis:latest
docker push YOUR_REGISTRY_URI/f1-analysis:latest

# Deploy a ECS
# Use AWS Console o Terraform
```

**Skill ganada:** Cloud DevOps, AWS
**Portfolio value:** ⭐⭐⭐⭐⭐

---

#### Día 17: Add Monitoring & Logging
**Tiempo:** 2-3 horas | **Dificultad:** ⭐⭐⭐
```python
# src/monitoring.py
import logging
from pythonjsonlogger import jsonlogger

# JSON logging para CloudWatch
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Metrics
from prometheus_client import Counter, Histogram, start_http_server

race_processed = Counter('races_processed_total', 'Total races processed')
processing_time = Histogram('race_processing_seconds', 'Processing time')

@processing_time.time()
def process_race_with_metrics(season, round_num):
    result = pipeline.process_race(season, round_num)
    race_processed.inc()
    return result
```

**Skill ganada:** Monitoring, Logging, Observability
**Portfolio value:** ⭐⭐⭐⭐

---

### Semana 9-12: Advanced Topics

#### Día 18: Data Quality Framework (Great Expectations)
**Tiempo:** 3-4 horas | **Dificultad:** ⭐⭐⭐⭐
```python
# src/data_quality.py
from great_expectations.dataset.pandas_dataset import PandasDataset

def validate_race_data(df: pd.DataFrame) -> bool:
    """Validate race data with Great Expectations"""
    dataset = PandasDataset(df)
    
    # Define expectations
    dataset.expect_column_values_to_be_of_type("lap_time_seconds", "float")
    dataset.expect_column_values_to_be_between("lap_time_seconds", 60, 300)
    dataset.expect_column_values_to_not_be_null("driver_id")
    dataset.expect_column_values_to_not_be_null("lap_num")
    
    results = dataset.validate(result_format="SUMMARY")
    return results['success']
```

**Skill ganada:** Data Quality Engineering
**Portfolio value:** ⭐⭐⭐⭐

---

#### Día 19: Performance Testing & Profiling
**Tiempo:** 2-3 horas | **Dificultad:** ⭐⭐⭐
```python
# tests/test_performance.py
import time
import pytest

@pytest.mark.performance
def test_pipeline_performance():
    """Ensure pipeline processes 1M rows in < 30 seconds"""
    start = time.time()
    result = pipeline.process_race(2024, 1, large_dataset)
    elapsed = time.time() - start
    
    assert elapsed < 30, f"Pipeline too slow: {elapsed}s"
    assert len(result) > 0

def profile_analysis():
    """Profile memory usage"""
    import cProfile
    import pstats
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    identify_tyre_degradation(df)
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

**Skill ganada:** Performance Optimization
**Portfolio value:** ⭐⭐⭐

---

#### Día 20: Documentation & Blog
**Tiempo:** 4-5 horas | **Dificultad:** ⭐⭐
Write a blog post (Medium/Dev.to/LinkedIn):

```markdown
# How I Built an F1 Data Pipeline from Scratch

## Problem
[Describe what you wanted to learn]

## Solution
1. Architecture: 3-layer ETL
2. Technologies: Python, PostgreSQL, Docker, Airflow
3. Results: 1M+ records processed with 100% accuracy

## Key Learnings
- [Learning 1]
- [Learning 2]
- [Learning 3]

## Code Example
[Show interesting code snippet]

## Lessons for Future Projects
```

**Skill ganada:** Technical Communication
**Portfolio value:** ⭐⭐⭐⭐⭐ (HUGE for marketing yourself)

---

#### Día 21: Interview Preparation
**Tiempo:** 3-4 horas | **Dificultad:** ⭐⭐
Prep for common questions:

```
1. "Walk us through your architecture"
   → 5 minute explanation ready
   
2. "How would you handle 10x data?"
   → Scaling strategy ready
   
3. "What's your biggest learning?"
   → Story + technical insight
   
4. "How do you ensure data quality?"
   → Talk about validation layer
   
5. "Describe a difficult problem"
   → Use real example from project
```

**Skill ganada:** Interview Communication
**Portfolio value:** ⭐⭐⭐⭐⭐

---

## 📊 Path B: ANALYTICS ENGINEER (10 semanas → €80k promedio)

### Similar structure, focus on:
- W1-2: Tests + SQL optimization
- W3-4: dbt setup + metrics definition
- W5-6: BI tool (Looker/Tableau) integration
- W7-8: Advanced SQL patterns + window functions
- W9-10: Data quality + testing framework

---

## 🤖 Path C: ML ENGINEER (14 semanas → €95k promedio)

### Similar structure, focus on:
- W1-2: Tests + Feature engineering
- W3-4: Baseline models (Linear, Tree models)
- W5-6: Advanced models (XGBoost, CatBoost)
- W7-8: Hyperparameter tuning + Cross-validation
- W9-10: Model deployment (Flask/FastAPI)
- W11-12: MLflow + Experiment tracking
- W13-14: Advanced (Ensemble, Deep Learning)

---

## 🎯 Path D: FULL-STACK (16 semanas → €110k promedio)

### All of the above combined, plus:
- Full API development
- Database design
- UI/Dashboard (Streamlit)
- Cloud deployment
- CI/CD automation

---

## ✅ Progress Tracker

Mark off as you complete:

```
Week 1:
□ Día 1: pytest
□ Día 2: Type hints
□ Día 3: Logging
□ Día 4: GitHub Actions
□ Día 5: README

Week 2:
□ Día 6: SQLite
□ Día 7: Schema
□ Día 8: Optimization

Week 3:
□ Día 9: FastAPI
□ Día 10: API Tests

Week 4:
□ Día 11: Docker
□ Día 12: Docker Compose

...continue through Day 21
```

---

## 🏁 Final Checklist Before Applying

- [ ] 80%+ test coverage
- [ ] All tests passing
- [ ] CI/CD working
- [ ] README excellent
- [ ] Code properly logged
- [ ] Type hints throughout
- [ ] API working + documented
- [ ] Database schema defined
- [ ] Containerized with Docker
- [ ] Deployed to cloud
- [ ] Blog post written
- [ ] 5-minute pitch ready
- [ ] Portfolio on GitHub
- [ ] LinkedIn updated

**When ALL are done:** You're job-ready 🚀

---

**Start today. Pick Day 1. Spend 2-3 hours. Push to GitHub.**

**Momentum builds. In 21 days you'll be unrecognizable.** 💪
