# 🎓 SPPU Credit Analysis & Prediction System

A data-driven web application built with **Python & Streamlit** designed specifically for the Savitribai Phule Pune University (SPPU) grading system. 

This tool analyzes historical student performance to uncover subject difficulty trends, and uses a hybrid Machine Learning approach to predict a student's future EndSem performance based on their past academic capability and current semester momentum.

---

## ✨ Dashboard Features

The application is split into two primary modules:

### 1. 📊 Dashboard Analysis
A comprehensive analytics suite to understand global dataset trends and individual student performance.
* **Global Metrics:** Real-time calculation of average scores, overall pass rates, and dataset size.
* **Interactive Data Visualizations:** Utilizes Plotly for interactive, hoverable charts showing Grade Distribution and Subject-wise EndSem averages.
* **Correlation Heatmaps:** Seaborn-powered heatmaps analyzing the relationship between Attendance, InSem (Internal) marks, and EndSem (External) marks.
* **🔥 Relative Subject Toughness:** A custom 0-10 scaling system. It identifies the hardest subject in the dataset (locked to 10) and ranks all other subjects relative to it, preventing high overall pass rates from masking subject difficulty.
* **🧑‍🎓 Individual Student Profiler:** Select any student to view their specific stats. Includes grouped bar charts comparing their individual Theory (TH) and Practical (PR) marks against the global dataset average.

### 2. 🤖 Performance Predictor
A personalized prediction engine for generating a future SPPU Grade Card.
* **Collapsible Subject UI:** Clean accordion-style interface to input current InSem marks and Attendance per subject.
* **Live SPPU SGPA Calculation:** Outputs predicted External marks, Total marks, official SPPU Grades, and predicted SGPA.
* **Backlog Detection:** Automatically flags predicted 'F' grades and adjusts earned credits accordingly.

---

## ⚙️ How It Works (Under the Hood)

Traditional prediction systems often fail because they treat all credits equally, leading to **"Lab Inflation"** (where easy 1-credit practicals artificially boost a student's perceived capability in tough 3-credit theory exams). This system solves that using a decoupled mathematical approach.

### 1. Calculating True Theory Strength
When a student uploads their past semester result, the system strictly separates Theory (TH) from Practical/Term Work (PR/TW). 
1. It calculates an SGPA using **only Theory subjects**.
2. It converts this SGPA into the official SPPU percentage: `Percentage = (Theory_SGPA - 0.75) * 10`.
3. This generates a True Capability Multiplier (e.g., 74.5% = `0.745`), representing their actual historical capability in written exams without lab inflation.

### 2. The Hybrid Prediction Engine
To predict the EndSem score (out of 70), the system uses a **Linear Regression ML Model** combined with a weighted momentum algorithm:
1. **The ML Baseline:** The Scikit-Learn model analyzes the historical dataset to find what a statistically "average" student scores in a specific subject based on their InSem marks and Attendance.
2. **Historical Component (70% Weight):** The ML baseline is multiplied by the student's True Capability Multiplier, anchoring the prediction to their established track record.
3. **Current Momentum Component (30% Weight):** The current InSem marks (out of 30) are scaled to an out-of-70 equivalent. This acts as a real-time pulse check, pulling the prediction up if the student is currently outperforming their usual baseline.

---

## 📁 File Formats & Data Structures

The system relies on two specific CSV inputs. Sample files (`dashboard_data.csv` and `student_past_result.csv`) are included in this repository for testing.

### Input 1: Global Historical Dataset (`dashboard_data.csv`)
Uploaded in the sidebar, this file trains the Machine Learning model and populates the dashboard.
* **Required Columns:**
  | Student_id | Name | Subject | Type | Internal | External | Attendance |
  | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
  | 101 | Amit | Computer Networks | TH | 22 | 56 | 85 |
  | 101 | Amit | CN Lab | PR | 18 | 42 | 90 |

*(Note: The `Type` column **must** contain `TH` for Theory subjects and `PR`/`TW` for Practicals).*

### Input 2: Student Past Result (`student_past_result.csv`)
Uploaded in the Predictor tab, this calculates the individual student's historical capability.
* **Required Columns:**
  | Subject | Type | Credits | Total |
  | :--- | :--- | :--- | :--- |
  | Operating Systems | TH | 3 | 72 |
  | OS Lab | PR | 1 | 45 |

*(Note: The system will automatically ignore the `PR` rows when calculating True Theory Strength).*

---

## 🚀 Installation & Setup

To run this project locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/sppu-credit-analysis.git](https://github.com/your-username/sppu-credit-analysis.git)
   cd sppu-credit-analysis
